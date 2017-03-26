#!/usr/bin/env python

import sys
from printEnergy import printEnergy

total_measured = 0
gndTruth = 0
pwrData = []

for inData in sys.argv[1:]:
	infile = open(inData, 'r')

	for line in infile:
		if(line[0] == '#'):
			lineList = line[2:-1].split(': ')
			if lineList[0] == 'total measured energy':
				total_measured += float(lineList[1])
			else:
				gndTruth += float(lineList[1])
		else:
			lineList = line[0:-1].split('\t')[1:]
			lineList[-1] = float(lineList[-1])
			pwrData.append(lineList)



printEnergy(pwrData, total_measured, gndTruth, 'combine')

#print(total_measured)
#print(gndTruth)
#print(pwrData)







