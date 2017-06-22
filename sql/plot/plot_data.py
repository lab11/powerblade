#!/usr/bin/env python

import mylogin
import MySQLdb
import json

from datetime import datetime, timedelta
import pytch

import os
import sys
import subprocess
from sh import epstopdf, gnuplot, mkdir, cp, mv

from printEnergy import printEnergy
from breakdown import breakdown
from boxplot import boxplot

import math
import numpy

def is_number(s):
    try:
        float(s)
        return True
    except:
        return False

query_startDay = datetime.utcnow().strftime('%Y_%m_%d_')

master_saveDir = os.environ['PB_DATA'] + "/savetest/" + str(query_startDay)

if not os.path.isdir(os.environ['PB_DATA'] + "/savetest/"):
	mkdir(os.environ['PB_DATA'] + "/savetest/")


pltconfig_str = '/'.join(sys.argv[0].split('/')[0:-1]) + '/.plotconfig'

# Read config file for start time, end time, and devices
config = {}
try:
	config_file = open(pltconfig_str, 'r')
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

def print_blink(ts_last, pwr_last, mot_last, time_last):
	if(maxVals[current_dev][0] > 0):
		pwr_print = pwr_last/maxVals[current_dev][0]
	else:
		pwr_print = 0
	if(maxVals[current_dev][1] > 0):
		mot_print = float(mot_last)/maxVals[current_dev][1]
	else:
		mot_print = 0
	if(maxVals[current_dev][2] > 0):
		time_print = float(time_last)/maxVals[current_dev][2]
	else:
		time_print = 0
	pb_out.write('\"' + str(ts_last) + '\"\t' + str(pwr_print) + '\t' + str(mot_print) + '\t' + str(time_print) + '\n')

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

total_complete = 0
def print_time():
	global total_complete
	total_complete += 1
	print('\nTotal elapsed time: ' + str(chop_microseconds(datetime.utcnow() - script_start)))
	print(str(round(100*float(total_complete)/total_scope,2)) + ' pct complete')

	if(total_complete == total_scope):
		remaining = 0
	else:
		remaining = chop_microseconds(((datetime.utcnow() - query_start)*total_scope/total_complete)-(datetime.utcnow() - query_start))
	print('Remaining time: ' + str(remaining) + '\n')

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

def dev_print():
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
	if(query_powerblade):
		aws_c.execute('select \'PowerBlade\', deviceMAC, location, deviceName from valid_powerblades_no1 where deviceMAC in ' + dev_powerblade + ';')
		devNames.extend(aws_c.fetchall())
	if(query_blees):
		aws_c.execute('select concat(deviceType, \'\\t\'), deviceMAC, location, deviceName from valid_lights where deviceMAC in ' + dev_blees + ';')
		devNames.extend(aws_c.fetchall())
	if(query_ligeiro):
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
		dev_print()
	elif(config['type'] == 'energy'):
		print("\nQuerying " + config['type'] + " from the following devices")
		dev_print()
	elif(config['type'] == 'blink'):
		print("\nQuerying " + config['type'] + " from the following devices")
		dev_print()
	else:
		print("\nQuerying " + config['type'])

	if(config['type'] != 'results' and config['type'] != 'occ'):
		print("\nFrom the following locations")
		for loc in sorted(config['locations']):
			print("\tLocation " + loc)

	if(config['type'] != 'results' and config['type'] != 'occ'):
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
print("\t'type [plot, energy, results, blink, occ]'")
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
		if(confirm_list[1] == 'plot' or confirm_list[1] == 'energy' or confirm_list[1] == 'results' or confirm_list[1] == 'blink' or confirm_list[1] == 'occ'):
			config['type'] = confirm_list[1]
			changes = True
		else:
			print("Usage is type [plot, energy, results, blink, occ]")
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
	elif(confirm_list[0] == 'room'):
		room = ' '.join(confirm_list[1:])
		
		locStr = ['(']
		for loc in config['locations']:
			locStr.append(str(loc))
			locStr.append(',')
		locStr[-1] = ')'
		locStr = ''.join(locStr)

		aws_c.execute('select lower(deviceMAC) from valid_devices where location in ' + locStr + ' and room=\'' + room + '\';')
		device_list = aws_c.fetchall()
		devList = [i[0] for i in device_list]

		config['devices'] = devList
		changes = True
	elif(confirm_list[0] == 'start' or confirm_list[0] == 'end'):
		try:
			if(len(confirm_list[1].split('-')) == 2):
				confirm_list[1] = '2017-' + confirm_list[1]
			if(len(confirm_list) == 2):
				try:
					strTime = datetime.strptime(confirm_list[1], '%Y-%m-%d').strftime('%Y-%m-%d')
					config[confirm_list[0]] = strTime + " " + config[confirm_list[0]].split(" ")[1]
					changes = True
				except:
					strTime = datetime.strptime(confirm_list[1], '%H:%M:%S').strftime('%H:%M:%S')
					config[confirm_list[0]] = config[confirm_list[0]].split(" ")[0] + " " + strTime
					changes = True
			else:
				date_text = confirm_list[1] + " " + confirm_list[2]
				config[confirm_list[0]] = datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
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
		with open(pltconfig_str, 'w') as outfile:
		    json.dump(config, outfile)

if(config['type'] == 'energy' or config['type'] == 'blink'):
	if(raw_input("\nSave data to final data table? [y/n]: ") == "y"):
		print("Saving to final data table")
		save_to_final = True
	else:
		print("Not saving to final data table")
		save_to_final = False


print("\nRunning queries...\n")

check_tag()

mkdir(qu_saveDir)

cp(pltconfig_str, qu_saveDir)

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



# Script body
script_start = datetime.utcnow()



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
			"join valid_powerblades t2 on t1.deviceMAC=t2.deviceMAC " \
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
	img = subprocess.Popen(['open', 'datfile.pdf'])
	img.wait()

	# Remove temporary file
	os.remove('datfile.eps')

	# Move data to saveDir
	mv('datfile.dat', qu_saveDir)
	mv('datfile.plt', qu_saveDir)
	cp('datfile.pdf', qu_saveDir)




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
	aws_c.execute('alter view dev_resets as ' \
		'select date(timestamp) as dayst, deviceMAC, ' \
		'min(energy) as minEnergy, '
		'case when min(energy)<1.75 then 1 else 0 end as devReset, min(timestamp) as minTs ' \
		'from dat_powerblade force index(devTimeEnergy) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and deviceMAC in ' + dev_powerblade + ' ' \
		'group by dayst, deviceMAC;')

	# Max power - maximum power per device over the time period
	aws_c.execute('alter view maxPower_pb as ' \
		'select deviceMAC, max(power) as maxPower from dat_powerblade force index (devTimePower) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and power != 120.13 ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;')
	# This only needs to be 'create' for the first time. Then change to 'alter'
	aws_c.execute('create view avgPower_pb as ' \
		'select deviceMAC, min(power) as minPower, avg(power) as avgPower, max(power) as maxPower ' \
		'from dat_powerblade t1 force index(devTimePower) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and power>(select case when maxPower>10 then 0.1*maxPower else 0.5*maxPower end from maxPower_pb t2 where t1.deviceMAC=t2.deviceMAC) ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;')
		

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
	expData = aws_c.fetchall()

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
		#'and category!=\'Overhead\' ' \
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

	# downsample = int(duration/100)

	# aws_c.execute('select t2.room, t1.ts, t1.ts2, t1.minMot from ' \
	# 	'(select round(unix_timestamp(timestamp)/(' + str(downsample) + ')) as timekey, max(timestamp) as ts, left(max(timestamp), 16) as ts2, deviceMAC, sum(minMot) as minMot ' \
	# 	'from dat_blink force index (devMIN) ' \
	# 	'where deviceMAC in ' + dev_blink + ' ' \
	# 	'and timestamp between \"' + str(config['start']) + '\" and \"' + str(config['end']) + '\" ' \
	# 	'group by timekey, deviceMAC) t1 ' \
	# 	'join valid_blinks t2 ' \
	# 	'on t1.deviceMAC=t2.deviceMAC ' \
	# 	'order by t1.deviceMAC, t1.timekey;')
	# blink_data = aws_c.fetchall()

	# blink_out = open('blink.dat', 'w')

	# plot_count = 0
	# current_room = 0
	# # Find max values (used for normalization)
	# maxVals = {}
	# for room, ts, ts2, minMot in blink_data:
	# 	if room != current_room:
	# 		plot_count += 1
	# 		current_room = room
	# 		maxVals[current_room] = minMot
	# 	if minMot > maxVals[current_room]:
	# 		maxVals[current_room] = minMot
	# 	#print(ts2)

	# current_room = 0
	# xcorr_data = {}
	# for room, ts, ts2, minMot in blink_data:
	# 	if room != current_room:
	# 		current_room = room
	# 		blink_out.write('\n\n\"Blink: ' + current_room + '\"\n')
	# 	blink_out.write('\"' + str(ts) + '\"\t' + str(minMot/maxVals[current_room]) + '\n')
	# 	xcorr_data[ts2] = float(minMot/maxVals[current_room])

	# blink_out.close()

	# aws_c.execute('select t2.deviceName, t1.ts, t1.ts2, t1.avgPower from ' \
	# 	'(select round(unix_timestamp(timestamp)/(' + str(downsample) + ')) as timekey, max(timestamp) as ts, left(max(timestamp), 16) as ts2, deviceMAC, avg(power) as avgPower ' \
	# 	'from dat_powerblade force index (devPower) ' \
	# 	'where deviceMAC in ' + dev_powerblade + ' ' \
	# 	'and timestamp between \"' + str(config['start']) + '\" and \"' + str(config['end']) + '\" ' \
	# 	'group by deviceMAC, timekey) t1 ' \
	# 	'join valid_powerblades t2 ' \
	# 	'on t1.deviceMAC=t2.deviceMAC ' \
	# 	"order by t2.deviceName, t1.timekey;")
	# pb_data = aws_c.fetchall()

	# pb_out = open('pb.dat', 'w')

	# pb_count = 0
	# current_dev = 0
	# for dev, ts, ts2, pwr in pb_data:
	# 	if dev != current_dev:
	# 		pb_count += 1
	# 		current_dev = dev
	# 		maxVals[current_dev] = pwr
	# 	if pwr > maxVals[current_dev]:
	# 		maxVals[current_dev] = pwr

	# current_dev = 0
	# xcorr_pb = {}
	# xcorr_pb_act = {}	# Active (on) measurements (above 10%)
	# for dev, ts, ts2, pwr in pb_data:
	# 	if dev != current_dev:
	# 		current_dev = dev
	# 		xcorr_pb[current_dev] = {}
	# 		xcorr_pb_act[current_dev] = {}
	# 		xcorr_pb[current_dev]['pb'] = []
	# 		xcorr_pb_act[current_dev]['pb'] = []
	# 		xcorr_pb[current_dev]['blink'] = []
	# 		xcorr_pb_act[current_dev]['blink'] = []
	# 	#print(ts2)
	# 	try:
	# 		xcorr_pb[current_dev]['blink'].append(xcorr_data[ts2])
	# 		xcorr_pb[current_dev]['pb'].append(float(pwr/maxVals[current_dev]))

	# 		if(float(pwr/maxVals[current_dev]) >= .1):
	# 			xcorr_pb_act[current_dev]['blink'].append(xcorr_data[ts2])
	# 			xcorr_pb_act[current_dev]['pb'].append(float(pwr/maxVals[current_dev]))

	# 	except:
	# 		print('Couldnt find ' + str(ts2))

	files_to_open = []

	locRooms = []

	total_data = []

	query_start = datetime.utcnow()

	total_scope = 0

	idle_savings_potential = {}
	idle_savings_potential['.5'] = 0
	idle_savings_potential['.75'] = 0

	for loc in config['locations']:
		aws_c.execute('select t1.room from ' \
			'(select room from valid_blinks where location=' + str(loc) + ' group by room) t1 ' \
			'join ' \
			'(select room from valid_powerblades_no1 where location=' + str(loc) + ' ' \
			'and deviceMAC in ' + dev_powerblade + ' '
			'group by room) t2 ' \
			'on t1.room=t2.room;')
		rooms = aws_c.fetchall()

		for room in rooms:
			total_scope += 1
			locRooms.append([loc, room[0]])


	for loc, room in locRooms:
		dev_powerblade_room = '(select deviceMAC from valid_powerblades where location=' + str(loc) + ' and room=\'' + str(room) + '\' ' \
			'and deviceMAC in ' + dev_powerblade + ')'

		item_start = datetime.utcnow()
		sys.stdout.write('Getting correlation for location ' + str(loc) + ' ' + room + ' ... ')
		sys.stdout.flush()
		aws_c.execute('select deviceMAC, deviceName, ' \
			'convert_tz(tsMin, \'UTC\', \'America/Detroit\') as tsMin, ' \
			'avgPower, minMot, ' \
			'timediff(extract(hour_second from \'2000-01-01 00:00:00\'), extract(hour_second from convert_tz(tsMin, \'UTC\', \'America/Detroit\'))) as timeDiff ' \
			'from mr_dat_occ ' \
			'where deviceMAC in ' + dev_powerblade_room + ' ' \
			'and tsMin between \"' + str(config['start']) + '\" and \"' + str(config['end']) + '\" ' \
			'order by deviceMAC, tsMin;')
		pb_data = aws_c.fetchall()

		print(str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')

		runString = 'L' + str(loc) + '_' + room.replace(' ', '_')

		pb_out = open('pb_' + runString + '.dat', 'w')

		pb_count = 0
		current_dev = 0
		maxVals = {}
		minVals = {}
		new_pb_data = []
		for idx, (dev, name, ts, pwr, mot, timeDiff) in enumerate(pb_data):

			if(abs(timeDiff) >= timedelta(hours=12)):
				timeDiff = (timedelta(hours=24)-abs(timeDiff)).seconds
			else:
				timeDiff = abs(timeDiff).seconds
			# Save back into the data structure
			new_pb_data.append([dev, name, ts, pwr, mot, timeDiff])

			if dev != current_dev:
				pb_count += 1
				current_dev = dev
				maxVals[current_dev] = [pwr, mot, timeDiff]
				minVals[current_dev] = pwr
			if pwr > maxVals[current_dev][0]:
				maxVals[current_dev][0] = pwr
			if mot > maxVals[current_dev][1]:
				maxVals[current_dev][1] = mot
			if timeDiff > maxVals[current_dev][2]:
				maxVals[current_dev][2] = timeDiff;
			if pwr < minVals[current_dev]:
				minVals[current_dev] = pwr


		for devMAC in maxVals:
			if maxVals[devMAC][0] == minVals[devMAC]:
				minVals[devMAC] = 0
			

		current_dev = 0
		current_day = 0
		xcorr_pb = {}
		xcorr_pb_act = {}
		dep_pb = {}
		interdev_pb = {}
		interdev_day = {}
		names = {}
		idleP = {}
		pwr_last = 0
		mot_last = 0
		for dev, name, ts, pwr, mot, timeDiff in new_pb_data:
			dayst = str(ts.strftime('%Y-%m-%d 00:00:00'))
			if dev != current_dev:
				current_dev = dev
				xcorr_pb[current_dev] = {}
				xcorr_pb_act[current_dev] = {}
				interdev_pb[current_dev] = {}
				interdev_day[current_dev] = {}
				xcorr_pb[current_dev]['pb'] = []
				xcorr_pb_act[current_dev]['pb'] = []
				xcorr_pb[current_dev]['blink'] = []
				xcorr_pb_act[current_dev]['blink'] = []
				dep_pb[current_dev] = {}
				dep_pb[current_dev]['po'] = 0
				dep_pb[current_dev]['pp'] = 0
				dep_pb[current_dev]['pop'] = 0
				dep_pb[current_dev]['tot'] = 0
				names[current_dev] = name
				idleP[current_dev] = []

			if current_day != dayst:
				current_day = dayst
				interdev_day[current_dev][current_day] = {}

			if(maxVals[current_dev][0] > 0):
				xcorr_pb[current_dev]['pb'].append(float(pwr/maxVals[current_dev][0]))
				interdev_pb[current_dev][ts] = float((pwr-minVals[current_dev])/(maxVals[current_dev][0]-minVals[current_dev]))
				interdev_day[current_dev][current_day][ts] = float((pwr-minVals[current_dev])/(maxVals[current_dev][0]-minVals[current_dev]))
			else:
				xcorr_pb[current_dev]['pb'].append(0)
				interdev_pb[current_dev][ts] = minVals[current_dev]
				interdev_day[current_dev][current_day][ts] = minVals[current_dev]
				#print('Zero maximum for ' + current_dev)
			xcorr_pb[current_dev]['blink'].append(float(float(mot)/maxVals[current_dev][1]))

			dep_pb[current_dev]['tot'] += 1

			if(float(float(mot)/maxVals[current_dev][1]) > .2):
				dep_pb[current_dev]['po'] += 1

			if(maxVals[current_dev][0] > 0 and float((pwr-minVals[current_dev])/(maxVals[current_dev][0]-minVals[current_dev])) > .2):
				xcorr_pb_act[current_dev]['pb'].append(float(pwr_last/maxVals[current_dev][0]))
				#xcorr_pb_act[current_dev]['blink'].append(float(float(mot_last)/maxVals[current_dev][1]))	
				xcorr_pb_act[current_dev]['blink'].append(float(float(mot_last)/maxVals[current_dev][1]))

				dep_pb[current_dev]['pp'] += 1
				if(float(float(mot)/maxVals[current_dev][1]) > .2):
					dep_pb[current_dev]['pop'] += 1
			else:
				idleP[current_dev].append(pwr)

				if(maxVals[current_dev][0] > 0 and float((pwr_last-minVals[current_dev])/(maxVals[current_dev][0]-minVals[current_dev])) > .2):
					xcorr_pb_act[current_dev]['pb'].append(float(pwr_last/maxVals[current_dev][0]))
					xcorr_pb_act[current_dev]['blink'].append(float(float(mot_last)/maxVals[current_dev][1]))
					xcorr_pb_act[current_dev]['pb'].append(float(pwr/maxVals[current_dev][0]))
					xcorr_pb_act[current_dev]['blink'].append(float(float(mot)/maxVals[current_dev][1]))

			pwr_last = pwr
			mot_last = mot
			# else:
			# 	#xcorr_pb_act[current_dev]['pb'].append(float(pwr/maxVals[current_dev][0]))
			# 	xcorr_pb_act[current_dev]['pb'].append(0)
			# 	xcorr_pb_act[current_dev]['blink'].append(0)

		# Inter-device correlation
		for device in interdev_pb:
			sys.stdout.write(names[device] + '\t')
			for new_device in interdev_pb:
				if device != new_device:
					common_times = 0
					dev_items = []
					new_items = []
					p_tot = 0
					p_dev = 0
					p_new = 0
					p_both = 0
					onThold = .25
					for timestamp in sorted(interdev_pb[device]):
						p_tot += 1
						if interdev_pb[device][timestamp] > onThold:
							p_dev += 1
						if timestamp in interdev_pb[new_device]:
							common_times += 1
							if interdev_pb[new_device][timestamp] > onThold:
								p_new += 1
							if interdev_pb[device][timestamp] > onThold and interdev_pb[new_device][timestamp] > onThold:
								p_both += 1
							dev_items.append(interdev_pb[device][timestamp])
							new_items.append(interdev_pb[new_device][timestamp])
						# if names[new_device] == 'Television' and names[device] == 'Xbox One':
						# 	print(str(timestamp) + ' ' + str(interdev_pb[device][timestamp] > onThold) + ' ' + str(interdev_pb[new_device][timestamp] > onThold))
					if len(dev_items) > 1 and len(new_items) > 1 and max(dev_items) > 0 and max(new_items) > 0:
						xcorr = round(numpy.corrcoef(dev_items, new_items)[0][1],2)
					else:
						xcorr = 0

					if p_tot > 0:
						pNew = float(p_new)/p_tot
					else:
						pNew = 0
					if p_dev > 0:
						pNewGivenDevRaw = round(float(p_both)/p_dev,2)
					else:
						pNewGivenDevRaw = 0

					sys.stdout.write(names[new_device] + '\t' + str(len(interdev_pb[device])) + '\t' + str(xcorr) + '\t' + str(p_dev) + '\t' + str(p_new) + '\t' + str(p_both) + '\t' + str(pNewGivenDevRaw) + '\n\t\t')
					if(save_to_final):
						aws_c.execute('insert into dat_dev_corr (testMAC, activeMAC, location, room, crossCorr, pOcc) values (' \
							'\'' + str(new_device) + '\', \'' + str(device) + '\', ' + str(loc) + ', \'' + str(room) + '\', ' + \
							str(xcorr) + ', ' + str(pNewGivenDevRaw) + ');')
						aws_db.commit()
			print('')


		current_dev = 0
		ts_last = new_pb_data[0][2] - timedelta(seconds=1)
		pwr_last = 0
		mot_last = 0
		pOccGivenPow = {}
		for dev, name, ts, pwr, mot, timeDiff in new_pb_data:
			if dev != current_dev:
				# Flush old data
				if(current_dev != 0):
					print_blink(ts_last, pwr_last, mot_last, time_last)


				current_dev = dev
				ts_last = new_pb_data[0][2] - timedelta(seconds=1)
				pwr_last = 0
				mot_last = 0
				time_last = 0

				# Conditional prob calc - normalizing for occupancy
				try:
					pOcc = float(dep_pb[current_dev]['po'])/dep_pb[current_dev]['tot']
					pOccGivenPowRaw = float(dep_pb[current_dev]['pop'])/dep_pb[current_dev]['pp']
				except:
					pOcc = 0
					pOccGivenPowRaw = 0

				if(pOccGivenPowRaw == 0):
					slope = 0
					yint = 0
				elif(pOccGivenPowRaw > pOcc):
					slope = 1/(1 - pOcc)
					yint = pOcc/(pOcc-1)
				else:
					slope = 1/pOcc
					yint = -1

				if(len(xcorr_pb_act[current_dev]['pb']) > 1 and max(xcorr_pb[current_dev]['blink']) > 0 and max(xcorr_pb[current_dev]['pb']) > 0):
					crossCorr = round(numpy.corrcoef(xcorr_pb[current_dev]['blink'], xcorr_pb[current_dev]['pb'])[0][1],2)
				else:
					crossCorr = 0
				if(len(xcorr_pb_act[current_dev]['pb']) > 1 and max(xcorr_pb_act[current_dev]['blink']) > 0 and max(xcorr_pb_act[current_dev]['pb']) > 0):
					actCrossCorr = round(numpy.corrcoef(xcorr_pb_act[current_dev]['blink'], xcorr_pb_act[current_dev]['pb'])[0][1],2)
				else:
					actCrossCorr = 0
				pOccGivenPow[current_dev] = round(slope * pOccGivenPowRaw + yint, 2)

				pb_out.write('\n\n\"' + str(name) + ': Cross Correlation = ' + str(crossCorr) + ', P(o|a) = ' + str(pOccGivenPow[current_dev]) + '\"\n')
				total_data.append([dev, name, loc, room, crossCorr, pOccGivenPow[current_dev]])
				if(save_to_final):
					aws_c.execute('insert into dat_occ_corr (deviceMAC, deviceName, location, room, crossCorr, pOcc) values (' \
							'\'' + str(dev) + '\', \'' + str(name.replace('\'', '')) + '\', ' + str(loc) + ', \'' + str(room) + '\', ' + \
							str(crossCorr) + ', ' + str(pOccGivenPow[current_dev]) + ');')
					aws_db.commit()

			print_blink(ts_last, pwr_last, mot_last, time_last)
			if (((ts-ts_last).days * 86400) + (ts - ts_last).seconds) > 3600:
				print_blink(ts_last + timedelta(seconds=1), 0, mot_last, time_last)
				print_blink(ts - timedelta(seconds=1), 0, mot, timeDiff)
			
			ts_last = ts
			pwr_last = pwr
			mot_last = mot
			time_last = timeDiff

		# Last data
		print_blink(ts_last, pwr_last, mot_last, time_last)

		for devMAC in dep_pb:
			if len(idleP[devMAC]) == 0:
				idleP[devMAC].append(0)
			print(names[devMAC] + ' idleP: ' + str(round(sum(idleP[devMAC])/len(idleP[devMAC]),2)))
			print(names[devMAC] + ' P(active): ' + str(round(float(dep_pb[devMAC]['pp'])/dep_pb[devMAC]['tot'],2)))
			print(names[devMAC] + ' P(o|p): ' + str(pOccGivenPow[devMAC]))
			if pOccGivenPow[devMAC] > 0.5:
				idle_savings_potential['.5'] += round(365 * 24 * float(sum(idleP[devMAC]))/len(idleP[devMAC]) * (1 - float(dep_pb[devMAC]['pp'])/dep_pb[devMAC]['tot']) / 1000, 2)
			if pOccGivenPow[devMAC] > 0.75:
				idle_savings_potential['.75'] += round(365 * 24 * float(sum(idleP[devMAC]))/len(idleP[devMAC]) * (1 - float(dep_pb[devMAC]['pp'])/dep_pb[devMAC]['tot']) / 1000, 2)

		pb_out.close()

		# Create .plt file and fill
		plt = open(runString + '.plt', 'w')
		plt.write('set terminal postscript enhanced eps solid color font "Helvetica,14" size 8.5in,11in\n')
		#plt.write('set terminal postscript enhanced eps solid color font "Helvetica,14" size 8.5in,3.4in\n')
		plt.write('set output \"' + runString + '.eps\"\n')

		plt.write('set xdata time\n')
		plt.write('set key outside above\n')
		plt.write('set timefmt \"\\\"%Y-%m-%d %H:%M:%S\\\"\"\n')
		plt.write('set format x \"%m-%d\\n%H:%M\"\n\n')

		plt.write('set ytics .2\n\n')

		#plt.write('plot for [IDX=0:' + str(plot_count) + '] \'blink.dat\' i IDX u 1:2 w lines axes x1y2 title columnheader(1), \\\n')
		#plt.write('\tfor[IDX=0:' + str(pb_count) + '] \'pb.dat\' i IDX u 1:2 w lines axes x1y1 title columnheader(1)\n')

		plt.write('set multiplot layout ' + str(pb_count) + ', 1\n\n')

		for i in range(0, pb_count):
			plt.write('plot \'pb_' + runString + '.dat\' i ' + str(i) + ' u 1:2 w lines title columnheader(1), \\\n')
			plt.write('\t\'\' i ' + str(0) + ' u 1:3 w lines title \'Blink\'\n')
			#plt.write('\t\'\' i ' + str(i) + ' u 1:4 w lines title \'Time\'\n\n')

		plt.write('unset multiplot\n')

		plt.close()

		# Generate plot and convert to PDF
		gnuplot(runString + '.plt')
		epstopdf(runString + '.eps')

		# Remove temporary file
		os.remove(runString + '.eps')

		# Move data to saveDir
		mv('pb_' + runString + '.dat', qu_saveDir)
		#mv('blink.dat', qu_saveDir)
		mv(runString + '.plt', qu_saveDir)
		mv(runString + '.pdf', qu_saveDir)

		# Show plot file
		# img = subprocess.Popen(['open', qu_saveDir + '/' + runString + '.pdf'])
		# img.wait()
		files_to_open.append(qu_saveDir + '/' + runString + '.pdf')

		print_time()

	print('\nSavings potential, thold = 0.5: ' + str(idle_savings_potential['.5']) + ' kWh ($' + str(round(idle_savings_potential['.5'] * .12,2)) + ') per year')
	print('Savings potential: ' + str(idle_savings_potential['.75']) + ' kWh ($' + str(round(idle_savings_potential['.75'] * .12,2)) + ') per year\n')

	for file in files_to_open:
		img = subprocess.Popen(['open', file])
		img.wait()

	for dev, name, loc, room, crossCorr, pOccGivenPow in total_data:
		print(dev + '\t' + str(crossCorr) + '\t' + str(pOccGivenPow) + '\t' + str(loc) + '\t' + room + '\t' + name)






####################################################################
#
# This section is for occ (the digested results of occupancy)
#
####################################################################

elif(config['type'] == 'occ'):

	aws_c.execute('select deviceType, min(crossCorr) as minCrossCorr, ' \
		'(select avg(crossCorr) from mr_dat_occ_corr where deviceType=ttop.deviceType and crossCorr<=' \
			'(select avg(crossCorr) from mr_dat_occ_corr where deviceType=ttop.deviceType)) as t1CrossCorr, ' \
		'avg(crossCorr) as meanCrossCorr, ' \
		'(select avg(crossCorr) from mr_dat_occ_corr where deviceType=ttop.deviceType and crossCorr>=' \
			'(select avg(crossCorr) from mr_dat_occ_corr where deviceType=ttop.deviceType)) as t3CrossCorr, ' \
		'max(crossCorr) as maxCrossCorr, ' \
		'min(pOcc) as minPOcc, ' \
		'(select avg(pOcc) from mr_dat_occ_corr where deviceType=ttop.deviceType and pOcc<=' \
			'(select avg(pOcc) from mr_dat_occ_corr where deviceType=ttop.deviceType)) as t1POcc, ' \
		'avg(pOcc) as meanPOcc, ' \
		'(select avg(pOcc) from mr_dat_occ_corr where deviceType=ttop.deviceType and pOcc>=' \
			'(select avg(pOcc) from mr_dat_occ_corr where deviceType=ttop.deviceType)) as t3POcc, ' \
		'max(pOcc) as maxPOcc ' \
		'from mr_dat_occ_corr ttop ' \
		'group by deviceType ' \
		'order by avg(pOcc) asc;')
	xCorr_data = aws_c.fetchall()

	xCorr_out = open('xcorr.dat', 'w')

	numTypes = 0
	for idx, data in enumerate(xCorr_data):
		printStr = str(idx+1) + '\t'
		for datum in data:
			if is_number(datum):
				printStr += str(datum) + '\t'
			else:
				printStr += '\"' + str(datum) + '\"\t'
		printStr += '0.5'
		xCorr_out.write(printStr + '\n')
		numTypes = idx+1

	xCorr_out.close()

	xCorr_plt = open('xcorr.plt', 'w')

	xCorr_plt.write('set terminal postscript enhanced eps solid color font "Helvetica,14" size 7in,2.7in\n')
	xCorr_plt.write('set output \"xcorr.eps\"\n\n')

	xCorr_plt.write('unset key\n\n')

	xCorr_plt.write('unset xtics\n')
	xCorr_plt.write('set yrange [:1.05]\n')
	xCorr_plt.write('set rmargin 3\n\n')

	xCorr_plt.write('set xrange [0:' + str(numTypes+1) + ']\n\n')

	xCorr_plt.write('set multiplot layout 2,1\n\n')

	xCorr_plt.write('set size 1,0.43\n')
	xCorr_plt.write('set origin 0,0.55\n\n')

	xCorr_plt.write('set ylabel \"P(occupancy | power)\"\n\n')

	xCorr_plt.write('plot \"xcorr.dat\" using 1:9:8:12:11:13:xticlabels(2) with candlesticks lw 1.5 fc rgb "#ac0a0f" whiskerbars, \\\n' \
		'\t\"\" using 1:10:10:10:10:13 with candlesticks lt -1 lw 1.5\n\n')

	xCorr_plt.write('set bmargin 6\n')
	xCorr_plt.write('set ylabel \"\" offset 1,-1 font \", 12\"\n')
	xCorr_plt.write('set xtics rotate by 45 right font \", 10\"\n\n')

	xCorr_plt.write('set size 1,0.58\n')
	xCorr_plt.write('set origin 0,0\n\n')

	xCorr_plt.write('set xrange [0:' + str(numTypes+1) + ']\n\n')

	xCorr_plt.write('set ylabel \"Cross-correlation\\nOccupancy with Power\"\n\n')

	xCorr_plt.write('plot \"xcorr.dat\" using 1:4:3:7:6:13:xticlabels(2) with candlesticks lw 1.5 fc rgb "#ac0a0f" whiskerbars, \\\n' \
		'\t\"\" using 1:5:5:5:5:13 with candlesticks lt -1 lw 1.5\n\n')

	xCorr_plt.write('unset multiplot\n\n')

	xCorr_plt.close()

	gnuplot('xcorr.plt')
	epstopdf('xcorr.eps')
	os.remove('xcorr.eps')

	mv('xcorr.dat', qu_saveDir)
	mv('xcorr.plt', qu_saveDir)
	mv('xcorr.pdf', qu_saveDir)

	img = subprocess.Popen(['open', qu_saveDir + '/xcorr.pdf'])
	img.wait()












