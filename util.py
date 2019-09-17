"""
Austin Hunt, Sept 16-17, 2019
helper methods used by host_object_creator.py
"""
import constants
import sys
from HostObject import HostObject
from dns import reversename


# Helper methods
# Remove the trailing . from the fqdn found in many of my input CSVs
def clean_fqdn(fqdn):
    return fqdn[:-1] if fqdn.endswith(".") else fqdn


# If a column argument is passed, return the indexed value, otherwise return none
def index_if_not_none(line, var):
    if var is not None:
        return line[var]
    else:
        return None


# Did a really basic check here; do not want to allow spaces in FQDNs
def is_valid_fqdn(string):
    return " " not in string


# Check if a line provides adequate info in order to create Host object; if not, skip line
def line_is_valid(line):
    valid = False
     # use global count variable to determine if header
    # Skip header -> "not valid"
    if constants.COUNT == 1:
        constants.COUNT += 1
        return False
    # If system has name
    name = index_if_not_none(line, constants.NAMECOL).strip()
    if name != "":
        # If system has spaces in its name, and does not have an IP address column or an FQDN column, can't create a host object
        # Only return true if either 1) the name has no spaces (Likely an FQDN), OR there exists an IP address column
        # In other words, is this a reachable Host based on the info in this line?
        if " " not in name or constants.IPCOL is not None:
            valid = True
    return valid


# Create an object for the IP addresses matched
def createObjectPerIP(ip_addresses, line):
    for ip in ip_addresses:
        # Get FQDN of ip
        try:
            addr = reversename.from_address(ip)
            fqdn = str(constants.RES.query(addr, "PTR")[0])
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
        host_name = index_if_not_none(line, constants.NAMECOL)
        if host_name not in constants.HOSTS_CREATED:
            # Let the FQDN be the host name if it works as an FQDN, otherwise, just keep its value (without a trailing . )
            # This should result in either a non-192.168 IP or a valid FQDN from either A) nslookup or B) host name column
            fqdn = host_name if is_valid_fqdn(host_name) else clean_fqdn(fqdn)
            try:
                # Create the host object using the custom class
                ho = HostObject(address=fqdn, hostname=host_name, display_name=host_name,
                                os=index_if_not_none(line, constants.OSCOL),
                                notes=index_if_not_none(line, constants.NOTESCOL)).create_object()
                # add to created objects
                constants.HOSTS_CREATED[host_name] = ho
                # Print it, so that output can be redirected to file
                print(ho)
            except Exception as e:
                # Likely you'll want to remove this since the output conf file will result in errors if this line is included.
                print("templating failed", e)


def parsearg(a):
    return int(a.split("=")[-1]) - 1


def setconstants(args):
    # include a help option for usage info
    if "help" in args:
        print("Usage: python host_object_creator.py name=1 host=2 os=3 ip=4 fname=/Users/test/something.csv")
        sys.exit()

    for a in args[1:]:
        if "includesvmhost" in a:
            constants.INCLUDESVMHOSTCOL = True if parsearg(a) + 1 == 1 else False
        elif "fname" in a:
            constants.FNAME = a.split("=")[-1]
        elif "name" in a:
            constants.NAMECOL = parsearg(a)
        elif "host" in a:
            constants.HOSTCOL = parsearg(a)
        elif "os" in a:
            constants.OSCOL = parsearg(a)
        elif "ip" in a:
            constants.IPCOL = parsearg(a)
        elif "notes" in a:
            constants.NOTESCOL = parsearg(a)
