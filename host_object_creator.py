# Assume you have a CSV file with at least one column containing IP addresses, preferably other columns
# Script will run nslookup command on each IP address and will write to a new file named 
# <originalCSVFilename>_nslookup.txt
# Usage: ./bulk_hostobject_creator.sh -n <display name column> -h <VM Host FQDN column> -o <VM os column> <fqdnCSV file>
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
# Use a count to skip the header.
count = 1
HOSTS_CREATED = {}

class HostObject:
	# constructor automatically detects if these columns were provided as arguments and determines the associated values
	def __init__(self, address=None,hostname=None,notes=None,os=None,display_name=None):
		# let the template be an instance variable
		self.template = tmp("object Host \"$hostname\" { $body}")
		self.address_def = "address = \"" + address + "\"" if address is not None else ""
		self.hostname = hostname
		self.notes_def = "vars.notes = \"" + notes.replace('\n',' ').replace('\r','') + "\"" if notes is not None else ""
		self.os_def = "vars.os = \"" + os + "\"" if os is not None else ""
		self.check_command_def = "check_command = \"hostalive\""
		self.display_name_def = "display_name = \"" + display_name + "\"" if display_name is not None else "display_name = \"" + self.hostname + "\""
	def create_object(self):
		config_body = ""
		for key, value in self.__dict__.items():
			if not isinstance(value,tmp) and key != "hostname" :
				config_body += "\n\t" + value
		config_body += "\n"
		obj = self.template.substitute(hostname=self.hostname, body=config_body)
		clean = "\n".join([ll.rstrip() for ll in obj.splitlines() if ll.strip()]) # remove empty lines
		return clean

def clean_fqdn(fqdn):
	return fqdn[:-1] if fqdn.endswith(".") else fqdn
def index_if_not_none(line,var):
	if var is not None:
		return line[var]
	else:
		return None
def createObjectPerIP(ip_addresses,line):
	for ip in ip_addresses:
		# Get fqdn
		try:
			addr = reversename.from_address(ip)
			fqdn = str(res.query(addr, "PTR")[0])
		except:
			fqdn = ip
			# If exception is thrown, it's possible that the host just isn't pingable.
		# Each record is a VM hosted on the Host in the "host" column. Create a Host object for each VM, then create a Host object for the Host machine.
		# VM host object using template

		# Don't create an object for the secondary 192.168 addresses
		if "192.168" in ip:
			continue

		# Also don't create an object if an object has already been created for this hostname (count maintained by global dictionary)
		host_name = index_if_not_none(line,namecol)
		if host_name not in HOSTS_CREATED:
			fqdn = host_name if is_valid_fqdn(host_name) else clean_fqdn(fqdn) # should result in either a non-192.168 IP or a valid FQDN from A) nslookup or B) host name column
			try:
				ho = HostObject(address=fqdn, hostname=host_name, display_name=host_name,
								os=index_if_not_none(line, oscol), notes=index_if_not_none(line, notescol)).create_object()
				# add to created objects
				HOSTS_CREATED[host_name] = ho
				print(ho)
			except Exception as e:
				print("templating failed", e)

def is_valid_fqdn(string):
	return " " not in string
def line_is_valid(line):
	valid = False
	global COUNT
	if COUNT == 1:
		COUNT += 1
		return False
	# If system has name
	name = index_if_not_none(line,namecol).strip()
	if name != "":
		# If system has spaces in its name, and does not have an IP address column or an FQDN column, can't create a host object
		# only return true if either 1) the name has no spaces (Likely an FQDN), OR there exists an IP address column
		if " " not in name or ipcol is not None:
			valid = True
	return valid
COUNT=1
def parse():
	with open(fname,newline='') as f:
		r = csv.reader(f, delimiter=',', quotechar='"')
		for line in r:
			# Make sure line can be used to generate a Host object; skip header
			if not line_is_valid(line):
				# if not, skip line.
				continue

			# process data
			else:
				ip_addresses = re.findall(ippattern, line[ipcol]) if ipcol is not None else None
				# if match exists
				if ip_addresses != None and len(ip_addresses) >0:
					# If file contains IP addresses, create corresponding objects
					createObjectPerIP(ip_addresses,line)

					# For files that contain a Host and Guest VM column, create object for Host machine as well as the Guests,
					# which were handled above.
					if includesvmhostcol:
						try:
							# Only create an object if the address (to be used for Host's name) has not already been used
							address = clean_fqdn(index_if_not_none(line,hostcol)) #if ends with .
							if address not in HOSTS_CREATED:
								ho = HostObject(hostname=address, display_name=index_if_not_none(line,hostcol), address=address).create_object()
								HOSTS_CREATED[address] = ho
								print(ho)
						except Exception as e:
							print("Templating failed.", e)

				else:
					# No ip addresses in file, which means there is a column containing the FQDN of each host.
					# Use the name= argument for this value
					name = index_if_not_none(line,namecol)
					fqdn = name
					# Seeing one file with name column values that look like <Description> (FQDN), so parse out the FQDN if true

					if re.search(fqdn_pattern,fqdn):
						fqdn = clean_fqdn(re.search(fqdn_pattern, fqdn)[0])
					ho = HostObject(hostname=name,display_name=name, address=fqdn, notes=index_if_not_none(line,notescol)).create_object()
					# If you need IP: res.query(fqdn, "A")[0]

					# If just a name, assume that domain is interanal; should not need to append domain
					print(ho)



if __name__ == "__main__":

	notescol = None
	oscol = None
	hostcol = None
	ipcol  = None
	fname = None
	if "help" in sys.argv:
		print("Usage: python host_object_creator.py <displaynamecolumn> <hostmachinecolumn> <oscolumn> <ipcolumn> <csvfilepath>")
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

	parse()
