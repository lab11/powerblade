#!/usr/bin/env python

import mylogin
import MySQLdb
import yagmail
from datetime import datetime, timedelta
import sys

STATUS_OK = "<font color=\"green\"><b>OK!</b></font>"
STATUS_DOWN = "<font color=\"orange\"><b>Down</b></font>"
STATUS_NOT_FOUND = "</td><td></td><td><font color=\"red\"><b>Not Found</b></font>"

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

longrun = 1
if len(sys.argv) > 1:
	if(sys.argv[1] == 'short'):
		print("Running PowerBlade Deployment Status Script - short check")
		email_body = ['<!DOCTYPE html><html><body><h1> PowerBlade Deployment Status Email - New Error Found</h1>']
		pb_error_list = []
		f = open('/tmp/powerblade-error.log', 'r')
		for line in f:
			try:
				deviceMAC, error = line.strip('\n').split(',')
				pb_error_list.append((deviceMAC, error))
			except:
				pass
		f.close()
		gw_error_list = []
		f = open('/tmp/gateway-error.log', 'r')
		for line in f:
			try:
				gatewayMAC, error = line.strip('\n').split(',')
				gw_error_list.append((gatewayMAC, error))
			except:
				pass
		f.close()
		longrun = 0
	elif(sys.argv[1] == 'daily'):
		print("Running PowerBlade Deployment Status Script - daily run")
		email_body = ['<!DOCTYPE html><html><body><h1> PowerBlade Deployment Status Email - Full Update</h1>']
	else:
		print("Unknown parameter")
		# TODO: send error email
		exit()

#print(pb_error_list)
#exit()

email_end = '</table></body></html>'

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

first_header = 1
def print_header(col1, col2):
	if(first_header == 1):
		email_body.append("<table style=\"width:80%\">")
		first_header = 0
	else:
		email_body.append("<tr><td><b>" + col1 + "</b></td><td><b>" + col2 + \
			"</b></td><td><b>Last Seen</b></td><td><b>Offtime</b></td><td><b>Status</b></td></tr>")

def print_row(name, specifier, time_now, maxTime, status):
	email_body.append("<tr><td>" + str(name) + "</td><td>" + str(specifier) + "</td><td>" + str(maxTime) + \
		"</td><td>" + str(chop_microseconds(time_now - maxTime)) + "</td><td>" + status + "</td></tr>")

def print_error(name, specifier):
	email_body.append("<tr><td>" + str(name) + "</td><td>" + str(specifier) + "</td><td>" + STATUS_NOT_FOUND + "</td></tr>")

def check_list(activelist, timeslist, outfile, col1, col2):
	time_now = datetime.utcnow()

	if(longrun == 1):
		print_header(col1, col2)

	new_errors = 0
	errors = open(outfile, 'w')

	for devname, specifier in activelist:
		if(specifier is not None):	# Location actually exists
			try:
				maxTime = [item for item in timeslist if item[0] == devname][0][1]
				if((time_now - maxTime) > timedelta(minutes=15)):	# If it has been more than fifteen minutes for a gateway
					status = STATUS_DOWN
				else:
					status = STATUS_OK

				if(longrun == 1):
					print_row(devname, specifier, time_now, maxTime, status)
				else:
					if(status != STATUS_OK):
						try:
							[item for item in gw_error_list if item[0] == devname and item[1] == status]
						except:
							if(new_gw_errors == 0):
								print_header(col1, col2)
								new_errors += 1
							print_row(devname, specifier, time_now, maxTime, status)
							errors.write(str(devname) + ',' + str(status) + '\n')
				
			except IndexError:
				# print("Error: gateway not found - " + str(gateway))
				if(longrun == 1):
					print_error(devname, specifier)

# Set up connection
aws_login = mylogin.get_login_info('aws')
aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
aws_c = aws_db.cursor()

# Query for list of gateways that should be active (inf_gw_lookup where now is between dates)
aws_c.execute('select gatewayMAC, location from inf_gw_lookup where utc_timestamp between startTime and ' \
	'endTime order by GatewayMAC desc')
gateway_active = aws_c.fetchall()

# Query for list of PowerBlades that should be active (inf_pb_lookup where now is between dates)
aws_c.execute('select deviceMAC, permanent from inf_pb_lookup where utc_timestamp between startTime and endTime')
pb_active = aws_c.fetchall()

# Query for most recent time seeing each gateway
aws_c.execute('select t1.gatewaymac, (select t2.timestamp from dat_powerblade t2 where t2.id=max(t1.id)) as maxTime ' \
	'from dat_powerblade t1 group by t1.gatewaymac')
gateway_times = aws_c.fetchall()

# Query for most recent time seeing each PowerBlade
aws_c.execute('select t1.deviceMAC, (select t2.timestamp from dat_powerblade t2 where t2.id=max(t1.id)) as maxTime ' \
	'from dat_powerblade t1 group by t1.deviceMAC')
pb_times = aws_c.fetchall()


check_list(gateway_active, gateway_times, '/tmp/gateway-error.log', "GatewayMAC", "Location")
check_list(pb_active, pb_times, '/tmp/powerblade-error.log', "DeviceMAC", "Permanent")


print("Sending results via email")
email_body.append(email_end)
yagmail.SMTP('powerblade.lab11@gmail.com', password).send('powerblade@umich.edu', 'Re: PowerBlade Deployment Status Email', email_body)


