#!/usr/bin/env python

import mylogin
import MySQLdb
import json

import datetime

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
	pass

# Check device list
dev_print = ""

query_powerblade = False
dev_powerblade = ["("]
query_blees = False
dev_blees = ["("]
query_ligeiro = False
dev_ligeiro = ["("]
query_blink = False
dev_blink = ["("]

def dev_print():
	for dev in config['devices']:
		print("\t" + str(dev))

# Confirm parameters

print("\nPowerBlade Deployment Plotting Program")

def print_parameters():

	print("\nPlotting data from the following devices:")
	dev_print()

	print("\nOver the following time period:")
	print("From\t" + config['start'])
	print("To\t" + config['end'])

	if(config['sum']):
		print("\nWith sum of power also plotted")
	else:
		print("\nWithout sum of power plotted")

print_parameters()

print("\nTo confirm, push enter. To modify:")
print("\t'devices: [comma separated 12 or 6 digit macs]' or")
print("\t'location: #'")
print("\t'start yyyy-mm-dd HH:mm:ss' or")
print("\t'end yyyy-mm-dd HH:mm:ss' or")
print("\t'sum [true:false]'")

confirm = raw_input("\nPress enter, or next change: ")

changes = False

connected = False

while(confirm != ""):
	confirm_list = confirm.split(" ")

	error = False

	if(confirm_list[0] == 'devices'):
		pass
	elif(confirm_list[0] == 'location'):
		# Set up connection
		aws_login = mylogin.get_login_info('aws')
		aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
		aws_c = aws_db.cursor()
		connected = True

		aws_c.execute('select deviceMAC from active_powerblades where location=' + confirm_list[1] + ';')
		device_list = aws_c.fetchall()
		print(device_list)
		print(config['devices'])
		config['devices'] = [i[0] for i in device_list]
		#exit()
	elif(confirm_list[0] == 'start' or confirm_list[0] == 'end'):
		try:
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

	confirm = raw_input("\nPress enter, or next change: ")

if(changes):
	if(raw_input("\nSave changes to config file? [y/n]: ") == "y"):
		with open('.plotconfig', 'w') as outfile:
		    json.dump(config, outfile)


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



if(connected == False):
	# Set up connection
	aws_login = mylogin.get_login_info('aws')
	aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
	aws_c = aws_db.cursor()

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









