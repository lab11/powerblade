#!/usr/bin/python

import sys
import os

#infile = sys.argv[1]
#outfile = sys.argv[1]

#fin = open(infile,'r')
#fout = open(outfile,'w')

csvCount = 0

for filename in os.listdir('.'):
	csvCount = csvCount + 1
	if filename.endswith(".CSV") | filename.endswith(".csv"):
		fin = open(filename, 'r')
		filename = filename.split('.')[0]
		fout = open(filename + '.dat', 'w')
		current = []
		voltage = []

	for line in fin:
		line = line.split(',')
		if line[0].split('.')[0].isdigit():
			#print line
			current.append((csvCount*2)+float(line[1]))
			voltage.append(float(line[3]))
			
	# Get vmin and max to find zero crossings
	vmin = min(voltage)
	vmax = max(voltage)
	vmid = (vmin + vmax) / 2

	print vmin
	print vmax
	print vmid

	if voltage[0] > vmid:
		above = 1
	else:
		above = 0

	index = 0
	# Find first zero crossing, and print one full cycles
	for idv, vval in enumerate(voltage):
		index = idv
		if above == 1:
			if vval > vmid:
				continue
			break
		if above == 0:
			if vval < vmid:
				continue
			break

	time = 0
	finalVal = index + 1740
	while index < finalVal:
		time = time + 1
		print(str(time) + '\t' + str(voltage[index]) + '\t' + str(current[index]) + '\n'),
		fout.write(str(time) + '\t' + str(voltage[index]) + '\t' + str(current[index]) + '\n')
		index = index + 1




