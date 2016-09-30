#!/usr/bin/env python

import mylogin
import MySQLdb
import yagmail
from datetime import datetime, timedelta

#yagmail.SMTP().send('sam.g.debruin@gmail.com', 'subject', 'This is the body')

#exit()

aws_login = mylogin.get_login_info('aws')
aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
aws_c = aws_db.cursor()

aws_c.execute('select t1.gatewaymac, (select t2.timestamp from dat_powerblade t2 where t2.id=max(t1.id)) as maxTime from dat_powerblade t1 group by t1.gatewaymac')

gateway_times = aws_c.fetchall()

time_now = datetime.utcnow()
print(time_now)

# Parse list of gateways for actives ones (date range w/ end=null or encompasing now())

for gateway, time in gateway_times:
	if(time is not None):
		print(gateway + ' - ' + str(time) + ' - ' + str(time_now - time))

		if((time_now - time) > timedelta(minutes=15)):
			print(gateway)

