#!/usr/bin/env python

import mylogin
import MySQLdb
import yagmail
from datetime import datetime, timedelta
import sys
from os.path import expanduser

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

script_start = datetime.utcnow()

# Set up connection
aws_login = mylogin.get_login_info('aws')
aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
aws_c = aws_db.cursor()


# Query for the device list
item_start = datetime.utcnow()
sys.stdout.write('Querying device list ... ')
aws_c.execute('select deviceMAC from valid_powerblades where (deviceMAC=\'c098e570016D\' or deviceMAC=\'c098e570016D\') and location!=1 and location!=10;')
device_list = aws_c.fetchall()
devList = [i[0] for i in device_list]
print(str((datetime.utcnow() - item_start).total_seconds()) + ' seconds')

# First query device is the first device
devI = 0
query_dev = devList[devI]
devI += devI


# Set up start and end times
start_date = datetime.strptime('2017-02-15', '%Y-%m-%d')
end_date = datetime.strptime('2017-03-15', '%Y-%m-%d')

print('\nTotal devices: ' + str(len(devList)))
print('Query scope: ' + str((end_date - start_date).days+1) + ' days')
print('Expected runtime: ' + str(timedelta(seconds=(len(devList) * ((end_date - start_date).days+1) * 25))) + '\n')

total_scope = len(devList) * ((end_date - start_date).days+1);
total_complete = 0

# First query date is the start date
query_date = start_date


new_data = {}

for query_dev in devList:

	query_date = start_date

	new_data[query_dev] = {}

	while query_date <= end_date:

		query_date_str = query_date.strftime('%Y-%m-%d')

		item_start = datetime.utcnow()
		sys.stdout.write('Pulling data for ' + query_dev + ' on ' + query_date_str + ' ... ')
		sys.stdout.flush()
		aws_c.execute('select * from dat_powerblade force index (devTimeSeq) ' \
			'where deviceMAC=\'' + query_dev + '\' and date(timestamp)=\'' + query_date_str + '\' ' \
			'order by deviceMAC, timestamp, seq;')
		cur_data = aws_c.fetchall()
		print(str((datetime.utcnow() - item_start).total_seconds()) + ' seconds')

		item_start = datetime.utcnow()
		sys.stdout.write('Processing deltas ... ')
		sys.stdout.flush()

		new_data[query_dev][query_date_str] = {}
		dat = new_data[query_dev][query_date_str]
		dat['5'] = [0,0]
		dat['10'] = [0,0]
		dat['15'] = [0,0]
		dat['25'] = [0,0]
		dat['50'] = [0,0]
		dat['75'] = [0,0]
		dat['100'] = [0,0]
		dat['150'] = [0,0]
		dat['250'] = [0,0]
		dat['500'] = [0,0]

		curPow = 0
		last_real_delta = 0
		prev_delta = 0
		curSeq = 0
		totalCt = 0
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
							for binSize in dat:
								if(last_real_delta >= int(binSize)*10):
									dat[binSize][1] += 1
						last_real_delta = prev_delta

						# Assign to correct bin(s)
						for binSize in dat:
							if(prev_delta >= int(binSize) and prev_delta <= int(binSize)*5):
								dat[binSize][0] += 1
								totalCt += 1

					# Finally, if this current delta is valid then save it
					if(abs(delta) >= 5):
						prev_delta = delta
					else:
						prev_delta = 0

		print(str(totalCt) + ' found in ' + str((datetime.utcnow() - item_start).total_seconds()) + ' seconds')

		print(str(dat))

		total_complete += 1
		print('\nTotal elapsed time: ' + str(chop_microseconds(datetime.utcnow() - script_start)))
		print(str(round(100*float(total_complete)/total_scope,2)) + ' pct complete')
		print('Remaining time: ' + str(chop_microseconds((datetime.utcnow() - script_start)*total_scope/total_complete)) + '\n')

		if(totalCt > 0): 
			aws_c.execute('insert into dat_delta (dayst, deviceMAC, ' \
				'ct5, spk5, ct10, spk10, ct15, spk15, ' \
				'ct25, spk25, ct50, spk50, ct75, spk75, ' \
				'ct100, spk100, ct150, spk150, ct250, spk250, ' \
				'ct500, spk500) ' \
				'values (\'' + str(query_date_str) + '\', \'' + query_dev + '\', ' + \
				str(dat['5'][0]) + ', ' + str(dat['5'][1]) + ', ' + str(dat['10'][0]) + ', ' + str(dat['10'][1]) + ', ' + str(dat['15'][0]) + ', ' + str(dat['15'][1]) + ', ' + \
				str(dat['25'][0]) + ', ' + str(dat['25'][1]) + ', ' + str(dat['50'][0]) + ', ' + str(dat['50'][1]) + ', ' + str(dat['75'][0]) + ', ' + str(dat['75'][1]) + ', ' + \
				str(dat['100'][0]) + ', ' + str(dat['100'][1]) + ', ' + str(dat['150'][0]) + ', ' + str(dat['150'][1]) + ', ' + str(dat['250'][0]) + ', ' + str(dat['250'][1]) + ', ' + \
				str(dat['500'][0]) + ', ' + str(dat['500'][1]) + ');')
			aws_db.commit()

		query_date = query_date + timedelta(days=1)

# for dev in new_data:
# 	for date in new_data[dev]:
# 		dat = new_data[dev][date]
# 		print(dev + ' ' + str(date) + ' ' + str(dat))
# 		aws_c.execute('insert into dat_delta (dayst, deviceMAC, ' \
# 			'ct5, spk5, ct10, spk10, ct15, spk15, ' \
# 			'ct25, spk25, ct50, spk50, ct75, spk75, ' \
# 			'ct100, spk100, ct150, spk150, ct250, spk250, ' \
# 			'ct500, spk500) ' \
# 			'values (\'' + str(date) + '\', \'' + dev + '\', ' + \
# 			str(dat['5'][0]) + ', ' + str(dat['5'][1]) + ', ' + str(dat['10'][0]) + ', ' + str(dat['10'][1]) + ', ' + str(dat['15'][0]) + ', ' + str(dat['15'][1]) + ', ' + \
# 			str(dat['25'][0]) + ', ' + str(dat['25'][1]) + ', ' + str(dat['50'][0]) + ', ' + str(dat['50'][1]) + ', ' + str(dat['75'][0]) + ', ' + str(dat['75'][1]) + ', ' + \
# 			str(dat['100'][0]) + ', ' + str(dat['100'][1]) + ', ' + str(dat['150'][0]) + ', ' + str(dat['150'][1]) + ', ' + str(dat['250'][0]) + ', ' + str(dat['250'][1]) + ', ' + \
# 			str(dat['500'][0]) + ', ' + str(dat['500'][1]) + ');')
# 		aws_db.commit()
			
