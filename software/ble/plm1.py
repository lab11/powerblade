#!/usr/bin/python

import sys
import os
import serial
import statistics
import time

def process_message(message):

	message = message.split(',')
	for item in message:
		item = item.strip()

	timeRead = time.time()

	#print(list(message[2]))

	#volt = float(message[0])
	#amp = float(message[1])
	va = float(message[6])
	watt = float(message[4]) - 0.6
	#vPeak = float(message[4])
	#cPeak = float(message[5])
	#wPeak = float(message[6])
	pf = float(message[7])
	#wattHour = float(message[8])
	hours = float(message[9])
	
	# Write data out
	print("Data Received: " + str(watt) + '\t' + str(va) + '\t' + str(pf))
	fout.write(str(timeRead) + '\t' + str(watt) + '\t' + str(va) + '\t' + str(pf) + '\n')

if len(sys.argv) > 1:
	ser = serial.Serial(
		port=sys.argv[1],
		baudrate=9600
	)
else:
	for root, dirs, filenames in os.walk('/dev'):
	    for f in filenames:
	    	#print(f)
	    	if('ttyUSB' in f or 'tty.usbserial' in f or 'tty.usbmodem' in f):
	    		ser = serial.Serial('/dev/' + f)
	    		ser = serial.Serial(
	    			port='/dev/' + f,
	    			baudrate=9600
				)

print(time.time())
fout = open('plm1.dat', 'w')

message = ''
start = 0
ser.flush()

while(1):
	byte = ser.read().decode()

	if byte == '\n':
		if start == 1:
			process_message(message)
		start = 1
		message = ''
	else:
		message += byte




