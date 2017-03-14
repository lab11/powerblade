#!/usr/bin/env python

import mylogin
import MySQLdb
import json

import datetime
import pytch

import os
import subprocess
from sh import epstopdf, gnuplot

# Read config file for start time, end time, and devices
config = {}
try:
	config_file = open('.plotconfig', 'r')
	json_txt = ""
	for line in config_file:
		json_txt += line
	config = json.loads(json_txt)
except:
	config['type'] = 'plot'
	config['start'] = '2017-01-01 00:00:00'
	config['end'] = '2017-01-01 23:59:59'
	config['devices'] = ['c098e5700000']
	config['sum'] = False

# Check device list

query_powerblade = False
query_blees = False
query_ligeiro = False
query_blink = False


# Set up connection
aws_login = mylogin.get_login_info('aws')
aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
aws_c = aws_db.cursor()
connected = True

def dev_print():
	global dev_powerblade
	global dev_blees
	global dev_ligeiro
	global dev_blink

	global query_powerblade
	global query_blees
	global query_ligeiro
	global query_blink

	dev_powerblade = ["("]
	dev_blees = ["("]
	dev_ligeiro = ["("]
	dev_blink = ["("]

	for dev in config['devices']:

		devType = dev[6:8]

		if(devType == "70"):	# PowerBlade
			query_powerblade = True
			dev_powerblade.append("\"")
			dev_powerblade.append(dev)
			dev_powerblade.append("\"")
			dev_powerblade.append(",")

		elif(devType == "30"):	# BLEES
			query_blees = True
			dev_powerblade.append("\"")
			dev_blees.append(dev)
			dev_powerblade.append("\"")
			dev_blees.append(",")

		elif(devType == "d0"):	# Ligeiro
			query_ligeiro = True
			dev_powerblade.append("\"")
			dev_ligeiro.append(dev)
			dev_powerblade.append("\"")
			dev_ligeiro.append(",")

		elif(devType == "90"):	# Blink	
			query_blink = True
			dev_powerblade.append("\"")
			dev_blink.append(dev)
			dev_powerblade.append("\"")
			dev_blink.append(",")

		else:
			print("Unknown device: " + dev)

	dev_powerblade[-1] = ")"
	dev_blees[-1] = ")"
	dev_ligeiro[-1] = ")"
	dev_blink[-1] = ")"

	# Repurpose these variables to be strings rather than lists
	dev_powerblade = "".join(dev_powerblade)
	dev_blees = "".join(dev_blees)
	dev_ligeiro = "".join(dev_ligeiro)
	dev_blink = "".join(dev_blink)

	aws_c.execute('select deviceMAC, deviceName from most_recent_powerblades where deviceMAC in ' + dev_powerblade + ";")
	devNames = aws_c.fetchall();

	for line in devNames:
		print("\t" + line[0] + "\t" + line[1])

	# for dev in config['devices']:
	# 	print("\t" + str(dev))

# Confirm parameters

print("\nPowerBlade Deployment Plotting Program")

def print_parameters():

	if(config['type'] == 'plot'):
		print("\nPlotting data from the following devices:")
	else:
		print("\nQuerying energy from the following devices")
	dev_print()

	print("\nOver the following time period:")
	config['startDay'] = config['start'][0:10]
	config['endDay'] = config['end'][0:10]
	if(config['type'] == 'plot'):
		print("From\t" + config['start'])
		print("To\t" + config['end'])
	else:
		print("From\t" + config['startDay'])
		print("To\t" + config['endDay'])

	if(config['sum']):
		print("\nWith sum of power also plotted")
	else:
		print("\nWithout sum of power plotted")

print_parameters()

print("\nTo confirm, push enter. To modify:")
print("\t'type [plot, energy]'")
print("\t'devices [comma separated 12 or 6 digit macs]' or")
print("\t'location #'")
print("\t'start yyyy-mm-dd HH:mm:ss' or")
print("\t'end yyyy-mm-dd HH:mm:ss' or")
print("\t'sum [true:false]'")

confirm = pytch.input_loop("\nPress enter, or next change: ")

changes = False

while(confirm != ""):

	confirm_list = confirm.split(" ")

	error = False

	if(confirm_list[0] == 'type'):
		if(confirm_list[1] == 'plot' or confirm_list[1] == 'energy'):
			config['type'] = confirm_list[1]
			changes = True
		else:
			print("Usage is type [plot:energy]")
			error = True
	elif(confirm_list[0] == 'dev' or confirm_list[0] == 'devices'):
		devType = 'replace'
		devOffset = 1
		if(confirm_list[1] == 'add' or confirm_list[1] == 'drop'):
			devType = confirm_list[1]
			devOffset = 2
		devList = "".join(confirm_list[devOffset:]).replace('[',' ').replace(']',' ').replace(',',' ').split()

		# Deal with shortened mac addresses
		for idx, dev in enumerate(devList):
			if(len(dev) == 3):
				devList[idx] = 'c098e5700' + dev
			elif(len(dev) == 6):
				devList[idx] = 'c098e5' + dev
			elif((len(dev) != 12) or (dev[0:5] != 'c098e5')):
				print("Unknown device: " + dev)

		if(devType == 'replace'):
			config['devices'] = devList
		elif(devType == 'add'):
			config['devices'] = config['devices'] + devList
		else:
			config['devices'] = [x for x in config['devices'] if x not in devList]
		changes = True
	elif(confirm_list[0] == 'location'):
		devType = 'replace'
		devOffset = 1
		if(confirm_list[1] == 'add' or confirm_list[1] == 'drop'):
			devType = confirm_list[1]
			devOffset = 2

		aws_c.execute('select lower(deviceMAC) from active_powerblades where location=' + confirm_list[devOffset] + ';')
		device_list = aws_c.fetchall()
		devList = [i[0] for i in device_list]

		if(devType == 'replace'):
			config['devices'] = devList
		elif(devType == 'add'):
			config['devices'] = config['devices'] + devList
		else:
			config['devices'] = [x for x in config['devices'] if x not in devList]
		changes = True
	elif(confirm_list[0] == 'start' or confirm_list[0] == 'end'):
		try:
			if(len(confirm_list[1].split('-')) == 2):
				confirm_list[1] = '2017-' + confirm_list[1]
			if(len(confirm_list) == 2):
				try:
					datetime.datetime.strptime(confirm_list[1], '%Y-%m-%d')
					config[confirm_list[0]] = confirm_list[1] + " " + config[confirm_list[0]].split(" ")[1]
					changes = True
				except:
					datetime.datetime.strptime(confirm_list[1], '%H:%M:%S')
					config[confirm_list[0]] = config[confirm_list[0]].split(" ")[0] + " " + confirm_list[1]
					changes = True
			else:
				date_text = confirm_list[1] + " " + confirm_list[2]
				datetime.datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
				config[confirm_list[0]] = date_text
				changes = True
		except:
			error = True
			print("Usage is 'start yyyy-mm-dd HH:mm:ss'")
	elif(confirm_list[0] == 'sum'):
		if(len(confirm_list) != 2 or (confirm_list[1] != 'true' and confirm_list[1] != 'false')):
			error = True
			print("Usage is 'sum [true:false]'")
		elif(confirm_list[1] == 'true'):
			config['sum'] = True
			changes = True
		else:
			config['sum'] = False
			changes = True
	else:
		error = True
		print("Unknown command")

	if(error == False):
		print(chr(27) + "[2J")
		print_parameters()

	confirm = pytch.input_loop("\nPress enter, or next change: ")

if(changes):
	if(raw_input("\nSave changes to config file? [y/n]: ") == "y"):
		with open('.plotconfig', 'w') as outfile:
		    json.dump(config, outfile)





####################################################################
#
# This section is for the plot option
#
####################################################################

if(config['type'] == 'plot'):

	if(query_powerblade):
		aws_c.execute("select deviceMAC, timestamp, power from dat_powerblade where deviceMAC in " + \
			dev_powerblade + " and timestamp between \"" + config['start'] + "\" and \"" + config['end'] + "\"" + \
			"order by deviceMAC, timestamp;")
		data_pb = aws_c.fetchall()
		
		if(config['sum']):
			aws_c.execute("select timestamp, sum(power) from dat_powerblade where deviceMAC in " + \
				dev_powerblade + " and timestamp between \"" + config['start'] + "\" and \"" + config['end'] + "\"" + \
				"group by timestamp order by timestamp;")
			sum_pb = aws_c.fetchall();



	# Create datfile and fill
	dat = open('datfile.dat', 'w')

	plot_count = 0

	if(config['sum']):
		plot_count = plot_count + 1
		dat.write("\"p = sum\"")
		for time, power in sum_pb:
			dat.write("\"" + str(time) + "\"\t" + str(power) + "\n")

	current_dev = 0
	for dev, time, power in data_pb:
		if dev != current_dev:
			plot_count = plot_count + 1
			current_dev = dev
			dat.write("\n\n\"p = " + current_dev + "\"\n")
		dat.write("\"" + str(time) + "\"\t" + str(power) + "\n")

	dat.close()

	# Create .plt file and fill
	plt = open('datfile.plt', 'w')
	plt.write('set terminal postscript enhanced eps solid color font "Helvetica,14" size 3in,2in\n')
	plt.write('set output "datfile.eps"\n')

	plt.write('set xdata time\n')
	plt.write('set timefmt \"\\\"%Y-%m-%d %H:%M:%S\\\"\"\n')
	plt.write('set format x \"%m-%d\\n%H:%M\"\n')

	plt.write('plot for [IDX=0:' + str(plot_count) + '] \'datfile.dat\' i IDX u 1:2 w lines title columnheader(1)\n')
	plt.close()


	# Clean up anything left from last time (in the case of errors)
	if(os.path.exists('datfile.eps')):
		os.remove('datfile.eps')
	if(os.path.exists('datfile.pdf')):
		os.remove('datfile.pdf')

	# Generate plot and convert to PDF
	gnuplot('datfile.plt')
	epstopdf('datfile.eps')

	# Show plot file
	img = subprocess.Popen(['open', 'datfile.pdf'])
	img.wait()

	# Remove temporary files
	os.remove('datfile.eps')
	os.remove('datfile.plt')






####################################################################
#
# This section is for the energy option
#
####################################################################

elif(config['type'] == 'energy'):

	# Step 1: starting energy for each device (min energy)
	aws_c.execute('select date(timestamp) as dayst, deviceMAc, min(energy) as energy from dat_powerblade force index(devEnergy) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['startDay'] + ' 12:00:00\' ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC, dayst order by deviceMAC, dayst')
	startEnergy = aws_c.fetchall()


	# Step 2: end energy per device per day in the time period (max energy)
	aws_c.execute('select date(timestamp) as dayst, deviceMAc, max(energy) as energy from dat_powerblade force index(devEnergy) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC, dayst order by deviceMAC, dayst')
	dayEnergy = aws_c.fetchall()

	
	# Step 3: end energy per device overall (used to ensure the data exists in the second half of the day)
	aws_c.execute('select date(timestamp) as dayst, deviceMAc, max(energy) as energy from dat_powerblade force index(devEnergy) ' \
		'where timestamp>=\'' + config['endDay'] + ' 12:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC, dayst order by deviceMAC, dayst')
	endEnergy = aws_c.fetchall()

	total_energy = 0
	energy_array = []
	errors = 0

	for dev in config['devices']:
		dev_startEnergy = -1
		for day, mac, energy in startEnergy:
			if(dev == mac):
				dev_startEnergy = energy
				break
		if(dev_startEnergy == -1):
			print("Error: No start energy value for " + dev)
			errors = errors + 1

		dev_endEnergy = -1
		for day, mac, energy in endEnergy:
			if(dev == mac):
				dev_endEnergy = energy
				break
		if(dev_endEnergy == -1):
			print("Error: No end energy value for " + dev)
			errors = errors + 1

		dev_energy = dev_endEnergy - dev_startEnergy
		total_energy = total_energy + dev_energy
		energy_array.append([dev, dev_energy])

	print(total_energy)
	print(energy_array)

	exit()

	# for day, mac, energy in dayEnergy:
	# 	for 



	# 	print(str(day) + " " + str(mac) + " " + str(energy))

	# exit()

	aws_c.execute('select t2.deviceMAC, t2.deviceName, t2.location from ' \
		'(select deviceMAC, max(id) as id ' \
		'from dat_powerblade where timestamp>date_sub(\'' + config['end'] + '\', interval 1 hour) AND timestamp<\'' + config['end'] + '\' ' \
		' group by deviceMAC) t1 ' \
		'join most_recent_powerblades t2 on t1.deviceMAC=t2.deviceMAC;')
	devNames = aws_c.fetchall();

	for idx, val in enumerate(startEnergy):
		print(str(idx) + " " + str(val[0]) + " " + str(endEnergy[idx][0]) + " " + str(devNames[idx][1]) + " " + str(devNames[idx][2]) + "\t" + str(val[1]) + " " + str(endEnergy[idx][1]) + " " + str(endEnergy[idx][1] - val[1]))


	# Print error message if missing the first part of the first day or last part of last day





