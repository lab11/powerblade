#!/usr/bin/env python

import mylogin
import MySQLdb
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
# aws_c.execute('select deviceMAC from valid_powerblades where location in (3, 5, 6) ' \
aws_c.execute('select deviceMAC from valid_powerblades where location in (0) ' \
	'and deviceType in (select * from id_categories);')
device_list = aws_c.fetchall()
devList = [i[0] for i in device_list]
print(str((datetime.utcnow() - item_start).total_seconds()) + ' seconds')

# First query device is the first device
devI = 0
query_dev = devList[devI]
devI += devI


# Set up start and end times
# start_date = datetime.strptime('2017-03-01', '%Y-%m-%d')
# end_date = datetime.strptime('2017-04-26', '%Y-%m-%d')
start_date = datetime.strptime('2017-03-10', '%Y-%m-%d')
end_date = datetime.strptime('2017-04-17', '%Y-%m-%d')

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



for query_dev in devList:

	query_date = start_date

	dev_complete += 1

	while query_date <= end_date:

		query_date_str = query_date.strftime('%Y-%m-%d')

		item_start = datetime.utcnow()
		sys.stdout.write('Pulling vector data for ' + query_dev + ' on ' + query_date_str + ' ... ')
		sys.stdout.flush()
		aws_c.execute('select * from mr_dat_vector ' \
			'where deviceMAC=\'' + query_dev + '\' and date(dayst)=\'' + query_date_str + '\';')
		vector_data = aws_c.fetchall()
		print(str(round((datetime.utcnow() - item_start).total_seconds(),2)) + ' seconds')

		if(len(vector_data) > 0):
			vector_data = vector_data[0]
		else:
			print('No data\n')
			total_complete += 1
			query_date = query_date + timedelta(days=1)
			continue

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
		sys.stdout.write('Processing vectors ... ')
		sys.stdout.flush()

		avgPower = vector_data[3]
		varPower = vector_data[4]
		maxPower = vector_data[5]
		minPower = vector_data[6]
		devCount = vector_data[7]
		dutyCycle = vector_data[8]

		dat = {}
		dat['5'] = [vector_data[9],vector_data[10]]
		dat['10'] = [vector_data[11],vector_data[12]]
		dat['15'] = [vector_data[13],vector_data[14]]
		dat['25'] = [vector_data[15],vector_data[16]]
		dat['50'] = [vector_data[17],vector_data[18]]
		dat['75'] = [vector_data[19],vector_data[20]]
		dat['100'] = [vector_data[21],vector_data[22]]
		dat['150'] = [vector_data[23],vector_data[24]]
		dat['250'] = [vector_data[25],vector_data[26]]
		dat['500'] = [vector_data[27],vector_data[28]]

		deviceType = vector_data[29];

		totalCt = sum([dat[binSize][0] for binSize in dat])

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
			if maxPwr > 0 and maxMot > 0:
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
				crossCorr = 0
				pOccGivenPow = 0
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

print('\nTotal elapsed time: ' + str(chop_microseconds(datetime.utcnow() - script_start)))
print(str(round(100*float(total_complete)/total_scope,2)) + ' pct complete (' + str(dev_complete) + '/' + str(dev_scope) + ' devices)')
print('Remaining time: ' + str(chop_microseconds(((datetime.utcnow() - script_start)*total_scope/total_complete)-(datetime.utcnow() - script_start))) + '\n')
			
