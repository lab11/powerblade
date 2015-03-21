#!/usr/bin/python

import sys

infile = sys.argv[1]
outfile = sys.argv[2]

fin = open(infile,'r')
fout = open(outfile,'w')

seqs = []
times = []
rms = []
powers = []
appPowers = []
wattHours = []
pfs = []
readingNum = 0

for line in fin:
	if len(line) > 1:
		line = line[:-1]
		line = line.split(':')
		for idx, item in enumerate(line):
			line[idx] = item.strip()
		
		if line[0] == 'Sequence Number':
			seqs.append(float(line[1].split(' ')[0]))
		elif line[0] == 'Time':
			times.append(float(line[1].split(' ')[0]))
		elif line[0] == 'RMS Voltage':
			rms.append(float(line[1].split(' ')[0]))
		elif line[0] == 'Current True Power':
			powers.append(float(line[1].split(' ')[0]))
		elif line[0] == 'Current Apparent Power':
			appPowers.append(float(line[1].split(' ')[0]))
		elif line[0] == 'Cumulative Watt Hours':
			wattHours.append(float(line[1].split(' ')[0]))
		elif line[0] == 'Power Factor':
			pfs.append(float(line[1].split(' ')[0]))

print 'True Power: ' + str(sum(powers)/len(powers))
print 'Power Factor: ' + str(sum(pfs)/len(pfs))

