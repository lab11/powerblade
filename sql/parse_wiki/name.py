#!/usr/bin/env python3

datfile = open('name.dat', 'r')
outfile = open('temp.temp', 'w')

for line in datfile:
	items = line.split('|')
	if len(items) > 1:
		#print(items[6].strip())
		if items[6].strip() == "SkySpecs":
			print(items[5].strip() + ', ' + items[7].strip() + ' ' + items[8].strip())
			outfile.write(items[5].strip().replace(':', '') + ', ' + items[7].strip() + ' ' + items[8].strip() + '\n')
