#!/usr/bin/env python

import mylogin
import MySQLdb
import json

from datetime import datetime
import pytch

import os
import sys
import subprocess
from sh import epstopdf, gnuplot, mkdir, cp, mv

from printEnergy import printEnergy
from breakdown import breakdown
from boxplot import boxplot

import math

query_startDay = datetime.utcnow().strftime('%Y_%m_%d_')

master_saveDir = os.environ['PB_DATA'] + "/savetest/" + str(query_startDay)

if not os.path.isdir(os.environ['PB_DATA'] + "/savetest/"):
	mkdir(os.environ['PB_DATA'] + "/savetest/")


# Read config file for start time, end time, and devices
config = {}
try:
	config_file = open('.plotconfig', 'r')
	json_txt = ""
	for line in config_file:
		json_txt += line
	config = json.loads(json_txt)
	if(config['tag'] != '' and config['tag'] != 'info'):
		config['tag'] = ''
except:
	config['type'] = 'plot'
	config['start'] = '2017-01-01 00:00:00'
	config['end'] = '2017-01-01 23:59:59'
	config['devices'] = ['c098e5700000']
	config['locations'] = ['0']
	config['sum'] = False
	config['tag'] = ''

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

qu_saveDir = ''
def check_tag():
	global qu_saveDir
	global config

	query_startTime = datetime.utcnow().strftime('%H_%M_%S')
	qu_saveDir = master_saveDir + str(query_startTime)
	qu_saveDir += '_l'
	for loc in config['locations']:
		qu_saveDir += loc
	qu_saveDir += '_' + config['type']
	if(config['type'] != 'results'):
		qu_saveDir += '_s' + datetime.strptime(config['start'], "%Y-%m-%d %H:%M:%S").strftime('%m%d')
		qu_saveDir += '_e' + datetime.strptime(config['end'], "%Y-%m-%d %H:%M:%S").strftime('%m%d')
	qu_saveDir += '/'

	# if(config['tag'] == ''):
	# 	query_startTime = datetime.utcnow().strftime('%H_%M_%S')
	# 	qu_saveDir = master_saveDir + str(query_startTime) + '/'
	# elif(config['tag'] == 'info'):
	# 	qu_saveDir = master_saveDir + 'l'
	# 	for loc in config['locations']:
	# 		qu_saveDir += loc
	# 	qu_saveDir += '_' + config['type']
	# 	if(config['type'] != 'power'):
	# 		qu_saveDir += '_s' + datetime.strptime(config['start'], "%Y-%m-%d %H:%M:%S").strftime('%m%d')
	# 		qu_saveDir += '_e' + datetime.strptime(config['end'], "%Y-%m-%d %H:%M:%S").strftime('%m%d')
	# 	qu_saveDir += '/'
	# 	if(os.path.isdir(qu_saveDir)):
	# 		#print("Error: cant save to this folder, experiment already exists. Changing to time tagging")
	# 		#error = True
	# 		config['tag'] = ''
	# else:
	# 	qu_saveDir = master_saveDir + config['tag'] + '/'

def dev_print(print_all):
	global loc_list

	global dev_powerblade
	global dev_blees
	global dev_ligeiro
	global dev_blink

	global query_powerblade
	global query_blees
	global query_ligeiro
	global query_blink

	loc_list = ["("]

	dev_powerblade = ["("]
	dev_blees = ["("]
	dev_ligeiro = ["("]
	dev_blink = ["("]

	query_powerblade = False
	query_blees = False
	query_ligeiro = False
	query_blink = False

	for loc in config['locations']:
		loc_list.append(loc)
		loc_list.append(",")

	loc_list[-1] = ")"
	loc_list = "".join(loc_list)

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
			dev_blees.append("\"")
			dev_blees.append(dev)
			dev_blees.append("\"")
			dev_blees.append(",")

		elif(devType == "d0"):	# Ligeiro
			query_ligeiro = True
			dev_ligeiro.append("\"")
			dev_ligeiro.append(dev)
			dev_ligeiro.append("\"")
			dev_ligeiro.append(",")

		elif(devType == "90"):	# Blink	
			query_blink = True
			dev_blink.append("\"")
			dev_blink.append(dev)
			dev_blink.append("\"")
			dev_blink.append(",")

		else:
			print("Unknown device type: " + dev)

	dev_powerblade[-1] = ")"
	dev_blees[-1] = ")"
	dev_ligeiro[-1] = ")"
	dev_blink[-1] = ")"

	# Repurpose these variables to be strings rather than lists
	dev_powerblade = "".join(dev_powerblade)
	dev_blees = "".join(dev_blees)
	dev_ligeiro = "".join(dev_ligeiro)
	dev_blink = "".join(dev_blink)

	devNames = []
	if(print_all and query_powerblade):
		aws_c.execute('select \'PowerBlade\', deviceMAC, location, deviceName from valid_powerblades where deviceMAC in ' + dev_powerblade + ';')
		devNames.extend(aws_c.fetchall())
	if(print_all and  query_blees):
		aws_c.execute('select concat(deviceType, \'\\t\'), deviceMAC, location, deviceName from valid_lights where deviceMAC in ' + dev_blees + ';')
		devNames.extend(aws_c.fetchall())
	if(print_all and query_ligeiro):
		aws_c.execute('select concat(deviceType, \'\\t\'), deviceMAC, location, deviceName from valid_lights where deviceMAC in ' + dev_ligeiro + ';')
		devNames.extend(aws_c.fetchall())
	if(query_blink):
		aws_c.execute('select \'Blink\\t\', deviceMAC, location, room from valid_blinks where deviceMAC in ' + dev_blink + ';')
		devNames.extend(aws_c.fetchall())

	for line in devNames:
		print("\t" + str(line[0]) + "\t" + str(line[1]) + "\tLocation " + str(line[2]) + "\t" + str(line[3]))

	# for dev in config['devices']:
	# 	print("\t" + str(dev))

# Confirm parameters

check_tag()

print("\nPowerBlade Deployment Plotting Program")

def print_parameters():

	if(config['type'] == 'plot'):
		print("\nPlotting data from the following devices:")
		dev_print(True)
	elif(config['type'] == 'energy'):
		print("\nQuerying " + config['type'] + " from the following devices")
		dev_print(True)
	elif(config['type'] == 'blink'):
		print("\nQuerying " + config['type'] + " from the following devices")
		dev_print(False)
	else:
		print("\nQuerying " + config['type'])

	if(config['type'] != 'results'):
		print("\nFrom the following locations")
		for loc in sorted(config['locations']):
			print("\tLocation " + loc)

	if(config['type'] != 'results'):
		print("\nOver the following time period:")
		config['startDay'] = config['start'][0:10]
		config['endDay'] = config['end'][0:10]
		if(config['type'] == 'plot' or config['type'] == 'blink'):
			print("From\t" + config['start'])
			print("To\t" + config['end'])
		#elif(config['type'] == 'energy'):
		else:
			print("From\t" + config['startDay'])
			print("To\t" + config['endDay'])

	if(config['type'] == 'plot'):
		if(config['sum']):
			print("\nWith sum of power also plotted")
		else:
			print("\nWithout sum of power plotted")

	if(config['type'] == 'energy' and config['tag'] != ''):
		print('\nTag for save file: ' + config['tag'])

print_parameters()

print("\nTo confirm, push enter. To modify:")
print("\t'type [plot, energy, results, blink]'")
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

	if(confirm_list[0] == 'exit'):
		sys.exit()
	elif(confirm_list[0] == 'type'):
		if(confirm_list[1] == 'plot' or confirm_list[1] == 'energy' or confirm_list[1] == 'results' or confirm_list[1] == 'blink'):
			config['type'] = confirm_list[1]
			changes = True
		else:
			print("Usage is type [plot, energy, results, blink]")
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
			elif((len(dev) != 12) or (dev[0:6] != 'c098e5')):
				print(len(dev))
				print(dev[0:5])
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

		aws_c.execute('select lower(deviceMAC) from valid_devices where location=' + confirm_list[devOffset] + ';')
		device_list = aws_c.fetchall()
		devList = [i[0] for i in device_list]

		if(devType == 'replace'):
			config['devices'] = devList
			config['locations'] = confirm_list[devOffset]
		elif(devType == 'add'):
			config['devices'] = config['devices'] + devList
			if confirm_list[devOffset] not in config['locations']:
				config['locations'] = config['locations'] + confirm_list[devOffset]
		else:
			config['devices'] = [x for x in config['devices'] if x not in devList]
			config['locations'] = [x for x in config['locations'] if x != confirm_list[devOffset]]
		changes = True
	elif(confirm_list[0] == 'start' or confirm_list[0] == 'end'):
		try:
			if(len(confirm_list[1].split('-')) == 2):
				confirm_list[1] = '2017-' + confirm_list[1]
			if(len(confirm_list) == 2):
				try:
					datetime.strptime(confirm_list[1], '%Y-%m-%d')
					config[confirm_list[0]] = confirm_list[1] + " " + config[confirm_list[0]].split(" ")[1]
					changes = True
				except:
					datetime.strptime(confirm_list[1], '%H:%M:%S')
					config[confirm_list[0]] = config[confirm_list[0]].split(" ")[0] + " " + confirm_list[1]
					changes = True
			else:
				date_text = confirm_list[1] + " " + confirm_list[2]
				datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
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
	# elif(confirm_list[0] == 'tag'):
	# 	if(len(confirm_list) != 2):
	# 		error = True
	# 		print("Usage is 'tag [tag]'")
	# 	elif(confirm_list[1] == '' or confirm_list[1] == 'clear'):
	# 		config['tag'] = ''
	# 		changes = True
	# 	elif(confirm_list[1] == 'info'):
	# 		config['tag'] = 'info'
	# 		changes = True
	# 	elif(os.path.isdir(master_saveDir + confirm_list[1])):
	# 		error = True
	# 		print("Error: save directory already exists")
	# 	else:
	# 		config['tag'] = confirm_list[1]
	# 		changes = True
	elif(confirm_list[0] == 'pass'):
		error = True
	else:
		error = True
		print("Unknown command")

	config['tag'] = 'info'
	check_tag()

	if(error == False):
		print(chr(27) + "[2J")
		print_parameters()

	confirm = pytch.input_loop("\nPress enter, or next change: ")
		

if(changes):
	if(raw_input("\nSave changes to config file? [y/n]: ") == "y"):
		with open('.plotconfig', 'w') as outfile:
		    json.dump(config, outfile)

if(config['type'] == 'energy'):
	if(raw_input("\nSave data to final data table? [y/n]: ") == "y"):
		save_to_final = True
	else:
		save_to_final = False


print("\nRunning queries...\n")

check_tag()

mkdir(qu_saveDir)

cp('.plotconfig', qu_saveDir)

# Create human readable tag for the test
configTxt = open(qu_saveDir + 'plotConfig.txt', 'w')
configTxt.write('PowerBlade Deployment Experiment Data\n\n')
configTxt.write('\tType:\t\t' + config['type'] + '\n\n')
configTxt.write('\tStart:\t\t' + config['start'] + '\n')
configTxt.write('\tEnd:\t\t' + config['end'] + '\n')
configTxt.write('\tLocations:\t')
for locs in config['locations']:
	configTxt.write(locs + ' ')
configTxt.write('\n\n')
configTxt.write('\tDevices:\t')
for devs in config['devices']:
	configTxt.write(devs + '\n\t\t\t\t')
configTxt.write('\n')
configTxt.close()

dStart = datetime.strptime(config['start'], "%Y-%m-%d %H:%M:%S")
dEnd = datetime.strptime(config['end'], "%Y-%m-%d %H:%M:%S")

duration = (dEnd - dStart).total_seconds()
duration_days = int(math.ceil(duration / 86400))



####################################################################
#
# This section is for the plot option
#
####################################################################

if(config['type'] == 'plot'):

	downsample = int(duration/10000)

	if(query_powerblade):
		aws_c.execute("select t2.deviceName, t1.timest, t1.avgPower from " \
			"(select round(unix_timestamp(timestamp)/(" + str(downsample) + ")) as timekey, " \
			"deviceMAC, max(timestamp) as timest, avg(power) as avgPower from dat_powerblade force index (devPower) where deviceMAC in " + \
			dev_powerblade + " and timestamp between \"" + str(config['start']) + "\" and \"" + str(config['end']) + "\"" + \
			"group by deviceMAC, timekey) t1 " \
			"join active_powerblades t2 on t1.deviceMAC=t2.deviceMAC " \
			"order by t2.deviceName, t1.timest;")
		data_pb = aws_c.fetchall()
		
		if(config['sum']):
			aws_c.execute("select timestamp, sum(power) from dat_powerblade where deviceMAC in " + \
				dev_powerblade + " and timestamp between \"" + config['start'] + "\" and \"" + config['end'] + "\" " + \
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
	plt.write('set terminal postscript enhanced eps solid color font "Helvetica,14" size 6in,4in\n')
	plt.write('set output "datfile.eps"\n')

	plt.write('set xdata time\n')
	plt.write('set key under\n')
	plt.write('set timefmt \"\\\"%Y-%m-%d %H:%M:%S\\\"\"\n')
	plt.write('set format x \"%m-%d\\n%H:%M\"\n')

	plt.write('plot for [IDX=0:' + str(plot_count) + '] \'datfile.dat\' i IDX u 1:2 w lines title columnheader(1)\n')
	plt.close()


	# Clean up anything left from last time (in the case of errors)
	# if(os.path.exists('datfile.eps')):
	# 	os.remove('datfile.eps')
	# if(os.path.exists('datfile.pdf')):
	# 	os.remove('datfile.pdf')

	# Generate plot and convert to PDF
	gnuplot('datfile.plt')
	epstopdf('datfile.eps')

	# Show plot file
	# img = subprocess.Popen(['open', 'datfile.pdf'])
	# img.wait()

	# Remove temporary file
	os.remove('datfile.eps')

	# Move data to saveDir
	mv('datfile.dat', qu_saveDir)
	mv('datfile.plt', qu_saveDir)
	mv('datfile.pdf', qu_saveDir)




####################################################################
#
# This section is for the energy option
#
####################################################################

elif(config['type'] == 'energy'):

	if(query_powerblade == False):
		print("Error: At least one PowerBlade required for energy printing")
		exit()

	# Step 0: Alter the views acccording to the specified query paremeters
	# Day energy: maximum energy minus minimum energy for each device for each day
	print("Altering views for energy query...\n")
	aws_c.execute('alter view day_energy_pb as ' \
		'select date(timestamp) as dayst, deviceMAC, (max(energy) - min(energy)) as dayEnergy ' \
		'from dat_powerblade force index (devTimeEnergy) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and deviceMAC in ' + dev_powerblade + ' and energy!=999999.99 group by deviceMAC, dayst;')
	# aws_c.execute('alter view day_energy_pb as ' \
	# 	'select date(timestamp) as dayst, deviceMAC, (max(energy) - min(energy)) as dayEnergy ' \
	# 	'from loc0_dat_powerblade force index (devTimeEnergy) ' \
	# 	'where energy!=999999.99 group by deviceMAC, dayst;')
	aws_c.execute('alter view dev_resets as ' \
		'select date(timestamp) as dayst, deviceMAC, ' \
		'min(energy) as minEnergy, '
		'case when min(energy)<1.75 then 1 else 0 end as devReset, min(timestamp) as minTs ' \
		'from dat_powerblade force index(devTimeEnergy) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and deviceMAC in ' + dev_powerblade + ' ' \
		'group by dayst, deviceMAC;')
	# aws_c.execute('alter view dev_resets as ' \
	# 	'select date(timestamp) as dayst, deviceMAC, ' \
	# 	'min(energy) as minEnergy, '
	# 	'case when min(energy)<1.75 then 1 else 0 end as devReset, min(timestamp) as minTs ' \
	# 	'from loc0_dat_powerblade force index(devTimeEnergy) ' \
	# 	'group by dayst, deviceMAC;')
	# Max power - maximum power per device over the time period
	aws_c.execute('alter view maxPower_pb as ' \
		'select deviceMAC, max(power) as maxPower from dat_powerblade force index (devTimePower) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and power != 120.13 ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;')
	# aws_c.execute('alter view maxPower_pb as ' \
	# 	'select deviceMAC, max(power) as maxPower from loc0_dat_powerblade force index (devTimePower) ' \
	# 	'where power != 120.13 group by deviceMAC;')
	aws_c.execute('alter view avgPower_pb as ' \
		'select deviceMAC, min(power) as minPower, avg(power) as avgPower, max(power) as maxPower ' \
		'from dat_powerblade t1 force index(devTimePower) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and power>(select case when maxPower>10 then 0.1*maxPower else 0.5*maxPower end from maxPower_pb t2 where t1.deviceMAC=t2.deviceMAC) ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;')
	# aws_c.execute('alter view avgPower_pb as ' \
	# 	'select deviceMAC, min(power) as minPower, avg(power) as avgPower, max(power) as maxPower, ' \
	# 	'(select avg(power) from loc0_dat_powerblade force index(devDevPower) where deviceMAC=t1.deviceMAC and power<=(select avg(power) from loc0_avg_power where deviceMAC=t1.deviceMAC)) as q1Pwr, ' \
	# 	'(select avg(power) from loc0_dat_powerblade force index(devDevPower) where deviceMAC=t1.deviceMAC and power>=(select avg(power) from loc0_avg_power where deviceMAC=t1.deviceMAC)) as q3Pwr ' \
	# 	'from loc0_dat_powerblade t1 force index(devTimePower) ' \
	# 	'where power>(select case when maxPower>10 then 0.1*maxPower else 0.5*maxPower end from maxPower_pb t2 where t1.deviceMAC=t2.deviceMAC) ' \
	# 	'group by deviceMAC;')
		

	day_en_str = ''
	avg_pwr_str = ''
	# Step 0.5: Handle light data
	if(query_blees):
		aws_c.execute('alter view energy_blees as ' \
			'select round(unix_timestamp(timestamp)/(5*60)) as timekey, deviceMAC, date(timestamp) as dayst, ' \
			'case when lux>(select avgLux from avg_lux t2 where t1.deviceMAC=t2.deviceMAC) then ' \
			'(select power*5/60 from valid_lights t3 where t1.deviceMAC=t3.deviceMAC) else 0 end as \'onoff\' ' \
			'from dat_blees t1 force index (devLux) ' \
			'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
			'and deviceMAC in ' + dev_blees + ' group by deviceMAC, timekey;')
		aws_c.execute('alter view day_energy_blees as ' \
			'select dayst, deviceMAC, sum(onoff) as dayEnergy from ' \
			'energy_blees group by deviceMAC, dayst;')
		day_en_str += ' union select * from day_energy_blees'
		avg_pwr_str += ' union (select deviceMAC, power, power, power, power, power from valid_lights where deviceMAC in ' + dev_blees + ')'
	if(query_ligeiro):
		aws_c.execute('alter view energy_ligeiro as ' \
			'select round(unix_timestamp(timestamp)/(5*60)) as timekey, deviceMAC, date(timestamp) as dayst, ' \
			'case when (1+max(count)-min(count)) >= 1 then '\
			'(select power*5/60 from valid_lights t2 where t1.deviceMAC=t2.deviceMAC) else 0 end as \'onoff\' ' \
			'from dat_ligeiro t1 ' \
			'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
			'and deviceMAC in ' + dev_ligeiro + ' group by deviceMAC, timekey;')
		aws_c.execute('alter view day_energy_ligeiro as ' \
			'select dayst, deviceMAC, sum(onoff) as dayEnergy from ' \
			'energy_ligeiro group by deviceMAC, dayst;')
		day_en_str += ' union select * from day_energy_ligeiro'
		avg_pwr_str += ' union (select deviceMAC, power, power, power, power, power from valid_lights where deviceMAC in ' + dev_ligeiro + ')'

	aws_c.execute('alter view day_energy as select * from day_energy_pb tta where ' \
		'(select actReset from dev_actResets ttb where tta.deviceMAC=ttb.deviceMAC and tta.dayst=ttb.dayst)=0' + day_en_str + ';')
	aws_c.execute('alter view avg_power as select * from avgPower_pb' + avg_pwr_str + ';')

	# Step 1: Unified query for energy and power
	print("Running data query...\n")
	aws_c.execute('select t1.deviceMAC, t1.deviceName, t1.location, t1.category, t1.deviceType, t2.avgEnergy, t2.avgEnergy, t2.totEnergy, t3.avgPower, ' \
		't2.minEnergy, 1, 1, t2.maxEnergy, ' \
		't3.minPower, 1, 1, t3.maxPower from ' \
		'active_devices t1 ' \
		'join (select deviceMAC, min(dayEnergy) as minEnergy, ' \
		'sum(dayEnergy)/' + str(duration_days) + ' as avgEnergy, ' \
		'max(dayEnergy) as maxEnergy, '
		'sum(dayEnergy) as totEnergy ' \
		'from day_energy tday group by deviceMAC) t2 ' \
		'on t1.deviceMAC=t2.deviceMAC ' \
		'join avg_power t3 ' \
		'on t1.deviceMAC=t3.deviceMAC ' \
		'order by t2.avgEnergy;')
	expData = aws_c.fetchall()
	# aws_c.execute('select t1.deviceMAC, t1.deviceName, t1.location, t1.category, t1.deviceType, t2.avgEnergy, t2.avgEnergy, t2.totEnergy, t3.avgPower, ' \
	# 	't2.minEnergy, t2.q1DayEn, t2.q3DayEn, t2.maxEnergy, ' \
	# 	't3.minPower, t3.q1Pwr, t3.q3Pwr, t3.maxPower from ' \
	# 	'active_devices t1 ' \
	# 	'join (select deviceMAC, min(dayEnergy) as minEnergy, ' \
	# 	'(select avg(dayEnergy) from day_energy_full where deviceMAC=tday.deviceMAC and dayEnergy<=(select avg(dayEnergy) from day_energy_full where deviceMAC=tday.deviceMAC)) as q1DayEn, ' \
	# 	'avg(dayEnergy) as avgEnergy, ' \
	# 	'(select avg(dayEnergy) from day_energy_full where deviceMAC=tday.deviceMAC and dayEnergy>=(select avg(dayEnergy) from day_energy_full where deviceMAC=tday.deviceMAC)) as q3DayEn, ' \
	# 	'max(dayEnergy) as maxEnergy, '
	# 	'sum(dayEnergy) as totEnergy ' \
	# 	'from day_energy_full tday group by deviceMAC) t2 ' \
	# 	'on t1.deviceMAC=t2.deviceMAC ' \
	# 	'join avg_power t3 ' \
	# 	'on t1.deviceMAC=t3.deviceMAC ' \
	# 	'order by t2.avgEnergy;')
	# expData = aws_c.fetchall()
	#'(select sum(dayEnergy)/' + str(duration_days) + ' from day_energy tq1 where tday.deviceMAC=tq1.deviceMAC and tq1.dayEnergy<=(select sum(tday.dayEnergy)/' + str(duration_days) + ' from day_energy tavg where tavg.deviceMAC=tday.deviceMAC)) as q1DayEn, ' \
	#'(select (sum(dayEnergy)/' + str(duration_days) + ') from day_energy tq3 where tday.deviceMAC=tq3.deviceMAC and tq3.dayEnergy>=(select sum(tday.dayEnergy)/' + str(duration_days) + ' from day_energy tavg where tavg.deviceMAC=tday.deviceMAC)) as q3DayEn, ' \
	#'join (select deviceMAC, avg(dayEnergy) as avgEnergy, stddev(dayEnergy) as stdEnergy, sum(dayEnergy) as totEnergy ' \

	# Step 2: Ground Truth
	aws_c.execute('select location, avg(energy), count(*), ' + str(duration_days) + '-count(*) from most_recent_gnd_truth where location in ' + loc_list + ' and ' \
		'date(dayst)>=\'' + config['startDay'] + '\' and date(dayst)<=\'' + config['endDay'] + '\' ' \
		'group by location;')
	gndTruth = aws_c.fetchall()

	tot_gndTruth = 0
	min_days = duration_days
	for truth in gndTruth:
		tot_gndTruth += truth[1]
		if truth[2] < min_days:
			min_days = truth[2]

	missing_days = duration_days - min_days

	outfile_pb = open('breakdown_pb.dat', 'w')
	outfile_li = open('breakdown_li.dat', 'w')
	boxfile_pb = open('boxplot_pb.dat', 'w')
	boxfile_li = open('boxplot_li.dat', 'w')
	outfile = open ('tot_energy.dat', 'w')

	labelstr = ""
	energyCutoff = 1200

	total_measured_energy = 0

	# Energy Printout
	for idx, (mac, name, loc, devCat, devType, dayEnergy, var, totEnergy, power, minEnergy, q1Energy, q3Energy, maxEnergy, minPower, q1Power, q3Power, maxPower) in enumerate(expData):
		total_measured_energy += dayEnergy
		print(str(idx) + " " + str(mac) + " \"" + str(name) + "\" " + str(loc) + " " + str(devCat) + " " + str(devType) + " " + str(dayEnergy) + " " + str(var) + " " + str(totEnergy) + " " + str(power))
		outfile.write(str(idx) + "\t" + str(mac) + "\t\"" + str(name) + "\"\t" + str(loc) + "\t" + str(devCat) + "\t" + str(devType) + "\t" + str(dayEnergy) + "\t" + str(var) + "\t" + str(totEnergy) + "\t" + str(power) + "\n")
		
		if(mac[6:8] == '70'):
			outfile_pb.write(str(idx) + "\t\"" + str(name) + "\"\t" + str(dayEnergy) + "\t" + str(power) + "\n")
			boxfile_pb.write(str(idx) + "\t\"" + str(name) + "\"\t" + str(minEnergy) + "\t" + str(q1Energy) + "\t" + str(dayEnergy) + "\t" + str(q3Energy) + "\t" + str(maxEnergy) + "\t" + str(minPower) + "\t" + str(q1Power) + "\t" + str(power) + "\t" + str(q3Power) + "\t" + str(maxPower) + "\t0.5\n")
		else:
			outfile_li.write(str(idx) + "\t\"" + str(name) + "\"\t" + str(dayEnergy) + "\t" + str(power) + "\n")
			boxfile_li.write(str(idx) + "\t\"" + str(name) + "\"\t" + str(minEnergy) + "\t" + str(q1Energy) + "\t" + str(dayEnergy) + "\t" + str(q3Energy) + "\t" + str(maxEnergy) + "\t" + str(minPower) + "\t" + str(q1Power) + "\t" + str(power) + "\t" + str(q3Power) + "\t" + str(maxPower) + "\t0.5\n")
		
		if(dayEnergy > energyCutoff):
			labelstr += 'set label at ' + str(idx) + ', ' + str(energyCutoff * 1.1) + ' \"' + str(int(dayEnergy)) + '\" center font \", 8\"\n'

	outfile.write('# total measured energy: ' + str(total_measured_energy) + '\n')
	outfile.write('# gnd truth: ' + str(tot_gndTruth) + '\n')
	outfile.write('# missing days: ' + str(missing_days) + '\n')

	outfile_pb.close()
	outfile_li.close()
	boxfile_pb.close()
	boxfile_li.close()

	breakdown(energyCutoff, labelstr, 'breakdown')

	# Generate plot and convert to PDF
	gnuplot('breakdown.plt')
	epstopdf('breakdown.eps')

	# Show plot file
	img = subprocess.Popen(['open', 'breakdown.pdf'])
	img.wait()

	# Remove temporary file
	os.remove('breakdown.eps')

	# Move data to saveDir
	mv('tot_energy.dat', qu_saveDir)
	mv('breakdown_pb.dat', qu_saveDir)
	mv('breakdown_li.dat', qu_saveDir)
	mv('breakdown.plt', qu_saveDir)
	mv('breakdown.pdf', qu_saveDir)

	printEnergy(expData, total_measured_energy, tot_gndTruth, 'energy')

	gnuplot('energy_pwrCDF.plt')
	epstopdf('energy_pwrCDF.eps')

	os.remove('energy_pwrCDF.eps')

	mv('energy_pwrCDF.dat', qu_saveDir)
	mv('energy_pwrCDF.plt', qu_saveDir)
	mv('energy_pwrCDF.pdf', qu_saveDir)

	boxplot(8, 66.5, 3000, 'boxplot')

	gnuplot('boxplot.plt')
	epstopdf('boxplot.eps')

	img = subprocess.Popen(['open', 'boxplot.pdf'])
	img.wait()

	os.remove('boxplot.eps')

	mv('boxplot_pb.dat', qu_saveDir)
	mv('boxplot_li.dat', qu_saveDir)
	mv('boxplot.plt', qu_saveDir)
	mv('boxplot.pdf', qu_saveDir)

	# Upload to final results table
	#if(raw_input("\nSave data to final data table? [y/n]: ") == "y"):
	if(save_to_final):
		uploadStr = ''
		for mac, name, loc, devCat, devType, dayEnergy, var, totEnergy, power, minEnergy, q1Energy, q3Energy, maxEnergy, minPower, q1Power, q3Power, maxPower in expData:
			aws_c.execute('insert into final_results (addedDate, deviceMAC, deviceName, location, category, deviceType, avgEnergy, stdEnergy, totEnergy, avgPower) values (utc_timestamp(), \"' + \
				str(mac) + '\", \"' + str(name) + '\", ' + str(loc) + ', \"' + str(devCat) + '\", \"' + str(devType) + '\", ' + str(round(dayEnergy,2)) + ', ' + str(round(var,2)) + ', ' + str(round(totEnergy,2)) + ', ' + str(round(power,2)) + ');')
			aws_db.commit()
		for loc in config['locations']:
			try:
				loc2, totEnergy, truthDays, missing = gndTruth[[x[0] for x in gndTruth].index(int(loc))]
			except:
				totEnergy = 0
				truthDays = 0
				missing = duration_days
			aws_c.execute('insert into final_gnd (addedDate, location, startDate, endDate, duration, truthDays, missingDays, totMeas, totGnd) values (utc_timestamp(), ' + \
				str(loc) + ', \'' + config['startDay'] + '\', \'' + config['endDay'] + '\', ' + str(duration_days) + ', ' + str(truthDays) + ', ' + str(missing) + ', ' + str(round(total_measured_energy)) + ', ' + str(round(totEnergy,2)) + ');')
			aws_db.commit()
			





####################################################################
#
# This section is for results (combine everything)
#
####################################################################

elif(config['type'] == 'results'):

	num_locations = 8

	# aws_c.execute('select t1.catName, sum(t1.energy) as energy, avg(t1.power) as power from ' \
	# 	'(select location, concat_ws(\' \', category, deviceType) as catName, ' \
	# 	'sum(avgEnergy) as energy, avg(avgPower) as power ' \
	# 	'from mr_final_results ' \
	# 	'group by location, category, deviceType) t1 ' \
	# 	'group by catName '
	# 	'order by energy asc;')
	
	#aws_c.execute('select concat_ws(\' \', category, deviceType) as catName, ' \
	aws_c.execute('select category as catName, ' \
		'sum(avgEnergy)/' + str(num_locations) + ' as energy, '\
		'avg(avgPower) as power ' \
		'from mr_final_results ' \
		'where location!=2 ' \
		'and deviceMAC!=\'c098e57001A0\'' \
		'and deviceMAC!=\'c098e5700193\'' \
		'group by category ' \
		'order by energy asc;')
	
	expData = aws_c.fetchall()

	outfile_pb = open('results_pb.dat', 'w')
	outfile_li = open('results_li.dat', 'w')

	labelstr = ""
	energyCutoff = 1000
	energyTop = 1200
	energyCutoff_loc = 1320

	# Energy Printout
	for idx, (name, dayEnergy, power) in enumerate(expData):

		name = name.split('/')[0]

		#print(str(idx) + " \"" + str(name) + "\" " + str(dayEnergy) + " " + str(power))
		
		if(name[0:8] == 'Overhead'):
			outfile_li.write(str(idx) + "\t\"" + str(name) + "\"\t" + str(dayEnergy) + "\t" + str(power) + "\n")
		else:
			outfile_pb.write(str(idx) + "\t\"" + str(name) + "\"\t" + str(dayEnergy) + "\t" + str(power) + "\n")
		
		if(dayEnergy > energyCutoff):
			labelstr += 'set label at ' + str(idx) + ', ' + str(energyCutoff_loc) + ' \"' + str(int(dayEnergy)) + '\" center font \", 8\"\n'
		else:
			labelstr += 'set label at ' + str(idx) + ', ' + str(float(dayEnergy) + 100) + ' \"' + str(int(dayEnergy)) + '\" center font \", 8\"\n'

	outfile_pb.close()
	outfile_li.close()

	breakdown(energyTop, labelstr, 'results')

	# Generate plot and convert to PDF
	gnuplot('results.plt')
	epstopdf('results.eps')

	# Show plot file
	img = subprocess.Popen(['open', 'results.pdf'])
	img.wait()

	# Remove temporary file
	os.remove('results.eps')

	# Move data to saveDir
	mv('results_pb.dat', qu_saveDir)
	mv('results_li.dat', qu_saveDir)
	mv('results.plt', qu_saveDir)
	mv('results.pdf', qu_saveDir)








	# aws_c.execute('select t1.category, min(t1.catSum) as minCat, ' \
	# 	'(select avg(catSum) from mr_cat_breakdown t2 where t1.category=t2.category and t2.catSum<avg(t1.catSum)) as q1, ' \
	# 	'avg(t1.catSum) as meanCat, ' \
	# 	'(select avg(catSum) from mr_cat_breakdown t3 where t1.category=t3.category and t3.catSum>avg(t1.catSum)) as q3, ' \
	# 	'max(t1.catSum) as maxCat ' \
	# 	'from mr_cat_breakdown t1 ' \
	# 	'group by t1.category ' \
	# 	'order by meanCat asc;')
	aws_c.execute('select * from mr_cat_en_pwr;')
	expData = aws_c.fetchall();

	aws_c.execute('select t1.category, min(t1.catSum) as minCat, ' \
		'(select avg(catSum) from mr_cat_breakdown t2 where t1.category=t2.category and t2.catSum<avg(t1.catSum)) as q1, ' \
		'avg(t1.catSum) as meanCat, ' \
		'(select avg(catSum) from mr_cat_breakdown t3 where t1.category=t3.category and t3.catSum>avg(t1.catSum)) as q3, ' \
		'max(t1.catSum) as maxCat ' \
		'from mr_cat_breakdown t1 ' \
		'where t1.category=\'Phone charger\' and t1.catSum>0 '
		'group by t1.category;')
	phone = aws_c.fetchall()[0];

	aws_c.execute('select t1.category, min(t1.catSum) as minCat, ' \
		'(select avg(catSum) from mr_cat_breakdown t2 where t1.category=t2.category and t2.catSum<avg(t1.catSum)) as q1, ' \
		'avg(t1.catSum) as meanCat, ' \
		'(select avg(catSum) from mr_cat_breakdown t3 where t1.category=t3.category and t3.catSum>avg(t1.catSum)) as q3, ' \
		'max(t1.catSum) as maxCat ' \
		'from mr_cat_breakdown t1 ' \
		'where t1.category=\'Overhead\' and t1.catSum>0 '
		'group by t1.category;')
	overhead = aws_c.fetchall()[0];

	cat_pb = open('boxplot_pb.dat', 'w')
	cat_li = open('boxplot_li.dat', 'w')

	# labelstr = ""
	# energyCutoff = 1000
	# energyTop = 1200
	# energyCutoff_loc = 1320

	# Energy Printout
	for idx, (name, minEn, q1En, meanEn, q3En, maxEn, minPwr, q1Pwr, meanPwr, q3Pwr, maxPwr) in enumerate(expData):

		name = name.split('/')[0]

		#print(str(idx) + " \"" + str(name) + "\" " + str(dayEnergy) + " " + str(power))


		
		if(name[0:8] == 'Overhead'):
			cat_li.write(str(idx) + "\t\"" + str(name) + "\"\t" + str(overhead[1]) + "\t" + str(overhead[2]) + "\t" + str(overhead[3]) + "\t" + str(overhead[4]) + "\t" + str(overhead[5]) + "\t")
			outputFile = cat_li
		elif(name[0:13] == 'Phone charger'):
			cat_pb.write(str(idx) + "\t\"" + str(name) + "\"\t" + str(phone[1]) + "\t" + str(phone[2]) + "\t" + str(phone[3]) + "\t" + str(phone[4]) + "\t" + str(phone[5]) + "\t")
			outputFile = cat_pb
		else:
			cat_pb.write(str(idx) + "\t\"" + str(name) + "\"\t" + str(minEn) + "\t" + str(q1En) + "\t" + str(meanEn) + "\t" + str(q3En) + "\t" + str(maxEn) + "\t")
			outputFile = cat_pb

		outputFile.write(str(minPwr) + "\t" + str(q1Pwr) + "\t" + str(meanPwr) + "\t" + str(q3Pwr) + "\t" + str(maxPwr) + "\t0.5\n")
		
		# if(dayEnergy > energyCutoff):
		# 	labelstr += 'set label at ' + str(idx) + ', ' + str(energyCutoff_loc) + ' \"' + str(int(dayEnergy)) + '\" center font \", 8\"\n'
		# else:
		# 	labelstr += 'set label at ' + str(idx) + ', ' + str(float(dayEnergy) + 100) + ' \"' + str(int(dayEnergy)) + '\" center font \", 8\"\n'

	cat_pb.close()
	cat_li.close()

	boxplot(4, idx + 0.5, 3000, 'boxplot')

	# Generate plot and convert to PDF
	gnuplot('boxplot.plt')
	epstopdf('boxplot.eps')

	# Show plot file
	img = subprocess.Popen(['open', 'boxplot.pdf'])
	img.wait()

	# Remove temporary file
	os.remove('boxplot.eps')

	# Move data to saveDir
	mv('boxplot_pb.dat', qu_saveDir)
	mv('boxplot_li.dat', qu_saveDir)
	mv('boxplot.plt', qu_saveDir)
	mv('boxplot.pdf', qu_saveDir)













	aws_c.execute('select deviceMAC, ' \
		'avgEnergy, avgPower ' \
		'from mr_final_results ' \
		'where location!=1 ' \
		'and category!=\'Overhead\' ' \
		'group by deviceMAC ' \
		'order by avgEnergy asc;')

	expData = aws_c.fetchall()

	total_measured_energy = 0
	# Energy Printout
	for name, dayEnergy, power in expData:
		total_measured_energy += dayEnergy

	aws_c.execute('select sum(fullGnd) from mr_final_gnd_corr where location!=1;')
	final_gnd = aws_c.fetchall()[0][0]

	printEnergy([[0, row[0], 0, 0, 0, row[1], 0, 0, row[2], 0, 0, 0, 0, 0, 0, 0, 0] for row in expData], total_measured_energy, final_gnd, 'total')

	gnuplot('total_pwrCDF.plt')
	epstopdf('total_pwrCDF.eps')

	# Show plot file
	img = subprocess.Popen(['open', 'total_pwrCDF.pdf'])
	img.wait()

	os.remove('total_pwrCDF.eps')

	mv('total_pwrCDF.dat', qu_saveDir)
	mv('total_pwrCDF.plt', qu_saveDir)
	mv('total_pwrCDF.pdf', qu_saveDir)



####################################################################
#
# This section is for blink (occupancy)
#
####################################################################

elif(config['type'] == 'blink'):

	aws_c.execute('select t2.room, t1.ts, t1.minMot from ' \
		'(select round(unix_timestamp(timestamp)/(60*60)) as timekey, min(timestamp) as ts, deviceMAC, sum(minMot) as minMot ' \
		'from dat_blink force index (devMIN) ' \
		'where deviceMAC in ' + dev_blink + ' ' \
		'and timestamp between \"' + str(config['start']) + '\" and \"' + str(config['end']) + '\" ' \
		'group by timekey, deviceMAC) t1 ' \
		'join valid_blinks t2 ' \
		'on t1.deviceMAC=t2.deviceMAC ' \
		'order by t1.deviceMAC, t1.timekey;')
	blink_data = aws_c.fetchall()

	blink_out = open('blink.dat', 'w')

	plot_count = 0
	current_room = 0
	for room, ts, minMot in blink_data:
		if room != current_room:
			plot_count += 1
			current_room = room
			blink_out.write('\n\n\"' + current_room + '\"\n')
		blink_out.write('\"' + str(ts) + '\"\t' + str(minMot) + '\n')

	blink_out.close()

	# Create .plt file and fill
	plt = open('blink.plt', 'w')
	plt.write('set terminal postscript enhanced eps solid color font "Helvetica,14" size 3in,2.8in\n')
	plt.write('set output "blink.eps"\n')

	plt.write('set xdata time\n')
	plt.write('set key under\n')
	plt.write('set timefmt \"\\\"%Y-%m-%d %H:%M:%S\\\"\"\n')
	plt.write('set format x \"%m-%d\\n%H:%M\"\n')

	plt.write('plot for [IDX=0:' + str(plot_count) + '] \'blink.dat\' i IDX u 1:2 w lines title columnheader(1)\n')
	plt.close()

	# Generate plot and convert to PDF
	gnuplot('blink.plt')
	epstopdf('blink.eps')

	# Show plot file
	img = subprocess.Popen(['open', 'blink.pdf'])
	img.wait()

	# Remove temporary file
	os.remove('blink.eps')

	# Move data to saveDir
	mv('blink.dat', qu_saveDir)
	mv('blink.plt', qu_saveDir)
	cp('blink.pdf', qu_saveDir)





























