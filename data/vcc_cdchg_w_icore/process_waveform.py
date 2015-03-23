#!/usr/bin/python

import sys
import os

#infile = sys.argv[1]
#outfile = sys.argv[1]

mid = 0

numaverage = 10
icore_averages = [0] * numaverage
v_averages = [0] * numaverage

def averageIcore(newVal):

	for ida, avVal in enumerate(icore_averages[:-1]):
		icore_averages[ida] = icore_averages[ida+1]

	icore_averages[-1] = newVal

	return 10*sum(icore_averages)/len(icore_averages)

def averageVoltage(newVal):

	for ida, avVal in enumerate(v_averages[:-1]):
		v_averages[ida] = v_averages[ida+1]

	v_averages[-1] = newVal

	return sum(v_averages)/len(v_averages)

if mid == 1:
	fin = open('vcc_cdchg_mid.CSV','r')
	fout = open('mid.dat','w')
else:
	fin = open('vcc_cdchg_veryFar.CSV','r')
	fout = open('far.dat','w')

vcap = []
icore = []

for line in fin:
	line = line.split(',')
	if line[0].strip('-').split('.')[0].isdigit():
		#print line
		icore.append(averageIcore(float(line[1])))
		vcap.append(averageVoltage(float(line[3])))
		
time = 0
for idv, vval in enumerate(vcap):
	if mid == 1:
		time = time + .192 	# Mid
	else:
		time = time + .768
		icore[idv] = icore[idv] * 1.42
	print(str(time) + '\t' + str(vcap[idv]) + '\t' + str(icore[idv]) + '\n'),
	fout.write(str(time) + '\t' + str(vcap[idv]) + '\t' + str(icore[idv]) + '\n')






