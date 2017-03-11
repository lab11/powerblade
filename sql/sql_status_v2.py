#!/usr/bin/env python

import mylogin
import MySQLdb
import yagmail
from datetime import datetime, timedelta
import sys
from os.path import expanduser

STATUS_OK = "<font color=\"green\"><b>OK!</b></font>"
STATUS_WARNING = "<font color=\"orange\"><b>Warning</b></font>"
STATUS_NOT_FOUND = "<font color=\"red\">Not Found</font>"

def print_header(col1, col2, col3):
	email_body.append("<tr>" \
		"<td><b>" + col1 + "</b></td>" \
		"<td><b>" + col2 + "</b></td>" \
		"<td><b>Location</b></td>" \
		"<td><b>Status</b></td>" \
		"<td><b>Avg. Count in 15 mins</b></td>" \
		"<td><b>" + col3 + "</b></td>" \
		"</tr>")

def print_row(mac, name, location, status, count, seen):
	email_body.append("<tr>" \
		"<td>" + str(mac) + "</td>" \
		"<td>" + str(name) + "</td>" \
		"<td>" + str(location) + "</td>" \
		"<td>" + status + "</td>" \
		"<td>" + str(count) + "</td>" \
		"<td>" + str(seen) + "</td>" \
		"</tr>")

def check_devices(printLines, col1, col2, col3, list):
	print_header(col1, col2, col3)

	save_loc = -1
	ok_count = 0
	for mac, name, location, permanent, count, seen in list:
		if printLines and (location != save_loc):
			print_row("", ok_count + " devices OK", save_loc, STATUS_OK, '', '')
			ok_count = 0
			email_body.append("<tr><td colspan=\"5\"><b>Location " + str(location) + "</b></td></tr>")
			save_loc = location
		if permanent == 1:
			if count > 400:
				pass
				ok_count = ok_count + 1
				#print_row(mac, name, location, STATUS_OK, count, '')
			elif count > 0:
				print_row(mac, name, location, STATUS_WARNING, count, seen)
			else:
				print_row(mac, name, location, STATUS_NOT_FOUND, '', seen)	


# Prepare email for sending
email_body = ['<!DOCTYPE html><html><body><h2> PowerBlade Deployment Status Email - Full Update</h2>']
email_body.append('<p>Script start time: ' + str(datetime.utcnow()) + '</p>')	




# Set up connection
aws_login = mylogin.get_login_info('aws')
aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
aws_c = aws_db.cursor()

aws_c.execute('select *,\'\' from success_gateway')
success_gateway = aws_c.fetchall()

aws_c.execute('select t1.*, t2.maxTime as last_seen from success_powerblade t1 left join last_seen_pb t2 on t1.deviceMAC=t2.deviceMAC;')
success_powerblade = aws_c.fetchall()

aws_c.execute('select t1.*, t2.maxTime as last_seen from success_blink t1 left join last_seen_blink t2 on t1.deviceMAC=t2.deviceMAC;')
success_blink = aws_c.fetchall()

aws_c.execute('select t1.*, t2.maxTime as last_seen from success_light t1 left join last_seen_light t2 on t1.deviceMAC=t2.deviceMAC')
success_light = aws_c.fetchall()




email_body.append("<table style=\"width:80%\">")

check_devices(False, 'gatewayMAC', '', '', success_gateway)
email_body.append("<tr><td colspan=\"5\">&nbsp</td></tr>")

email_body.append("<tr><td colspan=\"5\"><b>PowerBlade</b></td></tr>")
check_devices(True, 'deviceMAC', 'Name', 'Last Seen', success_powerblade)
email_body.append("<tr><td colspan=\"5\">&nbsp</td></tr>")

email_body.append("<tr><td colspan=\"5\"><b>Blink</b></td></tr>")
check_devices(True, 'deviceMAC', 'Room', 'Last Seen', success_blink)
email_body.append("<tr><td colspan=\"5\">&nbsp</td></tr>")

email_body.append("<tr><td colspan=\"5\"><b>BLEES & Ligeiro</b></td></tr>")
check_devices(True, 'deviceMAC', 'Name', 'Last Seen', success_light)
email_body.append("<tr><td colspan=\"5\">&nbsp</td></tr>")

email_body.append('</table></body></html>')



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



yagmail.SMTP('powerblade.lab11@gmail.com', password).send('powerblade@umich.edu', 'Re: PowerBlade Deployment Status Email', email_body)








