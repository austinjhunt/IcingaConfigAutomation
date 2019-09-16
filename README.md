## This is a repo of code for automating the creation of new Icinga configurations based on an input list of either FQDNs or IP addresses. 
### Repo does not contain IP addresses/FQDNS used originally, just the code for creating the configurations and instructions on how to use it
#### Ideal way to use bulk fqdn finder:
`./bulk_fdqn_finder.sh <hosts.csv> <IP Column number> | sort | uniq -u > <fqdns_file>`
