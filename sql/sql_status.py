#!/usr/bin/env python

import mylogin
import MySQLdb
import yagmail
from datetime import datetime, timedelta
import sys
from os.path import expanduser

STATUS_OK = "<font color=\"green\"><b>OK!</b></font>"
STATUS_DOWN = "<font color=\"orange\"><b>Down</b></font>"
STATUS_NOT_FOUND = "</td><td></td><td><font color=\"red\"><b>Not Found</b></font>"

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

first_header = 1
def print_header(col1, col2):
	global first_header
	if(first_header == 1):
		email_body.append("<table style=\"width:80%\">")
		first_header = 0
	else:
		email_body.append("<tr><td colspan=\"5\">&nbsp</td></tr>")
	email_body.append("<tr><td><b>" + col1 + "</b></td><td><b>" + col2 + \
		"</b></td><td><b>Last Seen</b></td><td><b>Offtime</b></td>" \
		"<td><b>Status</b></td><td><b>Count</b></td></tr>")

def print_row(name, specifier, time_now, maxTime, status, count):
	email_body.append("<tr><td>" + str(name) + "</td><td>" + str(specifier) + "</td><td>" + str(maxTime) + \
		"</td><td>" + str(chop_microseconds(time_now - maxTime)) + "</td><td>" + status + "</td><td>" + str(count) + "</td></tr>")

def print_error(name, specifier):
	email_body.append("<tr><td>" + str(name) + "</td><td>" + str(specifier) + "</td><td>" + STATUS_NOT_FOUND + "</td></tr>")

def print_list(status_list, col1, col2):
	if(~longrun):
		return 0	# Not supposed to happen

	print_header(col1, col2)

	for devname in status_list:
		this_statuslist = status_list[devname]
		print_row(devname, this_statuslist[0], this_statuslist[1], this_statuslist[2], this_statuslist[3], this_statuslist[4])

def check_list(activelist, timeslist, yest_statuslist, today_statuslist, outfile, col1, col2):
	if(longrun):
		return 0	# Not supposed to happen

	time_now = datetime.utcnow()

	print_header(col1, col2)

	new_statuss = 0

	for devname, specifier in activelist:	# Specifier is either location or permanent
		if(specifier is not None):	# Location actually exists
			try:
				maxTime = [item for item in timeslist if item[0] == devname][0][1]
				if((time_now - maxTime) > timedelta(minutes=15)):	# If it has been more than fifteen minutes for a gateway
					status = STATUS_DOWN
				else:
					status = STATUS_OK

				if(status != STATUS_OK):
					try:
						# Check if this status has happened today, and if so increment count
						today_statuslist[devname][4] += 1
					except:
						# New device/status for today, add new element
						today_statuslist[devname] = [specifier, time_now, maxTime, status, 1]
						try:
							# Check if this status also didnt happen yesterday, in which case it would have already been sent
							yest_statuslist[devname]
						except:
							# status did not happen yesterday or today, OK to send
							new_statuss += 1
							print_row(devname, specifier, time_now, maxTime, status, 1)
			except IndexError:
				print("Error: gateway not found - " + str(device))
				pass
				#if(longrun == 1):
				#	print_error(devname, specifier)

	statuss = open(outfile, 'w')
	for devname in today_statuslist:
		statuss.write(devname)
		for field in today_statuslist[devname]:
			statuss.write(',' + str(field))
		statuss.write('\n')

	return new_statuss

def read_file(status_list, listType, day):
	try:
		infile = open(logpath + listType + '-status-' + day.strftime("%Y-%m-%d") + '.log', 'r')
		for line in infile:
			deviceMAC, specifier, time_status, avgstatusTime, status, count = line.strip('\n').split(',')
			status_list[deviceMAC] = [specifier, time_status, avgstatusTime, status, count]
		infile.close()
	except:
		print("Unknown file")


# Start of execution


# Get the home directory, log path
home = expanduser("~")
logpath = home + '/log/'

# Get database parameters
f = open('/etc/swarm-gateway/powerblade-aws.conf', 'r')
password = 0
for line in f:
	lineList = line.strip('\n').split(' = ')
	if(lineList[0] == 'sql_pw'):
		password = lineList[1]
f.close()

if(password == 0):
	print("Unable to find password")
	exit()

# Read in the yesterday and today files
# If this is a long run the entire yesterday file is emailed
# If this is a short run the status is only emailed if not in the yesterday file
today = datetime.now()
yesterday = today - timedelta(1)

pb_yest_list = {}
read_file(pb_yest_list, 'powerblade', yesterday)

gw_yest_list = {}
read_file(gw_yest_list, 'gateway', yesterday)

pb_today_list = {}
read_file(pb_today_list, 'powerblade', today)

gw_today_list = {}
read_file(gw_today_list, 'gateway', today)


longrun = True
if len(sys.argv) > 1:
	if(sys.argv[1] == 'short'):
		print("Running PowerBlade Deployment Status Script - short check")
		email_body = ['<!DOCTYPE html><html><body><h2> PowerBlade Deployment Status Email - New status Found</h2>']
		longrun = False
	elif(sys.argv[1] == 'daily'):
		print("Running PowerBlade Deployment Status Script - daily run")
		email_body = ['<!DOCTYPE html><html><body><h2> PowerBlade Deployment Status Email - Full Update</h2>']
	else:
		print("Unknown parameter")
		# TODO: send status email
		exit()
else:
	print("Need to run with either \'short\' or \'daily\'")
	exit()

email_body.append('<style>\n\t.bottom-three {\n\t\tmargin-bottom: 3cm;\n\t}\n</style>')
email_body.append('<p class=\"bottom-three\">Script start time: ' + str(datetime.utcnow()) + '</p>')
email_end = '</table></body></html>'

# If this is a daily run the database is not connected, instead only the yesterday file is sent
# If a shortrun, the database is connected and new statuss are found
if(longrun):
	print_list(gw_yest_list, "GatewayMAC", "Location")
	print_list(pb_yest_list, "DeviceMAC", "Permanent")
	print("Sending results via email")
	email_body.append(email_end)
	yagmail.SMTP('powerblade.lab11@gmail.com', password).send('powerblade@umich.edu', 'Re: PowerBlade Deployment Status Email', email_body)
else:
	# Set up connection
	aws_login = mylogin.get_login_info('aws')
	aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
	aws_c = aws_db.cursor()

	# Query for list of gateways that should be active (inf_gw_lookup where now is between dates)
	aws_c.execute('select gatewayMAC, location from ' \
		'(select t1.* from inf_gw_lookup t1 where t1.id = ' \
		'(select max(t2.id) from inf_gw_lookup t2 where t1.gatewayMAC=t2.gatewayMAC)) t1 ' \
		'where ((utc_timestamp between startTime and endTime) or ' \
		'(utc_timestamp > startTime and endTime is null) or ' \
		'(utc_timestamp < endTime and startTime is null)) order by GatewayMAC desc;')
	# aws_c.execute('select gatewayMAC, location from inf_gw_lookup where ((utc_timestamp between startTime and ' \
	# 	'endTime) or (utc_timestamp > startTime and endTime is null) or (utc_timestamp < endTime and startTime is null)) order by GatewayMAC desc')
	gateway_active = aws_c.fetchall()

	# Query for list of PowerBlades that should be active (inf_pb_lookup where now is between dates)
	aws_c.execute('select deviceMAC, permanent from ' \
		'(select t1.* from inf_pb_lookup t1 where t1.id = ' \
		'(select max(t2.id) from inf_pb_lookup t2 where t1.deviceMAC=t2.deviceMAC)) t1 ' \
		'where ((utc_timestamp between startTime and endTime) or ' \
		'(utc_timestamp > startTime and endTime is null) or ' \
		'(utc_timestamp < endTime and startTime is null)) order by deviceMAC desc;')
	#aws_c.execute('select deviceMAC, permanent from inf_pb_lookup where utc_timestamp between startTime and endTime')
	pb_active = aws_c.fetchall()

	# Query for most recent time seeing each gateway
	aws_c.execute('select t1.gatewaymac, (select t2.timestamp from dat_powerblade t2 where t2.id=max(t1.id)) as maxTime ' \
		'from dat_powerblade t1 group by t1.gatewaymac')
	gateway_times = aws_c.fetchall()

	# Query for most recent time seeing each PowerBlade
	aws_c.execute('select t1.deviceMAC, (select t2.timestamp from dat_powerblade t2 where t2.id=max(t1.id)) as maxTime ' \
		'from dat_powerblade t1 group by t1.deviceMAC')
	pb_times = aws_c.fetchall()

	total_statuss = 0

	total_statuss += check_list(gateway_active, gateway_times, gw_yest_list, gw_today_list, logpath + 'gateway-status-' + today.strftime("%Y-%m-%d") + '.log', "GatewayMAC", "Location")
	total_statuss += check_list(pb_active, pb_times, pb_yest_list, pb_today_list, logpath + 'powerblade-status-' + today.strftime("%Y-%m-%d") + '.log', "DeviceMAC", "Permanent")

	email_body.append(email_end)

	if(total_statuss > 0):
		print("Sending results via email")
		yagmail.SMTP('powerblade.lab11@gmail.com', password).send('powerblade@umich.edu', 'Re: PowerBlade Deployment New Device Error', email_body)
	else:
		print("No errors, no email")


