#!/usr/bin/env python

import mylogin
import MySQLdb
import yagmail
from datetime import datetime, timedelta
import sys
from os.path import expanduser

STATUS_OK = "<font color=\"green\"><b>OK!</b></font>"
STATUS_DOWN = "<font color=\"orange\"><b>Down</b></font>"
STATUS_NOT_FOUND = "<font color=\"red\"><b>Not Found</b></font>"

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

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

first_header = 1
def print_header(col1):
	global first_header
	if(first_header == 1):
		email_body.append("<table style=\"width:80%\">")
		first_header = 0
	else:
		email_body.append("<tr><td colspan=\"5\">&nbsp</td></tr>")
	email_body.append("<tr>" \
		"<td><b>" + col1 + "</b></td>" \
		"<td><b>Location</b></td>" \
		"<td><b>Permanent</b></td>" \
		"<td><b>Last Seen</b></td>" \
		"<td><b>Offtime</b></td>" \
		"<td><b>Status</b></td>" \
		"<td><b>Count</b></td>" \
		"</tr>")

def print_row(name, location, permanent, time_now, maxTime, status, count):
	if(time_now == 0):
		t1 = ""
		t2 = ""
	else:
		t1 = str(maxTime)
		t2 = str(chop_microseconds(time_now - maxTime))
	email_body.append("<tr>" \
		"<td>" + str(name) + "</td>" \
		"<td>" + str(location) + "</td>" \
		"<td>" + str(permanent) + "</td>" \
		"<td>" + t1 + "</td>" \
		"<td>" + t2 + "</td>" \
		"<td>" + status + "</td>" \
		"<td>" + str(count) + "</td>" \
		"</tr>")

#def print_error(name, specifier):
#	email_body.append("<tr><td>" + str(name) + "</td><td>" + str(specifier) + "</td><td>" + STATUS_NOT_FOUND + "</td></tr>")

def print_list(status_list, col1):
	if(longrun == False):
		return 0	# Not supposed to happen

	print_header(col1)

	for devname in status_list:
		this_statuslist = status_list[devname]
		print_row(devname, this_statuslist[0], this_statuslist[1], this_statuslist[2], this_statuslist[3], this_statuslist[4], this_statuslist[5])

def check_list(activelist, timeslist, yest_statuslist, today_statuslist, outfile, col1, timeout):
	if(longrun):
		return 0	# Not supposed to happen

	time_now = datetime.utcnow()

	print_header(col1)

	new_error = 0

	for devname, location, permanent in activelist:
		if(location is not None):	# Location actually exists
			try:
				maxTime = [item for item in timeslist if item[0] == devname][0][1]
				if((time_now - maxTime) > timedelta(minutes=timeout)):	# If it has been more than fifteen minutes for a gateway
					status = STATUS_DOWN
				else:
					status = STATUS_OK

				# Store this in the today list
				try:
					# Check if we have an entry for this device today
					today_statuslist[devname]
				except:
					# New device for today
					today_statuslist[devname] = [location, permanent, time_now, maxTime, status, 0]
					
				# If this is an error increment the count and overwrite the status
				if(status == STATUS_DOWN):
					today_statuslist[devname][4] = status
					today_statuslist[devname][5] += 1

					# If the count is 1, this is a new error for today
					if(today_statuslist[devname][5] == 1):
						try:
							# Check if this error was already sent in the yesterday email
							yest_statuslist[devname]
						except:
							# New error for both yesterday and today
							new_error += 1
							print_row(devname, location, permanent, time_now, maxTime, status, 1)
			except IndexError:
				print("Error: device not found - " + str(devname))
				status = STATUS_NOT_FOUND
				today_statuslist[devname] = [location, permanent, 0, 0, status, 0]

	statuss = open(outfile, 'w')
	for devname in today_statuslist:
		statuss.write(devname)
		for field in today_statuslist[devname]:
			statuss.write(',' + str(field))
		statuss.write('\n')

	return new_error

def read_file(status_list, listType, day):
	try:
		infile = open(logpath + listType + '-status-' + day.strftime("%Y-%m-%d") + '.log', 'r')
		for line in infile:
			deviceMAC, location, permanent, time_status, avgstatusTime, status, count = line.strip('\n').split(',')
			if(time_status == '0'):
				time_status = 0
				avgstatusTime = 0
			else:
				time_status = datetime.strptime(time_status, "%Y-%m-%d %H:%M:%S.%f")
				avgstatusTime = datetime.strptime(avgstatusTime, "%Y-%m-%d %H:%M:%S")
			status_list[deviceMAC] = [location, permanent, time_status, avgstatusTime, status, int(count)]
		infile.close()
	except IOError:
		print("Unknown file - " + logpath + listType + '-status-' + day.strftime("%Y-%m-%d") + '.log')


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

email_body.append('<style>\n\t.bottom-three {\n\t\tmargin-bottom: 3cm;\n\t}\n</style>')
email_body.append('<p class=\"bottom-three\">Script start time: ' + str(datetime.utcnow()) + '</p>')
email_end = '</table></body></html>'

# If this is a daily run the database is not connected, instead only the yesterday file is sent
# If a shortrun, the database is connected and new statuss are found
if(longrun):
	print_list(gw_yest_list, "GatewayMAC")
	print_list(pb_yest_list, "DeviceMAC")
	print("Sending results via email")
	email_body.append(email_end)
	yagmail.SMTP('powerblade.lab11@gmail.com', password).send('powerblade@umich.edu', 'Re: PowerBlade Deployment Status Email', email_body)
else:
	# Set up connection
	aws_login = mylogin.get_login_info('aws')
	aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
	aws_c = aws_db.cursor()

	# Query for list of gateways that should be active (inf_gw_lookup where now is between dates)
	aws_c.execute('select lower(gatewayMAC), location, 1 from ' \
		'(select t1.* from inf_gw_lookup t1 where t1.id = ' \
		'(select max(t2.id) from inf_gw_lookup t2 where t1.gatewayMAC=t2.gatewayMAC)) t1 ' \
		'where ((utc_timestamp between startTime and endTime) or ' \
		'(utc_timestamp > startTime and endTime is null) or ' \
		'(utc_timestamp < endTime and startTime is null)) order by GatewayMAC desc;')
	# aws_c.execute('select gatewayMAC, location from inf_gw_lookup where ((utc_timestamp between startTime and ' \
	# 	'endTime) or (utc_timestamp > startTime and endTime is null) or (utc_timestamp < endTime and startTime is null)) order by GatewayMAC desc')
	gateway_active = aws_c.fetchall()

	# Query for list of PowerBlades that should be active (inf_pb_lookup where now is between dates)
	aws_c.execute('select lower(deviceMAC), location, permanent from ' \
		'(select t1.* from inf_pb_lookup t1 where t1.id = ' \
		'(select max(t2.id) from inf_pb_lookup t2 where t1.deviceMAC=t2.deviceMAC)) t1 ' \
		'where ((utc_timestamp between startTime and endTime) or ' \
		'(utc_timestamp > startTime and endTime is null) or ' \
		'(utc_timestamp < endTime and startTime is null)) order by deviceMAC desc;')
	#aws_c.execute('select deviceMAC, permanent from inf_pb_lookup where utc_timestamp between startTime and endTime')
	pb_active = aws_c.fetchall()

	# Query for most recent time seeing each gateway
	aws_c.execute('select lower(t1.gatewaymac), (select t2.timestamp from dat_powerblade t2 where t2.id=max(t1.id)) as maxTime ' \
		'from dat_powerblade t1 group by t1.gatewaymac')
	gateway_times = aws_c.fetchall()

	# Query for most recent time seeing each PowerBlade
	aws_c.execute('select lower(t1.deviceMAC), (select t2.timestamp from dat_powerblade t2 where t2.id=max(t1.id)) as maxTime ' \
		'from dat_powerblade t1 group by t1.deviceMAC')
	pb_times = aws_c.fetchall()

	total_statuss = 0

	total_statuss += check_list(gateway_active, gateway_times, gw_yest_list, gw_today_list, logpath + 'gateway-status-' + today.strftime("%Y-%m-%d") + '.log', "GatewayMAC", 15)
	total_statuss += check_list(pb_active, pb_times, pb_yest_list, pb_today_list, logpath + 'powerblade-status-' + today.strftime("%Y-%m-%d") + '.log', "DeviceMAC", 30)

	email_body.append(email_end)

	if(total_statuss > 0):
		print("Sending results via email")
		yagmail.SMTP('powerblade.lab11@gmail.com', password).send('powerblade@umich.edu', 'Re: PowerBlade Deployment New Device Error', email_body)
	else:
		print("No errors, no email")


