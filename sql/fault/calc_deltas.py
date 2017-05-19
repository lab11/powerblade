#!/usr/bin/env python

import mylogin
import MySQLdb
from datetime import datetime, timedelta
import sys
from os.path import expanduser

sys.path.append('../plot/')
import pytch

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

def conv_to_datetime(timestr):
	return datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')

def conv_to_string(dt):
	return dt.strftime('%Y-%m-%d %H:%M:%S')

script_start = datetime.utcnow()

# Set up connection
aws_login = mylogin.get_login_info('aws')
aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
aws_c = aws_db.cursor()



# List of queries to run
# Format: [ device MAC, device name, tag, start time, end time, broken [0-3], downsample]
query_list = [
#['c098e570004b', 'vacuum', '', '2017-05-01 14:53:32', '2017-05-01 14:55:00', 0, 10],
#['c098e570004b', 'vacuum', '', '2017-05-01 15:04:30', '2017-05-01 15:05:12', 0, 10],
#['c098e570004b', 'vacuum', '', '2017-05-01 14:57:29', '2017-05-01 14:58:16', 1, 10],
#['c098e570004b', 'vacuum', '', '2017-05-01 14:59:04', '2017-05-01 14:59:40', 2, 10],
#['c098e570004b', 'vacuum', '', '2017-05-01 15:00:51', '2017-05-01 15:01:16', 3, 10],
['c098e5700299', 'vacuum3', '', '2017-05-09 21:01:00', '2017-05-09 21:06:00', 0, 5],
['c098e5700299', 'vacuum3', '', '2017-05-09 20:56:00', '2017-05-09 21:00:00', 1, 5]
# ['c098e570025c', 'vacuum3', '', '2017-03-30 00:00:00', '2017-04-02 00:00:00', 1, 60],
# ['c098e570025c', 'vacuum3', '', '2017-04-15 00:00:00', '2017-04-18 00:00:00', 0, 60]
# ['c098e570015e', 'xbox', '', '2017-03-28 02:00:00', '2017-03-28 02:15:00', 0, 30],
# ['c098e570015e', 'xbox', '', '2017-03-30 00:45:00', '2017-03-30 01:15:00', 0, 30],
# ['c098e570004b', 'xbox', 'games', '2017-05-09 19:30:00', '2017-05-09 20:00:05', 0, 30],
# ['c098e570004b', 'xbox', 'netflix', '2017-05-01 17:40:00', '2017-05-01 17:48:35', 0, 30],
# ['c098e570004b', 'xbox', 'battlefront', '2017-05-01 15:14:00', '2017-05-01 15:17:59', 0, 30],
# ['c098e570004b', 'xbox', 'black flag', '2017-05-01 16:34:19', '2017-05-01 16:38:26', 0, 30],
# ['c098e570004b', 'xbox', 'netflix', '2017-05-01 16:03:01', '2017-05-01 16:10:07', 1, 30],
# ['c098e570004b', 'xbox', 'battlefront', '2017-05-01 15:24:00', '2017-05-01 15:30:33', 1, 30],
# ['c098e570004b', 'xbox', 'black flag', '2017-05-01 16:23:00', '2017-05-01 16:30:28', 1, 30],
# ['c098e570015e', 'xbox2', '', '2017-02-18 18:30:00', '2017-02-18 18:40:00', 1, 10],
# ['c098e570015e', 'xbox2', '', '2017-02-22 00:35:00', '2017-02-22 00:45:00', 0, 10]
# ['c098e570028c', 'veel', '', '2017-05-08 16:00:00', '2017-05-09 02:00:00', 0, 600],
# ['c098e570028c', 'veel', '', '2017-05-09 14:30:00', '2017-05-09 15:30:00', 0, 600],
# ['c098e570028c', 'veel', '', '2017-05-09 03:00:00', '2017-05-09 14:00:00', 1, 600],
# ['c098e570028c', 'veel', '', '2017-05-09 18:30:00', '2017-05-09 19:20:00', 1, 600]
]

total_scope = 0
for deviceMAC, deviceName, tag, start_time, end_time, broken, downsample in query_list:
	total_scope += ((conv_to_datetime(end_time) - conv_to_datetime(start_time)).days*86000 + (conv_to_datetime(end_time) - conv_to_datetime(start_time)).seconds)/(downsample) + 1


print('\nTotal queries: ' + str(len(query_list)))
print('Total minutes: ' + str(total_scope))


total_complete = 0


for deviceMAC, deviceName, tag, start_time, end_time, broken, downsample in query_list:

	query_start = start_time
	query_end = conv_to_string(conv_to_datetime(query_start) + timedelta(seconds=(downsample)))

	while conv_to_datetime(query_end) < (conv_to_datetime(end_time) + timedelta(seconds=(downsample))):

		item_start = datetime.utcnow()
		sys.stdout.write('Pulling data for ' + deviceMAC + ' as ' + deviceName + ' between ' + query_start + ' and ' + query_end + ' ... ')
		sys.stdout.flush()
		aws_c.execute('select * from dat_powerblade force index (devTimeSeq) ' \
			'where deviceMAC=\'' + deviceMAC + '\' ' \
			'and timestamp>\'' + query_start + '\' and timestamp<=\'' + query_end + '\' ' \
			'order by deviceMAC, timestamp, seq;')
		cur_data = aws_c.fetchall()

		aws_c.execute('select min(timestamp) as minTs, avg(power) as avgPwr, var_pop(power) as varPwr, min(power) as minPwr, max(power) as maxPwr ' \
			'from dat_powerblade force index (devTimeSeq) '
			'where deviceMAC=\'' + deviceMAC + '\' ' \
			'and timestamp>\'' + query_start + '\' and timestamp<=\'' + query_end + '\' ' \
			'and power>30;')
		minTs, avgPwr, varPwr, minPwr, maxPwr = aws_c.fetchall()[0]

		print(str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')

		item_start = datetime.utcnow()
		sys.stdout.write('Processing deltas ... ')
		sys.stdout.flush()

		dat = {}
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

		print(str(totalCt) + ' found in ' + str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')

		print(str(dat))

		total_complete += 1
		print('\nTotal elapsed time: ' + str(chop_microseconds(datetime.utcnow() - script_start)))
		print(str(round(100*float(total_complete)/total_scope,2)) + ' pct complete')
		print('Remaining time: ' + str(chop_microseconds(((datetime.utcnow() - script_start)*total_scope/total_complete)-(datetime.utcnow() - script_start))) + '\n')

		#aws_c.execute
		if(minTs):
			aws_c.execute('insert into dat_fault_vector (minTs, deviceMAC, ' \
				'deviceName, tag, '
				'avgPwr, varPwr, minPwr, maxPwr, ' \
				'ct5, spk5, ct10, spk10, ct15, spk15, ' \
				'ct25, spk25, ct50, spk50, ct75, spk75, ' \
				'ct100, spk100, ct150, spk150, ct250, spk250, ' \
				'ct500, spk500, broken) ' \
				'values (\'' + str(minTs) + '\', \'' + deviceMAC + '\', \'' + deviceName + '\', \'' + tag + '\', ' + \
				str(round(avgPwr,2)) + ', ' + str(round(varPwr,2)) + ', ' + str(round(minPwr,2)) + ', ' + str(round(maxPwr,2)) + ', ' + \
				str(dat['5'][0]) + ', ' + str(dat['5'][1]) + ', ' + str(dat['10'][0]) + ', ' + str(dat['10'][1]) + ', ' + str(dat['15'][0]) + ', ' + str(dat['15'][1]) + ', ' + \
				str(dat['25'][0]) + ', ' + str(dat['25'][1]) + ', ' + str(dat['50'][0]) + ', ' + str(dat['50'][1]) + ', ' + str(dat['75'][0]) + ', ' + str(dat['75'][1]) + ', ' + \
				str(dat['100'][0]) + ', ' + str(dat['100'][1]) + ', ' + str(dat['150'][0]) + ', ' + str(dat['150'][1]) + ', ' + str(dat['250'][0]) + ', ' + str(dat['250'][1]) + ', ' + \
				str(dat['500'][0]) + ', ' + str(dat['500'][1]) + ', ' + \
				str(broken) + ');')
			aws_db.commit()

		query_start = query_end
		query_end = conv_to_string(conv_to_datetime(query_start) + timedelta(seconds=(downsample)))


			
