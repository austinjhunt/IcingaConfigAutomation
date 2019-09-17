"""
Austin Hunt
Sept 16-17, 2019
Script for parsing a CSV file of hosts and building out Icinga2 configuration objects (Host objects, specifically) based on
flags passed to determine what Icinga attributes to map the columns to
Built for an Enterprise Application Management project for the College of Charleston IT department
"""
import sys,csv,re
from dns import resolver,reversename
from string import Template as tmp



# Define a resolver for DNS resolution
res = resolver.Resolver()
res.nameservers = ['153.9.116.5', '10.9.64.10', '153.9.116.1']
res.timeout = 1
res.lifetime = 1

# Define a regex pattern for matching IP addresses, and one for FQDNs
ippattern = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
fqdn_pattern = re.compile("(([a-z0-9\-\_]+\.)+[a-z]{2,})")

# Counter used to skip header line in CSV
COUNT=1

# Maintain global dictionary to avoid creation of multiple Host objects with same name.
HOSTS_CREATED = {}

# Class for dynamically building/filling out an Icinga Host object configuration that adapts to different
# arguments passed to it. If argument is not passed (e.g. OS or notes), then it doesn't add the variable to the config.
class HostObject:
	# constructor automatically detects if these columns were provided as arguments and determines the associated values
	def __init__(self, address=None,hostname=None,notes=None,os=None,display_name=None):
		# Let the template be an instance variable with an internally substitutable "body" which will be built using the other
		# instance variables.
		self.template = tmp("object Host \"$hostname\" { $body}")

		# The host name doesn't need to be defined as a 'definition' string, it'll just be substituted into $hostname directly.
		self.hostname = hostname

		# For these variables, give them either their passed value or empty string if that value is none
		self.address_def = "address = \"" + address + "\"" if address is not None else ""
		self.notes_def = "vars.notes = \"" + notes.replace('\n',' ').replace('\r','') + "\"" if notes is not None else ""
		self.os_def = "vars.os = \"" + os + "\"" if os is not None else ""
		self.check_command_def = "check_command = \"hostalive\""
		self.display_name_def = "display_name = \"" + display_name + "\"" if display_name is not None else "display_name = \"" + self.hostname + "\""
	def create_object(self):
		config_body = ""
		# Add every instance variable that is neither the 1) template nor 2) the host name to the body of the configuration.
		# Include new lines and tabs.
		for key, value in self.__dict__.items():
			if not isinstance(value,tmp) and key != "hostname" :
				config_body += "\n\t" + value
		config_body += "\n"

		# Fill in the template
		obj = self.template.substitute(hostname=self.hostname, body=config_body)
		# Clean the blank lines from the template.
		clean = "\n".join([ll.rstrip() for ll in obj.splitlines() if ll.strip()]) # remove empty lines
		return clean
# Helper methods
# Remove the trailing . from the fqdn found in many of my input CSVs
def clean_fqdn(fqdn):
	return fqdn[:-1] if fqdn.endswith(".") else fqdn

# If a column argument is passed, return the indexed value, otherwise return none
def index_if_not_none(line,var):
	if var is not None:
		return line[var]
	else:
		return None
# Create an object for the IP addresses matched
def createObjectPerIP(ip_addresses,line):
	for ip in ip_addresses:
		# Get FQDN of ip
		try:
			addr = reversename.from_address(ip)
			fqdn = str(res.query(addr, "PTR")[0])
		# Otherwise, let FQDN be the IP
		except:
			fqdn = ip
			# If exception is thrown, it's possible that the host just isn't pingable. (very common for untrusted network)


		# In the case that each CSV record is a VM hosted on the Host in the "host" column,
		# create a Host object for each VM, then create a Host object for the Host machine. (as long as conditions are satisfied)
		# VM host object using template

		# Don't create an object for the secondary 192.168 addresses
		# CSVs given to me include multiple IP addresses for some records, don't need local 192.168 one
		if "192.168" in ip:
			continue


		# Also don't create an object if an object has already been created for this hostname (count maintained by global dictionary)
		host_name = index_if_not_none(line,namecol)
		if host_name not in HOSTS_CREATED:
			# Let the FQDN be the host name if it works as an FQDN, otherwise, just keep its value (without a trailing . )
			# This should result in either a non-192.168 IP or a valid FQDN from either A) nslookup or B) host name column
			fqdn = host_name if is_valid_fqdn(host_name) else clean_fqdn(fqdn)
			try:
				# Create the host object using the custom class
				ho = HostObject(address=fqdn, hostname=host_name, display_name=host_name,
								os=index_if_not_none(line, oscol), notes=index_if_not_none(line, notescol)).create_object()
				# add to created objects
				HOSTS_CREATED[host_name] = ho
				# Print it, so that output can be redirected to file
				print(ho)
			except Exception as e:
				# Likely you'll want to remove this since the output conf file will result in errors if this line is included.
				print("templating failed", e)

# Did a really basic check here; do not want to allow spaces in FQDNs
def is_valid_fqdn(string):
	return " " not in string
# Check if a line provides adequate info in order to create Host object; if not, skip line
def line_is_valid(line):
	valid = False
	global COUNT # use global count variable to determine if header
	# Skip header -> "not valid"
	if COUNT == 1:
		COUNT += 1
		return False
	# If system has name
	name = index_if_not_none(line,namecol).strip()
	if name != "":
		# If system has spaces in its name, and does not have an IP address column or an FQDN column, can't create a host object
		# Only return true if either 1) the name has no spaces (Likely an FQDN), OR there exists an IP address column
		# In other words, is this a reachable Host based on the info in this line?
		if " " not in name or ipcol is not None:
			valid = True
	return valid

def parse():
	# Open and use csv reader to parse the passed file
	with open(fname,newline='') as f:
		r = csv.reader(f, delimiter=',', quotechar='"')
		for line in r:
			# Make sure line can be used to generate a Host object; skip header
			if not line_is_valid(line):
				# if not, skip line.
				continue

			# Process data
			else:
				# Regex match all of the IP addresses in the IP address column (if column argument passed)
				ip_addresses = re.findall(ippattern, line[ipcol]) if ipcol is not None else None
				# If a match exists
				if ip_addresses != None and len(ip_addresses) >0:

					# Create objects using the IP(s)
					createObjectPerIP(ip_addresses,line)

					# For files that contain a Host and Guest VM column, create object for Host machine as well as the Guests,
					# which were handled above.
					if includesvmhostcol: # This is why this arg is required.
						try:
							# Only create an object if the address (to be used for Host's name) has not already been used
							address = clean_fqdn(index_if_not_none(line,hostcol)) #if ends with .
							if address not in HOSTS_CREATED:
								ho = HostObject(hostname=address, display_name=index_if_not_none(line,hostcol), address=address).create_object()
								HOSTS_CREATED[address] = ho
								print(ho)
						except Exception as e:
							# May not want to include this; output Icinga conf will throw errors if this statement is included in fil
							print("Templating failed.", e)

				else:
					# No ip addresses in file, which means there NEEDS TO BE a column containing the FQDN of each host.
					# Use the name= argument for this value; this will serve as the Host's 1) name, 2) display name
					# and 3) address/FQDN
					name = index_if_not_none(line,namecol)
					fqdn = name
					# Seeing one file with name column values that look like <Description> (FQDN), so parse out the FQDN if true

					if re.search(fqdn_pattern,fqdn):
						fqdn = clean_fqdn(re.search(fqdn_pattern, fqdn)[0])
					ho = HostObject(hostname=name,display_name=name, address=fqdn, notes=index_if_not_none(line,notescol)).create_object()
					# If you need IP: res.query(fqdn, "A")[0]

					# If just a name, assume that domain is internal; should not need to append domain
					print(ho)



if __name__ == "__main__":

	# initialize column values to none.
	notescol = None
	oscol = None
	hostcol = None
	ipcol  = None
	fname = None

	# Add your own column names here, make sure you include the parsing in the for loop as well.


	# include a help option for usage info
	if "help" in sys.argv:
		print("Usage: python host_object_creator.py name=1 host=2 os=3 ip=4 fname=/Users/test/something.csv")
		sys.exit()
	def parsearg(a):
		return int(a.split("=")[-1]) - 1
	for a in sys.argv[1:]:
		if "includesvmhost" in a:
			includesvmhostcol = True if parsearg(a)+1 == 1 else False
		elif "fname" in a:
			fname = a.split("=")[-1]
		elif "name" in a:
			namecol = parsearg(a)
		elif "host" in a:
			hostcol = parsearg(a)
		elif "os" in a:
			oscol = parsearg(a)
		elif "ip" in a:
			ipcol = parsearg(a)
		elif "notes" in a:
			notescol = parsearg(a)

	# Call the parse function
	parse()
