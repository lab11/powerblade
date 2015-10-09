#!/usr/bin/python

import sys
import statistics

calibrate = 1

infile = sys.argv[1]
outfile = sys.argv[2]

fin = open(infile,'r')
fout = open(outfile,'w')

timestamps = []
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

		if line[0] == 'Data':
			timestamps.append(float(line[1].split(' ')[0]))
		elif line[0] == 'Sequence Number':
			seqs.append(float(line[1].split(' ')[0]))
		elif line[0] == 'Time':
			#print line
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

powers = powers[1:]
pfs = pfs[1:]
# if calibrate == 1:
# 	print 'Time: ' + str(sum(times)/len(times))
# 	print('Variance: ' + str(statistics.variance(times)))
	
# 	for idx, val in enumerate(times):
# 		fout.write(str(timestamps[idx]) + '\t' + str(times[idx]) + '\t0.0\n')
if calibrate == 1:
	print('Ave: ' + str(sum(wattHours)/len(wattHours)))
	print('Variance: ' + str(statistics.variance(wattHours)))
else:
	print 'True Power: ' + str(sum(powers)/len(powers))
	print 'Power Factor: ' + str(sum(pfs)/len(pfs))
	print('Variance in TP: ' + str(statistics.variance(powers)))

	for idx, val in enumerate(powers):
		fout.write(str(timestamps[idx]) + '\t' + str(powers[idx]) + '\t' + str(pfs[idx]) + '\n')

