#!/usr/bin/env python

import mylogin
import MySQLdb
import json

import datetime
import pytch

import os
import sys
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

	query_powerblade = False
	query_blees = False
	query_ligeiro = False
	query_blink = False

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
		aws_c.execute('select \'PowerBlade\', deviceMAC, location, deviceName from most_recent_powerblades where deviceMAC in ' + dev_powerblade + ';')
		devNames.extend(aws_c.fetchall())
	if(query_blees):
		aws_c.execute('select concat(deviceType, \'\\t\'), deviceMAC, location, deviceName from most_recent_lights where deviceMAC in ' + dev_blees + ';')
		devNames.extend(aws_c.fetchall())
	if(query_ligeiro):
		aws_c.execute('select concat(deviceType, \'\\t\'), deviceMAC, location, deviceName from most_recent_lights where deviceMAC in ' + dev_ligeiro + ';')
		devNames.extend(aws_c.fetchall())

	for line in devNames:
		print("\t" + str(line[0]) + "\t" + str(line[1]) + "\tLocation " + str(line[2]) + "\t" + str(line[3]))

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
print("\t'type [plot, energy, light]'")
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
		if(confirm_list[1] == 'plot' or confirm_list[1] == 'energy' or confirm_list[1] == 'light'):
			config['type'] = confirm_list[1]
			changes = True
		else:
			print("Usage is type [plot, energy, light]")
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

		aws_c.execute('select lower(deviceMAC) from most_recent_devices where location=' + confirm_list[devOffset] + ';')
		device_list = aws_c.fetchall()
		devList = [i[0] for i in device_list]

		print(device_list)
		print(devList)

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


print("\nRunning queries...\n")





####################################################################
#
# This section is for the plot option
#
####################################################################

if(config['type'] == 'plot'):

	dStart = datetime.datetime.strptime(config['start'], "%Y-%m-%d %H:%M:%S")
	dEnd = datetime.datetime.strptime(config['end'], "%Y-%m-%d %H:%M:%S")

	duration = (dEnd - dStart).total_seconds()
	downsample = int(duration/10000)

	if(query_powerblade):
		aws_c.execute("select t2.deviceName, t1.timest, t1.avgPower from " \
			"(select round(unix_timestamp(timestamp)/(" + str(downsample) + ")) as timekey, " \
			"deviceMAC, max(timestamp) as timest, avg(power) as avgPower from dat_powerblade force index (devPower) where deviceMAC in " + \
			dev_powerblade + " and timestamp between \"" + str(config['start']) + "\" and \"" + str(config['end']) + "\"" + \
			"group by deviceMAC, timekey) t1 " \
			"join most_recent_powerblades t2 on t1.deviceMAC=t2.deviceMAC " \
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

	if(query_powerblade == False):
		print("Error: At least one PowerBlade required for energy printing")
		exit()

	# Step 0: Alter the views acccording to the specified query paremeters
	# Day energy: maximum energy minus minimum energy for each device for each day
	print("Altering views for energy query...\n")
	aws_c.execute('alter view day_energy_pb as ' \
		'select date(timestamp) as dayst, deviceMAC, (max(energy) - min(energy)) as dayEnergy from dat_powerblade force index (devEnergy) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and deviceMAC in ' + dev_powerblade + ' and energy!=999999.99 group by deviceMAC, dayst;')
	# Max power - maximum power per device over the time period
	aws_c.execute('alter view maxPower_pb as ' \
		'select deviceMAC, max(power) as maxPower from dat_powerblade force index (devPower) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and power != 120.13 ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;')
	aws_c.execute('alter view avgPower_pb as ' \
		'select deviceMAC, avg(power) as avgPower from dat_powerblade t1 force index(devPower) ' \
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
			'(select power*5/60 from most_recent_lights t3 where t1.deviceMAC=t3.deviceMAC) else 0 end as \'onoff\' ' \
			'from dat_blees t1 force index (devLux) ' \
			'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
			'and deviceMAC in ' + dev_blees + ' group by deviceMAC, timekey;')
		aws_c.execute('alter view day_energy_blees as ' \
			'select dayst, deviceMAC, sum(onoff) as dayEnergy from ' \
			'energy_blees group by deviceMAC, dayst;')
		day_en_str += ' union select * from day_energy_blees'
		avg_pwr_str += ' union (select deviceMAC, power from most_recent_lights where deviceMAC in ' + dev_blees + ')'
	if(query_ligeiro):
		aws_c.execute('alter view energy_ligeiro as ' \
			'select round(unix_timestamp(timestamp)/(5*60)) as timekey, deviceMAC, date(timestamp) as dayst, ' \
			'case when (1+max(count)-min(count)) >= 1 then '\
			'(select power*5/60 from most_recent_lights t2 where t1.deviceMAC=t2.deviceMAC) else 0 end as \'onoff\' ' \
			'from dat_ligeiro t1 ' \
			'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
			'and deviceMAC in ' + dev_ligeiro + ' group by deviceMAC, timekey;')
		aws_c.execute('alter view day_energy_ligeiro as ' \
			'select dayst, deviceMAC, sum(onoff) as dayEnergy from ' \
			'energy_ligeiro group by deviceMAC, dayst;')
		day_en_str += ' union select * from day_energy_ligeiro'
		avg_pwr_str += ' union (select deviceMAC, power from most_recent_lights where deviceMAC in ' + dev_ligeiro + ')'

	aws_c.execute('alter view day_energy as select * from day_energy_pb' + day_en_str + ';')
	aws_c.execute('alter view avg_power as select * from avgPower_pb' + avg_pwr_str + ';')

	# Step 1: Unified query for energy and power
	print("Running data query...\n")
	aws_c.execute('select t1.deviceMAC, t1.deviceName, t2.avgEnergy, t2.stdEnergy, t3.avgPower from ' \
		'most_recent_devices t1 ' \
		'join (select deviceMAC, avg(dayEnergy) as avgEnergy, stddev(dayEnergy) as stdEnergy ' \
		'from day_energy group by deviceMAC) t2 ' \
		'on t1.deviceMAC=t2.deviceMAC '
		'join avg_power t3 ' \
		'on t1.deviceMAC=t3.deviceMAC ' \
		'order by t2.avgEnergy;')
	expData = aws_c.fetchall()

	outfile_pb = open('energy_pb.dat', 'w')
	outfile_li = open('energy_li.dat', 'w')

	#'(select * from most_recent_devices where deviceMAC in ' + dev_powerblade + ') t1 ' \

	labelstr = ""
	energyCutoff = 1000

	for idx, (mac, name, energy, var, power) in enumerate(expData):
		print(str(idx) + " " + str(mac) + " \"" + str(name) + "\" " + str(energy) + " " + str(var) + " " + str(power))
		if(mac[6:8] == '70'):
			outfile_pb.write(str(idx) + "\t" + str(mac) + "\t\"" + str(name) + "\"\t" + str(energy) + "\t" + str(var) + "\t" + str(power) + "\n")
		else:
			outfile_li.write(str(idx) + "\t" + str(mac) + "\t\"" + str(name) + "\"\t" + str(energy) + "\t" + str(var) + "\t" + str(power) + "\n")
		if(energy > energyCutoff):
			labelstr += 'set label at ' + str(idx) + ', ' + str(energyCutoff * 1.1) + ' \"' + str(int(energy)) + '\" center font \", 8\"\n'

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

	outfile.write('plot \"energy_li.dat\" using 1:6:xticlabels(3) with boxes fc rgb \"#4b97c8\" title \"BLEES/Ligeiro\", \\\n'
		'\t\"energy_pb.dat\" using 1:6:xticlabels(3) with boxes fc rgb \"#ac0a0f\"\n')

	outfile.write('unset multiplot\n')

	outfile.close()



####################################################################
#
# This section is for the light option (temporary)
#
####################################################################

elif(config['type'] == 'light'):


	print("Running light")

