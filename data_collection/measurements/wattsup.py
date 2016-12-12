#! /usr/bin/env python

import serial
import os
import time
import signal
import struct
import sys
import json

count = 10
rx_count = 0

total_power = 0
total_voltage = 0

def signal_handler(signal, frame):
	print("Exiting")
	# Stop reading data
	ser.write(b'\x18')
	exit()

def process_message(message):
	global rx_count
	global total_power
	global total_voltage

	message = message.split(',')

	timeRead = time.time()

	messageType = message[0]

	if messageType == 'd':
		ser.write(bytes(b'#R,W,0;'))
		watt = (float(message[3]) / 10) - 0.2 	# Account for PowerBlade
		volt = float(message[4]) / 10
		amp = float(message[5]) / 1000
		wattHour = float(message[6]) / 10
		cost = float(message[7]) / 1000
		wh_mo = float(message[8])
		co_mo = float(message[9]) / 1000
		wMax = float(message[10]) / 10
		vMax = float(message[11]) / 10
		aMax = float(message[12]) / 10
		wMin = float(message[13]) / 10
		vMin = float(message[14]) / 10
		aMin = float(message[15]) / 10
		pf = float(message[16]) / 100
		dc = float(message[17])
		pc = float(message[18])
		freq = float(message[19]) / 10
		va = float(message[20]) / 10

		# Write data out
		print("Data Received: " + str(watt) + '\t' + str(pf))
		outobj = json.dumps({
			'time': timeRead,
			'power': watt,
			'vrms': volt,
			'va': va,
			'pf': pf
			})
		#fout.write(str(timeRead) + ',' + str(watt) + ',' + str(volt) + ',' + str(va) + ',' + str(pf) + '\n')
		fout.write(outobj + "\n")

		rx_count = rx_count + 1

		total_power = total_power + watt
		total_voltage = total_voltage + volt

		if(rx_count == count):
			print("Power: " + str(total_power / count))
			print("Voltage: " + str(total_voltage / count))
			exit()

	elif messageType == 'l':
		ser.write(bytes(b'#D,R,0;'))

directory = os.environ['PB_DATA']

# Prepare to write data
if(len(sys.argv) > 1):
	outfile = directory + '/' + sys.argv[1]
	if(len(sys.argv) > 2):
		outfile += "_" + sys.argv[2]
	outfile += ".dat"	
else:
	outfile = directory + '/wattsup.dat'

if os.path.isfile(outfile):
	replace = raw_input("Warning: file exists. Replace? (y/n): ")
	if replace == 'y':
		newfileNum = 0
		newfile = outfile.split('.')[0] + '.bak'
		while(os.path.isfile(newfile)):
			newfileNum += 1
			newfile = outfile.split('.')[0] + '_' + str(newfileNum) + '.bak'
		os.rename(outfile, newfile)
	else:
		exit()

# if len(sys.argv) > 1:
# 	ser = serial.Serial(
# 		port=sys.argv[1],
# 		baudrate=115200
# 	)
# 	print("Connected to: " + ser.name)
# else:
for root, dirs, filenames in os.walk('/dev'):
	for f in filenames:
		#print(f)
		if('ttyUSB' in f or 'tty.usbserial' in f or 'tty.usbmodem' in f):
			ser = serial.Serial('/dev/' + f)
			ser.baudrate = 115200
			print("Connected to: " + ser.name)

signal.signal(signal.SIGINT, signal_handler)

# Start reading data
print(time.time())

fout = open(outfile, 'w')
#fout.write("#Time,watt,volt,va,pf\n")

message = ''

#ser.flush()
start = 0
ser.write(bytes(b'#R,W,0;'))
ser.write(bytes(b'#D,R,0;'))

while(1):
	byte = ser.read().decode("utf-8")

	if byte == '#':
		message = ''
		start = 1
	elif byte == ';':
		if start == 1:
			process_message(message)
	else:
		message += byte



