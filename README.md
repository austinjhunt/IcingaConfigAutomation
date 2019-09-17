## This is a repo of code for automating the creation of new Icinga configurations based on an input CSV containing: IP addresses, Host names, FQDNs, OSs, Notes, and really any other custom attributes you may want to add to your Host objects
### Repo does not contain IP addresses/FQDNS used originally, just the code for creating the configurations and instructions on how to use it
#### Ideal way to use bulk fqdn finder:
`./bulk_fdqn_finder.sh <hosts.csv> <os column number> | sort | uniq -u > <fqdns_file>`
where the output file may optionally store either: 
i) FQDN, or ii) FQDN, OS
