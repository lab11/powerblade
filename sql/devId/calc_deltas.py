#!/usr/bin/env python

import mylogin
import MySQLdb
import yagmail
from datetime import datetime, timedelta
import sys
from os.path import expanduser

# Set up connection
aws_login = mylogin.get_login_info('aws')
aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
aws_c = aws_db.cursor()


# Query for the device list
aws_c.execute('select deviceMAC from valid_powerblades where deviceMAC=\'c098e570027d\' and location!=1 and location!=10 limit 1;')
device_list = aws_c.fetchall()
devList = [i[0] for i in device_list]

# First query device is the first device
devI = 0
query_dev = devList[devI]
devI += devI


# Set up start and end times
start_date = datetime.strptime('2017-04-11', '%Y-%m-%d')
end_date = datetime.strptime('2017-04-12', '%Y-%m-%d')

# First query date is the start date
query_date = start_date


new_data = {}

for query_dev in devList:

	query_date = start_date

	new_data[query_dev] = {}

	while query_date <= end_date:

		item_start = datetime.utcnow()
		sys.stdout.write('Pulling data for ' + query_dev + ' on ' + query_date.strftime('%Y-%m-%d') + ' ... ')
		sys.stdout.flush()
		aws_c.execute('select * from dat_powerblade force index (devTimeSeq) ' \
			'where deviceMAC=\'' + query_dev + '\' and date(timestamp)=\'' + query_date.strftime('%Y-%m-%d') + '\' ' \
			'order by deviceMAC, timestamp, seq;')
		cur_data = aws_c.fetchall()
		print(str((datetime.utcnow() - item_start).total_seconds()) + ' seconds')

		item_start = datetime.utcnow()
		sys.stdout.write('Processing deltas ... ')
		sys.stdout.flush()

		new_data[query_dev][query_date] = {}
		new_data[query_dev][query_date]['5'] = [0,0]
		new_data[query_dev][query_date]['10'] = [0,0]
		new_data[query_dev][query_date]['15'] = [0,0]
		new_data[query_dev][query_date]['25'] = [0,0]
		new_data[query_dev][query_date]['50'] = [0,0]
		new_data[query_dev][query_date]['75'] = [0,0]
		new_data[query_dev][query_date]['100'] = [0,0]
		new_data[query_dev][query_date]['150'] = [0,0]
		new_data[query_dev][query_date]['250'] = [0,0]
		new_data[query_dev][query_date]['500'] = [0,0]

		curPow = 0
		last_real_delta = 0
		prev_delta = 0
		curSeq = 0
		for pid, gwMac, devMac, seq, volt, power, energy, pf, flags, timestamp in cur_data:
			if(curPow == 0):	# First run
				curPow = power
			elif(curSeq != seq): # New measurement
				curSeq = seq

				# Calculate delta to the previous measurement
				delta = power - curPow
				curPow = power

				# Check if this delta is combinable with the previous
				# This is true if both are valid (above 5) and have the same sign
				# If true, combine them and do not print the previous
				if(abs(delta) >= 5 and abs(prev_delta) >= 5 and (delta<0) == (prev_delta<0)):
					prev_delta += delta
				else:
					# Otherwise, if the previous delta is valid it should be processed
					if(abs(prev_delta) >= 5):
						# Process delta
						# Detect potential 'spike' - positive increase followed by at least 30% decrease
						# Note that this applies to the last real delta, as this current delta is used to confirm the 30% correction
						if(last_real_delta > 0 and (float(last_real_delta) + float(prev_delta)/.3) < 0):
							for binSize in new_data[query_dev][query_date]:
								if(last_real_delta >= int(binSize)*10):
									new_data[query_dev][query_date][binSize][1] += 1
						last_real_delta = prev_delta

						# Assign to correct bin(s)
						for binSize in new_data[query_dev][query_date]:
							if(prev_delta >= int(binSize) and prev_delta <= int(binSize)*5):
								new_data[query_dev][query_date][binSize][0] += 1

					# Finally, if this current delta is valid then save it
					if(abs(delta) >= 5):
						prev_delta = delta
					else:
						prev_delta = 0

		print(str((datetime.utcnow() - item_start).total_seconds()) + ' seconds')

		query_date = query_date + timedelta(days=1)

for dev in new_data:
	for date in new_data[dev]:
		print(new_data[dev][date])
			
