"""
Austin Hunt
Sept 16-17, 2019
Script for parsing a CSV file of hosts and building out Icinga2 configuration objects (Host objects, specifically) based on
flags passed to determine what Icinga attributes to map the columns to
Built for an Enterprise Application Management project for the College of Charleston IT department
"""
import csv, re, constants
from util import *
from CofCHostObject import CofCHostObject



def parse():
    # Open and use csv reader to parse the passed file
    with open(constants.FNAME, newline='') as f:
        r = csv.reader(f, delimiter=',', quotechar='"')
        for line in r:
            # Make sure line can be used to generate a Host object; skip header
            if not line_is_valid(line):
                # if not, skip line.
                continue

            # Process data
            else:
                # Regex match all of the IP addresses in the IP address column (if column argument passed)
                ip_addresses = re.findall(constants.IPPATTERN, line[constants.IPCOL]) if constants.IPCOL is not None else None
                # If a match exists
                if ip_addresses != None and len(ip_addresses) > 0:

                    # Create objects using the IP(s)
                    createObjectPerIP(ip_addresses, line)

                    # For files that contain a Host and Guest VM column, create object for Host machine as well as the Guests,
                    # which were handled above.
                    if constants.INCLUDESVMHOSTCOL:  # This is why this arg is required.
                        try:
                            # Only create an object if the address (to be used for Host's name) has not already been used
                            address = clean_fqdn(index_if_not_none(line, constants.HOSTCOL))  # if ends with .
                            if address not in constants.HOSTS_CREATED:
                                ho = CofCHostObject(hostname=address, display_name=index_if_not_none(line, constants.HOSTCOL),
                                                address=address).create_object()
                                constants.HOSTS_CREATED[address] = ho
                                print(ho)
                        except Exception as e:
                            # May not want to include this; output Icinga conf will throw errors if this statement is included in fil
                            print("Templating failed.", e)

                else:
                    # No ip addresses in file, which means there NEEDS TO BE a column containing the FQDN of each host.
                    # Use the name= argument for this value; this will serve as the Host's 1) name, 2) display name
                    # and 3) address/FQDN
                    name = index_if_not_none(line, constants.NAMECOL)
                    fqdn = name
                    # Seeing one file with name column values that look like <Description> (FQDN), so parse out the FQDN if true

                    if re.search(constants.FQDN_PATTERN, fqdn):
                        fqdn = clean_fqdn(re.search(constants.FQDN_PATTERN, fqdn)[0])

                    ho = CofCHostObject(hostname=name, display_name=name, address=fqdn,
                                    notes=index_if_not_none(line, constants.NOTESCOL)).create_object()
                    # If you need IP: res.query(fqdn, "A")[0]

                    # If just a name, assume that domain is internal; should not need to append domain
                    print(ho)


if __name__ == "__main__":
    args = sys.argv

    setconstants(args) # use args to either set constants or print help statement

    # Call the parse function
    parse()
