"""
Austin Hunt, Sept 16-17, 2019
Constants used by host_object_creator.py
"""
import re
from dns import resolver
# Define a resolver for DNS resolution
RES = resolver.Resolver()
RES.nameservers = ['153.9.116.5', '10.9.64.10', '153.9.116.1']
RES.timeout = 1
RES.lifetime = 1

# Define a regex pattern for matching IP addresses, and one for FQDNs
IPPATTERN = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
FQDN_PATTERN = re.compile("(([a-z0-9\-\_]+\.)+[a-z]{2,})")

# Counter used to skip header line in CSV
COUNT = 1

# Maintain global dictionary to avoid creation of multiple Host objects with same name.
HOSTS_CREATED = {}


# Argument-defined constants
# initialize column values to none.

NOTESCOL = None
NAMECOL = None
OSCOL = None
HOSTCOL = None
IPCOL = None
FNAME = None
INCLUDESVMHOSTCOL = None

# Add your own constants here, be sure to include the argument parsing in the for a in sys.argv[:-1] loop