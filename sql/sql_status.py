#!/usr/bin/env python

import mylogin
import MySQLdb
import yagmail
from datetime import datetime, timedelta

print("Running PowerBlade Deployment Status Script")

email_body = ['<!DOCTYPE html><html><body><h1> PowerBlade Deployment Status Email</h1>']
email_end = '</table></body></html>'

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

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

time_now = datetime.utcnow()

# Set up gateway status table
email_body.append("<table style=\"width:80%\"><tr><td><b>GatewayMAC</b></td>" \
	"<td><b>Location</b></td><td><b>Last Seen</b></td><td><b>Offtime</b></td><td><b>Status</b></td></tr>")

status_not_found = "</td><td></td><td><font color=\"red\"><b>Not Found</b></font>"

for gateway, location in gateway_active:
	if(location is not None):	# Location actually exists
		try:
			maxTime = [item for item in gateway_times if item[0] == gateway][0][1]
			if((time_now - maxTime) > timedelta(minutes=15)):	# If it has been more than fifteen minutes for a gateway
				status = "<font color=\"orange\"><b>Down</b></font>"
			else:
				status = "<font color=\"green\"><b>OK!</b></font>"
			email_body.append("<tr><td>" + str(gateway) + "</td><td>" + str(location) + "</td><td>" + str(maxTime) + \
				"</td><td>" + str(chop_microseconds(time_now - maxTime)) + "</td><td>" + status + "</td></tr>")
		except IndexError:
			print("Error: gateway not found - " + str(gateway))
			email_body.append("<tr><td>" + str(gateway) + "</td><td>" + str(location) + "</td><td>" + status_not_found + "</td></tr>")

email_body.append("<tr><td colspan=\"5\">&nbsp</td></tr><tr><td colspan=\"5\">&nbsp</td></tr><tr><td><b>DeviceMAC</b></td>" \
	"<td><b>Permanent</b></td><td><b>Last Seen</b></td><td><b>Offtime</b></td><td><b>Status</b></td></tr>")

for powerblade, permanent in pb_active:
	try:
		maxTime = [item for item in pb_times if item[0] == powerblade][0][1]
		if((time_now - maxTime) > timedelta(minutes=15)):
			status = "<font color=\"orange\"><b>Down</b></font>"
		else:
			status = "<font color=\"green\"><b>OK!</b></font>"
		email_body.append("<tr><td>" + str(powerblade) + "</td><td>" + str(permanent) + "</td><td>" + str(maxTime) + \
			"</td><td>" + str(chop_microseconds(time_now - maxTime)) + "</td><td>" + status + "</td></tr")
	except IndexError:
		print("Error: PowerBlade not found - " + str(powerblade))
		email_body.append("<tr><td>" + str(powerblade) + "</td><td>" + str(permanent) + "</td><td>" + status_not_found + "</td></tr>")

print("Sending results via email")
email_body.append(email_end)
yagmail.SMTP().send('powerblade@umich.edu', 'PowerBlade Deployment Status Email', email_body)


