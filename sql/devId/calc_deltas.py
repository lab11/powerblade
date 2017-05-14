#!/usr/bin/env python

import mylogin
import MySQLdb
import yagmail
from datetime import datetime, timedelta
import sys
from os.path import expanduser
import numpy

sys.path.append('../plot/')
import pytch

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
aws_c.execute('select deviceMAC from valid_powerblades where location in (9) ' \
	'and deviceType in (select * from id_categories);')
device_list = aws_c.fetchall()
devList = [i[0] for i in device_list]
print(str((datetime.utcnow() - item_start).total_seconds()) + ' seconds')

# First query device is the first device
devI = 0
query_dev = devList[devI]
devI += devI


# Set up start and end times
start_date = datetime.strptime('2017-03-30', '%Y-%m-%d')
end_date = datetime.strptime('2017-04-18', '%Y-%m-%d')

print('\nTotal devices: ' + str(len(devList)))
print('Query scope: ' + str((end_date - start_date).days+1) + ' days')
print('Expected runtime: ' + str(timedelta(seconds=(len(devList) * ((end_date - start_date).days+1) * 20))) + '\n')

confirm = pytch.input_loop('Press enter, or \'exit\' to cancel: ')

print('')

if(confirm == 'exit'):
	exit()

dev_scope = len(devList)
dev_complete = -1
total_scope = len(devList) * ((end_date - start_date).days+1);
total_complete = 0

# First query date is the start date
query_date = start_date


new_data = {}

for query_dev in devList:

	query_date = start_date

	dev_complete += 1

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
		print(str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')

		item_start = datetime.utcnow()
		sys.stdout.write('Occupancy data for ' + query_dev + ' on ' + query_date_str + ' ... ')
		sys.stdout.flush()
		aws_c.execute('select deviceMAC, deviceName, tsMin, avgPower, minMot ' \
			'from mr_dat_occ ' \
			'where deviceMAC=\'' + query_dev + '\' ' \
			'and date(tsMin)=\'' + query_date_str + '\' ' \
			'order by deviceMAC, tsMin;')
		occ_data = aws_c.fetchall()
		print(str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')

		item_start = datetime.utcnow()
		sys.stdout.write('Statistics for ' + query_dev + ' on ' + query_date_str + ' ... ')
		sys.stdout.flush()
		aws_c.execute('alter view maxPower_pb as ' \
			'select deviceMAC, max(power) as maxPower from dat_powerblade force index (devTimePower) ' \
			'where deviceMAC=\'' + query_dev + '\' ' \
			'and timestamp>\'2017-03-01 00:00:00\' ' \
			'and power != 120.13;')

		aws_c.execute('select coalesce(t2.avgPwr, 0) as avgPwr, coalesce(t2.varPwr, 0) as varPwr, ' \
			'coalesce(t2.maxPwr, 0) as maxPwr, coalesce(t2.minPwr, 0) as minPwr, ' \
			't1.count as count, ' \
			'coalesce(t2.count, 0)/t1.count as dutyCycle, ' \
			't3.deviceType ' \
			'from ' \
			'(select count(*) as count ' \
			'from dat_powerblade force index (devTimePower) ' \
			'where deviceMAC=\'' + query_dev + '\' ' \
			'and date(timestamp)=\'' + query_date_str + '\') t1 ' \
			'join ' \
			'(select avg(power) as avgPwr, var_pop(power) as varPwr, max(power) as maxPwr, min(power) as minPwr, ' \
			'count(*) as count ' \
			'from dat_powerblade force index (devTimePower) ' \
			'where deviceMAC=\'' + query_dev + '\' ' \
			'and power>(select case when maxPower>10 then 0.1*maxPower else 0.5*maxPower end from maxPower_pb) ' \
			'and date(timestamp)=\'' + query_date_str + '\') t2 ' \
			'join (select deviceType from valid_powerblades_no1 ' \
			'where deviceMAC=\'' + query_dev + '\') t3;')
		avgPower, varPower, maxPower, minPower, devCount, dutyCycle, deviceType = aws_c.fetchall()[0]
		print(str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')
		#print(str(deviceType) + ': Average power = ' + str(avgPower) + ', maxPower = ' + str(maxPower) + ', minPower = ' + str(minPower) + ', dutyCycle = ' + str(dutyCycle))

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

		print(str(totalCt) + ' found in ' + str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')

		#print(str(dat))

		item_start = datetime.utcnow()
		sys.stdout.write('Processing occupancy ... ')
		sys.stdout.flush()

		onThold = 0.2

		if(len(occ_data) > 0):
			# 0 = MAC, 1 = Name, 2 = tsMin, 3 = avgPower, 4 = minMot
			maxPwr = max([x[3] for x in occ_data])
			maxMot = max([x[4] for x in occ_data])
			xcorr_pb = [float(x[3])/float(maxPwr) for x in occ_data]
			xcorr_blink = [float(x[4])/float(maxMot) for x in occ_data]
			p_tot = len(occ_data)
			p_a = len([x for x in occ_data if float(x[3])/float(maxPwr) > onThold])
			p_o = len([x for x in occ_data if float(x[4])/float(maxMot) > onThold])
			p_oa = len([x for x in occ_data if float(x[3])/float(maxPwr) > onThold and float(x[4])/float(maxMot) > onThold])

			if(len(xcorr_pb) > 1 and max(xcorr_pb) > 0 and max(xcorr_blink) > 0):
				crossCorr = round(numpy.corrcoef(xcorr_blink, xcorr_pb)[0][1], 2)
			else:
				crossCorr = 0

			try:
				pOcc = float(p_o)/p_tot
				pOccGivenPowRaw = float(p_oa)/p_a
			except:
				pOcc = 0
				pOccGivenPowRaw = 0

			if(pOccGivenPowRaw == 0):
				slope = 0
				yint = 0
			elif(pOccGivenPowRaw > pOcc):
				slope = 1/(1 - pOcc)
				yint = pOcc/(pOcc-1)
			else:
				slope = 1/pOcc
				yint = -1

			pOccGivenPow = round(slope * pOccGivenPowRaw + yint, 2)
		else:
			crossCorr = 'NULL'
			pOccGivenPow = 'NULL'

		print('Crosscorr: ' + str(crossCorr) + ' and P(o|a): ' + str(pOccGivenPow) + ' found in ' + str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')

		total_complete += 1
		print('\nTotal elapsed time: ' + str(chop_microseconds(datetime.utcnow() - script_start)))
		print(str(round(100*float(total_complete)/total_scope,2)) + ' pct complete (' + str(dev_complete) + '/' + str(dev_scope) + ' devices)')
		print('Remaining time: ' + str(chop_microseconds(((datetime.utcnow() - script_start)*total_scope/total_complete)-(datetime.utcnow() - script_start))) + '\n')

		if(totalCt > 0): 
			aws_c.execute('insert into dat_occ_vector (dayst, deviceMAC, ' \
				'avgPwr, varPwr, maxPwr, minPwr, count, duty, ' \
				'crossCorr, pOcc, ' \
				'ct5, spk5, ct10, spk10, ct15, spk15, ' \
				'ct25, spk25, ct50, spk50, ct75, spk75, ' \
				'ct100, spk100, ct150, spk150, ct250, spk250, ' \
				'ct500, spk500, ' \
				'deviceType) ' \
				'values (\'' + str(query_date_str) + '\', \'' + query_dev + '\', ' + \
				str(round(avgPower,6)) + ', ' + str(round(varPower,6)) + ', ' + str(round(maxPower,2)) + ', ' + str(round(minPower,2)) + ', ' + \
				str(devCount) + ', ' + str(dutyCycle) + ', ' + \
				str(crossCorr) + ', ' + str(pOccGivenPow) + ', ' + \
				str(dat['5'][0]) + ', ' + str(dat['5'][1]) + ', ' + str(dat['10'][0]) + ', ' + str(dat['10'][1]) + ', ' + str(dat['15'][0]) + ', ' + str(dat['15'][1]) + ', ' + \
				str(dat['25'][0]) + ', ' + str(dat['25'][1]) + ', ' + str(dat['50'][0]) + ', ' + str(dat['50'][1]) + ', ' + str(dat['75'][0]) + ', ' + str(dat['75'][1]) + ', ' + \
				str(dat['100'][0]) + ', ' + str(dat['100'][1]) + ', ' + str(dat['150'][0]) + ', ' + str(dat['150'][1]) + ', ' + str(dat['250'][0]) + ', ' + str(dat['250'][1]) + ', ' + \
				str(dat['500'][0]) + ', ' + str(dat['500'][1]) + ', ' + \
				'\'' + str(deviceType) + '\');')
			aws_db.commit()

		query_date = query_date + timedelta(days=1)


			
