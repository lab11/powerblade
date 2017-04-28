#!/usr/bin/env python

import mylogin
import MySQLdb
import yagmail
from datetime import datetime, timedelta
import sys
from os.path import expanduser

sys.path.append('../plot/')
import pytch

from math import floor

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

def is_number(s):
    try:
        float(s)
        return True
    except:
        return False

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

	

# Set up connection
aws_login = mylogin.get_login_info('aws')
aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
aws_c = aws_db.cursor()


downsample = 3600


# Location
locations = [5]

# Start and end times
start_date = datetime.strptime('2017-02-23', '%Y-%m-%d')
end_date = datetime.strptime('2017-04-17', '%Y-%m-%d')


# Script body
script_start = datetime.utcnow()

# Determine script scope
total_scope = 0
locLists = {}
for loc in locations:
	locLists[loc] = []

	# Get list of rooms for this location (that contain both powerblades and blinks)
	sys.stdout.write('Pulling room list for location ' + str(loc) + ' ... ')
	sys.stdout.flush()
	item_start = datetime.utcnow()
	aws_c.execute('select t1.room from ' \
		'(select room from valid_blinks where location=' + str(loc) + ' group by room) t1 ' \
		'join ' \
		'(select room from valid_powerblades where location=' + str(loc) + ' group by room) t2 ' \
		'on t1.room=t2.room;')
	rooms = aws_c.fetchall()

	for room in rooms:
		total_scope += (4 * ((end_date - start_date).days+1)); # One for download, one for upload for each of blink and powerblade
		locLists[loc].append(room[0])

	print(str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')


query_start = datetime.utcnow()

print('')

for loc in locLists:

	for room in locLists[loc]:

		# First query date is the start date
		query_date = start_date

		while query_date <= end_date:

				query_date_str = query_date.strftime('%Y-%m-%d')

				item_start = datetime.utcnow()
				sys.stdout.write('Getting ' + query_date_str + ' for location ' + str(loc) + ' ' + room + ' Blink data ... ')
				sys.stdout.flush()
				aws_c.execute('select t1.deviceMAC, t2.room, t1.tsMin, t1.minMot from ' \
					'(select round(unix_timestamp(timestamp)/(' + str(downsample) + ')) as timekey, left(max(timestamp), 16) as tsMin, deviceMAC, sum(minMot) as minMot ' \
					'from dat_blink force index (devMIN) ' \
					'where deviceMAC in (select deviceMAC from valid_blinks where location=' + str(loc) + ' and room=\'' + room + '\' group by deviceMAC) ' \
					'and timestamp >=\"' + query_date.strftime('%Y-%m-%d') + '\" and timestamp <date_add(\"' + query_date.strftime('%Y-%m-%d') + '\", interval 1 day) ' \
					'group by timekey, deviceMAC) t1 ' \
					'join valid_blinks t2 ' \
					'on t1.deviceMAC=t2.deviceMAC ' \
					'order by t1.deviceMAC, t1.timekey;')
				blink_data = aws_c.fetchall()
				print(str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')
				#'and date(timestamp)=\'' + query_date_str + '\' ' \
				print(str(len(blink_data)) + ' devices')

				print_time()

				item_start = datetime.utcnow()
				sys.stdout.write('Uploading to AWS ... ')
				sys.stdout.flush()
				for devMAC, room, tsMin, minMot in blink_data:
					aws_c.execute('insert into dat_occ_blink (deviceMAC, room, tsMin, minMot) values (' \
						'\'' + str(devMAC) + '\', \'' + str(room) + '\', \'' + str(tsMin) + '\', ' + str(minMot) + ');')
					aws_db.commit()
				print(str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')

				print_time()

				item_start = datetime.utcnow()
				sys.stdout.write('Getting ' + query_date_str + ' for location ' + str(loc) + ' ' + room + ' PowerBlade data ... ')
				sys.stdout.flush()
				aws_c.execute('select t1.deviceMAC, t2.room, t1.tsMin, t1.avgPower from ' \
					'(select round(unix_timestamp(timestamp)/(' + str(downsample) + ')) as timekey, left(max(timestamp), 16) as tsMin, deviceMAC, avg(power) as avgPower ' \
					'from dat_powerblade force index (devPower) ' \
					'where deviceMAC in (select deviceMAC from valid_powerblades where location=' + str(loc) + ' and room=\'' + room + '\' group by deviceMAC) ' \
					'and timestamp >=\"' + query_date.strftime('%Y-%m-%d') + '\" and timestamp <date_add(\"' + query_date.strftime('%Y-%m-%d') + '\", interval 1 day) ' \
					'group by deviceMAC, timekey) t1 ' \
					'join valid_powerblades t2 ' \
					'on t1.deviceMAC=t2.deviceMAC ' \
					"order by t1.deviceMAC, t1.timekey;")
				pb_data = aws_c.fetchall()
				print(str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')
				print(str(len(pb_data)) + ' devices')

				print_time()

				item_start = datetime.utcnow()
				sys.stdout.write('Uploading to AWS ... ')
				sys.stdout.flush()
				for devMAC, room, tsMin, avgPwr in pb_data:
					aws_c.execute('insert into dat_occ_pb (deviceMAC, room, tsMin, avgPower) values (' \
						'\'' + str(devMAC) + '\', \'' + str(room) + '\', \'' + str(tsMin) + '\', ' + str(round(avgPwr,6)) + ');')
					aws_db.commit()
				print(str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')

				print_time()

				query_date = query_date + timedelta(days=1)






