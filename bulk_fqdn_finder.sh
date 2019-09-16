#!/bin/bash
# Assume you have a CSV file with the Nth column (with header) containing IP addresses
# Script will run nslookup command on each IP address in that column and will write to a new file named 
# <originalCSVFilename>_nslookup.txt
# Usage: ./bulk_nslookup <csv_file> <N> (starting from 1 as leftmost)
csv=$1
n=$2
count=0
ippattern="(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"
echo "Reading from $csv"
filename=$(echo "$csv" | rev | cut -d/ -f1 | rev)
filename="$(echo $filename | cut -d. -f1)"
echo "Writing to file... $filename"
count=1
while read -r line
do	
	if [[ $count == 1 ]]; then
		echo "Skipping header" 
		let count=$count+1
	else 
		ipaddr="$(echo $line | grep -Eo $ippattern)"
		# if not empty/whitespace
		if [[ -z "${ipaddr// }" ]]; then # empty, do nothing
			continue # skip iteration
		else
			# Handle the case in which there are multiple matches. Specific to my case in which a file given to me has 
			# multiple IP addresses in a single IP address column. grep separates multiple matches using a \n character. 
			for ip in $ipaddr; do
				#echo "IP Address: $ip"
				#echo "nslookup $ip..."
				fqdn="$(nslookup $ip)"
				# Some will return a FQDN, some will return NXDOMAIN. 
				if [[ $fqdn =~ "NXDOMAIN" ]]; then
					fqdn=$ip
				else
					fqdn="$(echo $fqdn | rev | cut -d' ' -f 1 | rev)"
				fi
				echo $fqdn
			done
		fi
	fi
done < "$csv"
