import serial
import os
import time
import signal
import struct
import sys

def signal_handler(signal, frame):
	print("Exiting")
	# Stop reading data
	ser.write(b'\x18')

def process_message(message):
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
		fout.write(str(timeRead) + '\t' + str(watt) + '\t' + str(va) + '\t' + str(pf) + '\n')

	elif messageType == 'l':
		ser.write(bytes(b'#D,R,0;'))
if len(sys.argv) > 1:
	ser = serial.Serial(
		port=sys.argv[1],
		baudrate=115200
	)
	print("Connected to: " + ser.name)
else:
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

# Prepare to write data
#outfile = sys.argv[1]
fout = open('wattsup.dat','w')

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



