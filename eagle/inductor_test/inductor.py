#!/usr/bin/python

import sys
import os
import serial
import statistics
import time

numReadings = 100
currentIndex = 0
currentReadings = [0] * numReadings

for root, dirs, filenames in os.walk('/dev'):
    for f in filenames:
    	#print(f)
    	if('ttyUSB' in f or 'tty.usbserial' in f or 'tty.usbmodem' in f):
    		ser = serial.Serial('/dev/' + f)
    		ser = serial.Serial(
    			port='/dev/' + f,
    			baudrate=38400
			)

test = str(sys.argv[1])
setting = int(sys.argv[2])

outfileName = 'test' + test + '_' + str(setting) + '.txt'
if os.path.isfile(outfileName):
	print('ERROR: File exists')
	exit()
else:
	print('Test board #' + test)
	print('Wattage set at ' + str(setting) + ' W')

f = open(outfileName, 'w')

while(1):
	while ser.inWaiting() < 3:
		pass
	readData = ser.read(3)
	time.sleep(0.5)
	ser.flushInput()
	currentVal = int(readData[1] + (readData[2] << 8))
	if(currentVal < 2000):
		currentReadings[currentIndex] = currentVal
		currentIndex += 1
		print('Reading ' + str(currentIndex) + ': ' + str(currentVal))
		f.write(str(currentVal) + '\n')
		if(currentIndex == numReadings):
			break

print('Mean: ' + str(statistics.mean(currentReadings)))
print('Var: ' + str(statistics.variance(currentReadings)))
print('Stddev: ' + str(statistics.stdev(currentReadings)))



