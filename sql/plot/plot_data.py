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

query_startDay = datetime.utcnow().strftime('%Y_%m_%d_')

master_saveDir = ".savetest/" + str(query_startDay)


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

	if(config['tag'] == ''):
		query_startTime = datetime.utcnow().strftime('%H_%M_%S')
		qu_saveDir = master_saveDir + str(query_startTime) + '/'
	elif(config['tag'] == 'info'):
		qu_saveDir = master_saveDir + 'l'
		for loc in config['locations']:
			qu_saveDir += loc
		qu_saveDir += '_' + config['type']
		if(config['type'] != 'power'):
			qu_saveDir += '_s' + datetime.strptime(config['start'], "%Y-%m-%d %H:%M:%S").strftime('%m%d')
			qu_saveDir += '_e' + datetime.strptime(config['end'], "%Y-%m-%d %H:%M:%S").strftime('%m%d')
		qu_saveDir += '/'
		if(os.path.isdir(qu_saveDir)):
			#print("Error: cant save to this folder, experiment already exists. Changing to time tagging")
			#error = True
			config['tag'] = ''
	else:
		qu_saveDir = master_saveDir + config['tag'] + '/'

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
		aws_c.execute('select \'PowerBlade\', deviceMAC, location, deviceName from active_powerblades where deviceMAC in ' + dev_powerblade + ';')
		devNames.extend(aws_c.fetchall())
	if(query_blees):
		aws_c.execute('select concat(deviceType, \'\\t\'), deviceMAC, location, deviceName from active_lights where deviceMAC in ' + dev_blees + ';')
		devNames.extend(aws_c.fetchall())
	if(query_ligeiro):
		aws_c.execute('select concat(deviceType, \'\\t\'), deviceMAC, location, deviceName from active_lights where deviceMAC in ' + dev_ligeiro + ';')
		devNames.extend(aws_c.fetchall())
	if(query_blink):
		aws_c.execute('select \'Blink\\t\', deviceMAC, location, room from active_blinks where deviceMAC in ' + dev_blink + ';')
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
	else:
		print("\nQuerying " + config['type'] + " from the following devices")
	dev_print()

	print("\nFrom the following locations")
	for loc in sorted(config['locations']):
		print("\tLocation " + loc)

	print("\nOver the following time period:")
	config['startDay'] = config['start'][0:10]
	config['endDay'] = config['end'][0:10]
	if(config['type'] == 'plot'):
		print("From\t" + config['start'])
		print("To\t" + config['end'])
	else:
		print("From\t" + config['startDay'])
		print("To\t" + config['endDay'])

	if(config['type'] == 'plot'):
		if(config['sum']):
			print("\nWith sum of power also plotted")
		else:
			print("\nWithout sum of power plotted")

	if(config['tag'] != ''):
		print('\nTag for save file: ' + config['tag'])

print_parameters()

print("\nTo confirm, push enter. To modify:")
print("\t'type [plot, energy, power]'")
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
		if(confirm_list[1] == 'plot' or confirm_list[1] == 'energy' or confirm_list[1] == 'power'):
			config['type'] = confirm_list[1]
			changes = True
		else:
			print("Usage is type [plot, energy, power]")
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

		aws_c.execute('select lower(deviceMAC) from active_devices where location=' + confirm_list[devOffset] + ';')
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
	elif(confirm_list[0] == 'tag'):
		if(len(confirm_list) != 2):
			error = True
			print("Usage is 'tag [tag]'")
		elif(confirm_list[1] == '' or confirm_list[1] == 'clear'):
			config['tag'] = ''
			changes = True
		elif(confirm_list[1] == 'info'):
			config['tag'] = 'info'
			changes = True
		elif(os.path.isdir(master_saveDir + confirm_list[1])):
			error = True
			print("Error: save directory already exists")
		else:
			config['tag'] = confirm_list[1]
			changes = True
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


print("\nRunning queries...\n")

check_tag()

if not os.path.isdir('.savetest'):
	mkdir('.savetest/')

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
		'select date(timestamp) as dayst, deviceMAC, (max(energy) - min(energy)) as dayEnergy from dat_powerblade force index (devTimeEnergy) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and deviceMAC in ' + dev_powerblade + ' and energy!=999999.99 group by deviceMAC, dayst;')
	# Max power - maximum power per device over the time period
	aws_c.execute('alter view maxPower_pb as ' \
		'select deviceMAC, max(power) as maxPower from dat_powerblade force index (devTimePower) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and power != 120.13 ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;')
	aws_c.execute('alter view avgPower_pb as ' \
		'select deviceMAC, avg(power) as avgPower from dat_powerblade t1 force index(devTimePower) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and power>(select 0.1*maxPower from maxPower_pb t2 where t1.deviceMAC=t2.deviceMAC) ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;')

	day_en_str = ''
	avg_pwr_str = ''
	# Step 0.5: Handle light data
	if(query_blees):
		aws_c.execute('alter view energy_blees as ' \
			'select round(unix_timestamp(timestamp)/(5*60)) as timekey, deviceMAC, date(timestamp) as dayst, ' \
			'case when lux>(select avgLux from avg_lux t2 where t1.deviceMAC=t2.deviceMAC) then ' \
			'(select power*5/60 from active_lights t3 where t1.deviceMAC=t3.deviceMAC) else 0 end as \'onoff\' ' \
			'from dat_blees t1 force index (devLux) ' \
			'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
			'and deviceMAC in ' + dev_blees + ' group by deviceMAC, timekey;')
		aws_c.execute('alter view day_energy_blees as ' \
			'select dayst, deviceMAC, sum(onoff) as dayEnergy from ' \
			'energy_blees group by deviceMAC, dayst;')
		day_en_str += ' union select * from day_energy_blees'
		avg_pwr_str += ' union (select deviceMAC, power from active_lights where deviceMAC in ' + dev_blees + ')'
	if(query_ligeiro):
		aws_c.execute('alter view energy_ligeiro as ' \
			'select round(unix_timestamp(timestamp)/(5*60)) as timekey, deviceMAC, date(timestamp) as dayst, ' \
			'case when (1+max(count)-min(count)) >= 1 then '\
			'(select power*5/60 from active_lights t2 where t1.deviceMAC=t2.deviceMAC) else 0 end as \'onoff\' ' \
			'from dat_ligeiro t1 ' \
			'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
			'and deviceMAC in ' + dev_ligeiro + ' group by deviceMAC, timekey;')
		aws_c.execute('alter view day_energy_ligeiro as ' \
			'select dayst, deviceMAC, sum(onoff) as dayEnergy from ' \
			'energy_ligeiro group by deviceMAC, dayst;')
		day_en_str += ' union select * from day_energy_ligeiro'
		avg_pwr_str += ' union (select deviceMAC, power from active_lights where deviceMAC in ' + dev_ligeiro + ')'

	aws_c.execute('alter view day_energy as select * from day_energy_pb' + day_en_str + ';')
	aws_c.execute('alter view avg_power as select * from avgPower_pb' + avg_pwr_str + ';')

	# Step 1: Unified query for energy and power
	print("Running data query...\n")
	aws_c.execute('select t1.deviceMAC, t1.deviceName, t2.avgEnergy, t2.stdEnergy, t2.totEnergy, t3.avgPower from ' \
		'active_devices t1 ' \
		'join (select deviceMAC, avg(dayEnergy) as avgEnergy, stddev(dayEnergy) as stdEnergy, sum(dayEnergy) as totEnergy ' \
		'from day_energy group by deviceMAC) t2 ' \
		'on t1.deviceMAC=t2.deviceMAC ' \
		'join avg_power t3 ' \
		'on t1.deviceMAC=t3.deviceMAC ' \
		'order by t2.avgEnergy;')
	expData = aws_c.fetchall()
	# aws_c.execute('select t1.deviceMAC, t1.deviceName, t2.avgEnergy, t2.stdEnergy, t2.totEnergy, 0 from ' \

	# Step 2: Ground Truth
	aws_c.execute('select avg(energy), count(*) from most_recent_gnd_truth where location in ' + loc_list + ' and ' \
		'date(dayst)>=\'' + config['startDay'] + '\' and date(dayst)<=\'' + config['endDay'] + '\';')
	gndTruth = aws_c.fetchall()[0]

	duration_days = duration / 86400
	missing_days = duration_days - gndTruth[1]

	outfile_pb = open('energy_pb.dat', 'w')
	outfile_li = open('energy_li.dat', 'w')
	outfile = open ('tot_energy.dat', 'w')

	labelstr = ""
	energyCutoff = 1000

	total_measured_energy = 0

	# Energy Printout
	for idx, (mac, name, dayEnergy, var, totEnergy, power) in enumerate(expData):
		total_measured_energy += dayEnergy
		print(str(idx) + " " + str(mac) + " \"" + str(name) + "\" " + str(dayEnergy) + " " + str(var) + " " + str(totEnergy) + " " + str(power))
		outfile.write(str(idx) + "\t" + str(mac) + "\t\"" + str(name) + "\"\t" + str(dayEnergy) + "\t" + str(var) + "\t" + str(totEnergy) + "\t" + str(power) + "\n")
		if(mac[6:8] == '70'):
			outfile_pb.write(str(idx) + "\t" + str(mac) + "\t\"" + str(name) + "\"\t" + str(dayEnergy) + "\t" + str(var) + "\t" + str(totEnergy) + "\t" + str(power) + "\n")
		else:
			outfile_li.write(str(idx) + "\t" + str(mac) + "\t\"" + str(name) + "\"\t" + str(dayEnergy) + "\t" + str(var) + "\t" + str(totEnergy) + "\t" + str(power) + "\n")
		if(dayEnergy > energyCutoff):
			labelstr += 'set label at ' + str(idx) + ', ' + str(energyCutoff * 1.1) + ' \"' + str(int(dayEnergy)) + '\" center font \", 8\"\n'

	outfile.write('# total measured energy: ' + str(total_measured_energy) + '\n')
	outfile.write('# gnd truth: ' + str(gndTruth[0]) + '\n')
	outfile.write('# missing days: ' + str(missing_days) + '\n')

	outfile_pb.close()
	outfile_li.close()

	outfile = open('breakdown.plt', 'w')
	outfile.write('set terminal postscript enhanced eps solid color font \"Helvetica,14\" size 8in,2.0in\n')
	outfile.write('set output \"breakdown.eps\"\n\n')

	outfile.write('# General setup\n\n')
	outfile.write('unset key\n')
	outfile.write('set boxwidth 0.5\n')
	outfile.write('set style fill solid 1.00 border lt -1\n')
	outfile.write('\n')

	outfile.write('set multiplot layout 2,1\n\n')

	outfile.write('# Top plot (energy)\n\n')
	outfile.write('unset xtics\n')
	outfile.write('set lmargin 10\n')
	outfile.write('set ylabel \"Average Daily\\nEnergy (Wh)\" offset 1,0 font \", 12\"\n')
	outfile.write('set yrange[0:' + str(energyCutoff) + ']\n')
	outfile.write('set size 1,0.38\n')
	outfile.write('set origin 0,0.60\n')
	outfile.write('set key top left font \", 12\"\n')
	outfile.write('\n')

	outfile.write(labelstr)

	outfile.write('plot \"energy_li.dat\" using 1:4 with boxes fc rgb \"#4b97c8\" title \"BLEES/Ligeiro\", \\\n'
		'\t\"energy_pb.dat\" using 1:4 with boxes fc rgb \"#ac0a0f\" title \"PowerBlade\"\n\n')

	outfile.write('# Bottom plot (power)\n\n')
	outfile.write('unset label\n')
	outfile.write('unset key\n')
	outfile.write('set logscale y\n')
	outfile.write('set bmargin 5.5\n')
	outfile.write('set xtics  rotate by 45 right font \", 10\"\n')
	outfile.write('set size 1,0.66\n')
	outfile.write('set origin 0,0\n')
	outfile.write('set yrange[1:5000]\n')
	outfile.write('set ylabel \"Average Active\\nPower (w)\" offset 1,-1 font \", 12\"\n')

	outfile.write('plot \"energy_li.dat\" using 1:7:xticlabels(3) with boxes fc rgb \"#4b97c8\" title \"BLEES/Ligeiro\", \\\n'
		'\t\"energy_pb.dat\" using 1:7:xticlabels(3) with boxes fc rgb \"#ac0a0f\"\n')

	outfile.write('unset multiplot\n')

	outfile.close()

	# Clean up anything left from last time (in the case of errors)
	# if(os.path.exists('breakdown.eps')):
	# 	os.remove('breakdown.eps')
	# if(os.path.exists('breakdown.pdf')):
	# 	os.remove('breakdown.pdf')

	# Generate plot and convert to PDF
	gnuplot('breakdown.plt')
	epstopdf('breakdown.eps')

	# Show plot file
	# img = subprocess.Popen(['open', 'datfile.pdf'])
	# img.wait()

	# Remove temporary file
	os.remove('breakdown.eps')

	# Move data to saveDir
	mv('tot_energy.dat', qu_saveDir)
	mv('energy_pb.dat', qu_saveDir)
	mv('energy_li.dat', qu_saveDir)
	mv('breakdown.plt', qu_saveDir)
	mv('breakdown.pdf', qu_saveDir)

	printEnergy(expData, total_measured_energy, gndTruth[0], 'energy')

	if gndTruth[0] != 0 and gndTruth[0] != None:
		gnuplot('energy_pwrCDF.plt')
		epstopdf('energy_pwrCDF.eps')

		os.remove('energy_pwrCDF.eps')

		mv('energy_pwrCDF.dat', qu_saveDir)
		mv('energy_pwrCDF.plt', qu_saveDir)
		mv('energy_pwrCDF.pdf', qu_saveDir)


####################################################################
#
# This section is for the power option (temporary)
#
####################################################################

elif(config['type'] == 'power'):

	print("Running power...\n")

	print("Acquiring max power...\n")

	# # Max power - maximum power per device over the time period
	# aws_c.execute('insert into perm_maxPower_pb (deviceMAC, maxPower) ' \
	# 	'select deviceMAC, max(power) as maxPower from dat_powerblade force index (devTimePower) ' \
	# 	'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
	# 	'and power != 120.13 ' \
	# 	'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;')

	# print("Acquiring avg power...\n")

	# aws_c.execute('insert into perm_avgPower_pb (deviceMAC, avgPower) ' \
	# 	'select deviceMAC, avg(power) as avgPower from dat_powerblade t1 force index(devDevPower) ' \
	# 	'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
	# 	'and power>(select 0.1*maxPower from mr_maxPower_pb t2 where t1.deviceMAC=t2.deviceMAC) ' \
	# 	'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;')

	aws_c.execute('alter view maxPower_pb as ' \
		'select deviceMAC, max(power) as maxPower from dat_powerblade force index (devTimePower) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and power != 120.13 ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;')
	aws_c.execute('alter view avgPower_pb as ' \
		'select deviceMAC, avg(power) as avgPower from dat_powerblade t1 force index(devTimePower) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and power>(select 0.1*maxPower from maxPower_pb t2 where t1.deviceMAC=t2.deviceMAC) ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;')

	aws_c.execute('select t1.deviceMAC, t1.deviceName, t2.avgPower from ' \
		'active_devices t1 ' \
		'join avgPower_pb t2 ' \
		'on t1.deviceMAC=t2.deviceMAC ' \
		'order by t1.deviceMAC;')
	expData = aws_c.fetchall()


	outfile_pwr = open('tot_power.dat', 'w')

	pwrData = sorted(expData, key=lambda dev: dev[2])

	for idx, (mac, name, avgPower) in enumerate(pwrData):
		print(str(idx) + " " + str(mac) + " \"" + str(name) + "\" " + str(avgPower))
		outfile_pwr.write(str(idx) + "\t" + str(mac) + "\t\"" + str(name) + "\"\t" + str(avgPower) + "\n")

	outfile_pwr.close()

	breakdown([['tot_power.dat', '#4b97c8', 'BLEES/Ligeiro']], True, 'tot_power')
	
	gnuplot('tot_power.plt')
	epstopdf('tot_power.eps')

	os.remove('tot_power.eps')

	mv('tot_power.dat', qu_saveDir)
	mv('tot_power.plt', qu_saveDir)
	mv('tot_power.pdf', qu_saveDir)












