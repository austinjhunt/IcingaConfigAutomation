## This is a repo of code for automating the creation of new Icinga configurations based on an input CSV containing: IP addresses, Host names, FQDNs, OSs, Notes, and really any other custom attributes you may want to add to your Host objects
### Repo does not contain IP addresses/FQDNS used originally, just the code for creating the configurations and instructions on how to use it

## Usage:
### Create a virtual environment (I used Python 3.6), activate, then install requirements before using
##### name=Column containing Host object's name
##### os=Column containing Host object's operating System
##### fname=path/to/csv
##### includesvmhostcol=<whether or not your file is structured such that 'name' is the name of a GUEST VM on a HOST machine; if 1, pass hostcol ; this boolean flag is REQUIRED; if not structured this way, pass 0, otherwise 1
#### hostcol=Column containing the FQDN of the HOST on which the Guest VM is running>
#### ipcol=Column containing IP address of the host object ; really, it's better to use FQDNs for your host address attribute; the script is written in such a way that it tries to avoid using IP addresses as "address" values; first uses dns.resolver to find FQDN, then checks to see whether `name` is a valid FQDN; if neither, use IP 
#### notes=Column containing host object notes; be sure that you have the , delimeter between " " if you use it.

```
#### Structured with 'name' column (column 1) as name/FQDN of Guest VM, <host> column as name/FQDN of Host machine
(icingavenv) IT-C07L20D3DY3H:automate_icinga austinhunt$ python host_object_creator.py name=1 ip=4 includesvmhostcol=1 host=5 os=6 fname=~/Downloads/inventory1.csv

#### Structured as 'name' column (column 1) as FQDN of host object, notes in column 5
(icingavenv) IT-C07L20D3DY3H:automate_icinga austinhunt$ python host_object_creator.py name=1 includesvmhostcol=0 notes=5 fname=~/Downloads/inventory2.csv

#### Structured as 'name' column (column 1) as FQDN of host object, ip address in column 4 for hosts where name doesn't work as FQDN
(icingavenv) IT-C07L20D3DY3H:automate_icinga austinhunt$  python host_object_creator.py name=1 ip=4 includesvmhostcol=0 fname=~/Downloads/inventory3.csv

# Structured as 'name' column (column 4) as FQDN of host (in some cases; some are blank, some have spaces; script includes validation)
(icingavenv) IT-C07L20D3DY3H:automate_icinga austinhunt$ python host_object_creator.py name=4 includesvmhostcol=0 fname=~/Downloads/inventory4.csv
```
