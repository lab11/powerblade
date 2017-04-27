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

# Set up connection
aws_login = mylogin.get_login_info('aws')
aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
aws_c = aws_db.cursor()


# Get list of deviceTypes to query
aws_c.execute('select * from id_categories order by deviceType asc;')
type_list = aws_c.fetchall()
typeList = [i[0] for i in type_list]


# Data structure for storing all of the data
total_data = []

script_scope = len(typeList) * 2
script_complete = 0

script_start = datetime.utcnow()

devTest = []
devTrain = []

for devType in typeList:

	sys.stdout.write('Querying for ' + devType + ' ... ')
	sys.stdout.flush()
	item_start = datetime.utcnow()

	aws_c.execute('alter view maxPower_pb as ' \
		'select deviceMAC, max(power) as maxPower from dat_powerblade force index (devTimePower) ' \
		'where timestamp>\'2017-03-01 00:00:00\' ' \
		'and power != 120.13 ' \
		'and deviceMAC in (select deviceMAC from valid_powerblades ' \
			'where deviceType in (\'' + devType + '\') ' \
			'and location!=1) ' \
		'group by deviceMAC;')

	aws_c.execute('select t1.dayst, t1.deviceMAC, ' \
		'coalesce(t2.avgPwr, 0) as avgPwr, coalesce(t2.varPwr, 0) as varPwr, coalesce(t2.maxPwr, 0) as maxPwr, coalesce(t2.minPwr, 0) as minPwr, ' \
		't1.count as count, ' \
		'coalesce(t2.count, 0)/t1.count as dutyCycle, ' \
		'coalesce(t4.ct5, 0) as ct5, coalesce(t4.spk5, 0) as spk5, coalesce(t4.ct10, 0) as ct10, coalesce(t4.spk10, 0) as spk10, ' \
		'coalesce(t4.ct15, 0) as ct15, coalesce(t4.spk15, 0) as spk15, coalesce(t4.ct25, 0) as ct25, coalesce(t4.spk25, 0) as spk25, ' \
		'coalesce(t4.ct50, 0) as ct50, coalesce(t4.spk50, 0) as spk50, coalesce(t4.ct75, 0) as ct75, coalesce(t4.spk75, 0) as spk75, ' \
		'coalesce(t4.ct100, 0) as ct100, coalesce(t4.spk100, 0) as spk100, coalesce(t4.ct150, 0) as ct150, coalesce(t4.spk150, 0) as spk150, ' \
		'coalesce(t4.ct250, 0) as ct250, coalesce(t4.spk250, 0) as spk250, coalesce(t4.ct500, 0) as ct500, coalesce(t4.spk500, 0) as spk500, ' \
		't3.deviceType ' \
		'from ' \
		'(select ROUND(unix_timestamp(timestamp)/(24*60*60)) as timekey, date(timestamp) as dayst, ' \
		'deviceMAC, ' \
		'max(power) as maxPwr, ' \
		'count(*) as count ' \
		'from dat_powerblade ' \
		'where deviceMAC in (select deviceMAC from valid_powerblades ' \
			'where deviceType in (\'' + devType + '\') ' \
			'and location!=1) ' \
		'and timestamp>\'2017-03-01 00:00:00\' ' \
		'group by deviceMAC, timekey) t1 ' \
		'left join ' \
		'(select ROUND(unix_timestamp(timestamp)/(24*60*60)) as timekey, date(timestamp) as dayst, ' \
		'deviceMAC, ' \
		'avg(power) as avgPwr, var_pop(power) as varPwr, max(power) as maxPwr, min(power) as minPwr, ' \
		'count(*) as count ' \
		'from dat_powerblade tpa ' \
		'where deviceMAC in (select deviceMAC from valid_powerblades ' \
			'where deviceType in (\'' + devType + '\') ' \
    		'and location!=1) ' \
		'and power>(select case when maxPower>10 then 0.1*maxPower else 0.5*maxPower end from maxPower_pb tpb where tpa.deviceMAC=tpb.deviceMAC) ' \
		'and timestamp>\'2017-03-01 00:00:00\' ' \
		'group by deviceMAC, timekey) t2 ' \
		'on t1.timekey=t2.timekey and t1.deviceMAC=t2.deviceMAC ' \
		'left join ' \
		'(select * from valid_powerblades where location!=1) t3 ' \
		'on t1.deviceMAC=t3.deviceMAC ' \
		'left join ' \
		'mr_dat_delta t4 ' \
		'on t1.deviceMAC=t4.deviceMAC and t1.dayst=t4.dayst ' \
		'where t1.count>100;')
	devData = aws_c.fetchall()

	these_devices = {}
	maxDev = 0
	maxVal = 0
	for data in devData:
		if data[1] in these_devices:
			these_devices[data[1]] += 1
		else:
			these_devices[data[1]] = 1
		if these_devices[data[1]] > maxVal:
			maxDev = data[1]
			maxVal = these_devices[data[1]]

	devTotal = len(these_devices)
	if devTotal == 1:
		numDevTest = 0
		numDevtrain = 1
	else:
		numDevTest = max(1, floor(devTotal*.2))
		numDevTrain = devTotal - numDevTest

	sys.stdout.write(str(chop_microseconds(datetime.utcnow() - item_start)) + ' ... ')

	script_complete += 1
	sys.stdout.write(str(round(100*float(script_complete)/script_scope,2)) + ' pct complete ... ')

	sys.stdout.write(str(chop_microseconds(datetime.utcnow() - script_start)) + ' total ... ')
	
	if(script_complete == script_scope):
		remaining = 0
	else:
		remaining = chop_microseconds(((datetime.utcnow() - script_start)*script_scope/script_complete)-(datetime.utcnow() - script_start))
	sys.stdout.write(str(remaining) + ' remaining\n')

	sys.stdout.flush()

	total_data.extend(devData)

	sys.stdout.write('Uploading to AWS ... ')
	sys.stdout.flush()
	item_start = datetime.utcnow()

	for data in devData:
		aws_c.execute
		exeStr = ['insert into dat_vector (dayst, deviceMAC, ' \
			'avgPwr, varPwr, maxPwr, minPwr, count, duty, ' \
			'ct5, spk5, ct10, spk10, ct15, spk15, ' \
			'ct25, spk25, ct50, spk50, ct75, spk75, ' \
			'ct100, spk100, ct150, spk150, ct250, spk250, ' \
			'ct500, spk500, deviceType) ' \
			'values (']
		for datItem in data:
			if is_number(datItem):
				exeStr.append(str(round(datItem,6)))
			else:
				exeStr.append('\'')
				exeStr.append(str(datItem))
				exeStr.append('\'')
			exeStr.append(',')
		exeStr[-1] = ');'
		exeStr = ''.join(exeStr)

		aws_c.execute(exeStr)
		aws_db.commit()

	sys.stdout.write(str(chop_microseconds(datetime.utcnow() - item_start)) + ' ... ')

	script_complete += 1
	sys.stdout.write(str(round(100*float(script_complete)/script_scope,2)) + ' pct complete ... ')

	sys.stdout.write(str(chop_microseconds(datetime.utcnow() - script_start)) + ' total ... ')
	
	if(script_complete == script_scope):
		remaining = 0
	else:
		remaining = chop_microseconds(((datetime.utcnow() - script_start)*script_scope/script_complete)-(datetime.utcnow() - script_start))
	sys.stdout.write(str(remaining) + ' remaining\n')

	sys.stdout.flush()
				

	# print(str(devTotal) + ' total devices (' + str(numDevTrain) + ' train, ' + str(numDevTest) + ' test)')

	# print(these_devices)

	# sorted_list = sorted([x for x in these_devices], key=lambda x: these_devices[x], reverse=True)

	# idDev = 0

	# while(idDev < devTotal):
	# 	dev = sorted_list[idDev]
	# 	print('train: ' + str(idDev) + ' ' + str(dev))
	# 	devTrain.append(dev)
	# 	idDev += 1

	# 	if(idDev/2 < numDevTest):
	# 		dev = sorted_list[idDev]
	# 		print('test: ' + str(idDev) + ' ' + str(dev))
	# 		devTest.append(dev)
	# 		idDev += 1
		

	# for idx, dev in enumerate(these_devices):
	# 	if idx < numDevTest:
	# 		print('test: ' + str(idx) + ' ' + str(dev))
	# 		devTest.append(dev)
	# 	else:
	# 		print('train: ' + str(idx) + ' ' + str(dev))
	# 		devTrain.append(dev)


# # Generate type list
# total_types = ['{']
# for devType in typeList:
# 	total_types.append('"')
# 	total_types.append(devType)
# 	total_types.append('"')
# 	total_types.append(',')
# total_types[-1] = '}'
# typeStr = ''.join(total_types)

# # Generate date list
# total_dates = ['{']
# for data in total_data:
# 	if(str(data[0]) not in total_dates):
# 		total_dates.append(str(data[0]))
# 		total_dates.append(',')
# total_dates[-1] = '}'
# dateStr = ''.join(total_dates)

# # Generate device list
# total_devices = ['{']
# for data in total_data:
# 	if(data[1] not in total_devices):
# 		total_devices.append(data[1])
# 		total_devices.append(',')
# total_devices[-1] = '}'
# devStr = ''.join(total_devices)

# # Create arff file for Weka for all devices
# arff = open('all_devices.arff', 'w')

# arff.write('@relation all_devices\n\n')

# arff.write('@attribute dayst ' + dateStr + '\n')
# arff.write('@attribute deviceMAC ' + devStr + '\n')
# arff.write('@attribute avgPwr numeric\n')
# arff.write('@attribute varPwr numeric\n')
# arff.write('@attribute maxPwr numeric\n')
# arff.write('@attribute minPwr numeric\n')
# arff.write('@attribute count numeric\n')
# arff.write('@attribute dutyCycle numeric\n')
# arff.write('@attribute ct5 numeric\n')
# arff.write('@attribute spk5 numeric\n')
# arff.write('@attribute ct10 numeric\n')
# arff.write('@attribute spk10 numeric\n')
# arff.write('@attribute ct15 numeric\n')
# arff.write('@attribute spk15 numeric\n')
# arff.write('@attribute ct25 numeric\n')
# arff.write('@attribute spk25 numeric\n')
# arff.write('@attribute ct50 numeric\n')
# arff.write('@attribute spk50 numeric\n')
# arff.write('@attribute ct75 numeric\n')
# arff.write('@attribute spk75 numeric\n')
# arff.write('@attribute ct100 numeric\n')
# arff.write('@attribute spk100 numeric\n')
# arff.write('@attribute ct150 numeric\n')
# arff.write('@attribute spk150 numeric\n')
# arff.write('@attribute ct250 numeric\n')
# arff.write('@attribute spk250 numeric\n')
# arff.write('@attribute ct500 numeric\n')
# arff.write('@attribute spk500 numeric\n')
# arff.write('@attribute deviceType ' + typeStr + '\n\n')

# arff.write('@data\n')

# for data in total_data:
# 	dataStr = []
# 	for datItem in data:
# 		dataStr.append(str(datItem))
# 		dataStr.append(',')
# 	dataStr[-2] = '"' + dataStr[-2] + '"'
# 	dataStr[-1] = '\n'
# 	dataStr = ''.join(dataStr)

# 	arff.write(dataStr)

# arff.write('\n')
# arff.close()

# # Create arff files for test and train datasets for unsees devices
# arff_train = open('train.arff', 'w')

# arff_train.write('@relation train\n\n')

# arff_train.write('@attribute dayst ' + dateStr + '\n')
# arff_train.write('@attribute deviceMAC ' + devStr + '\n')
# arff_train.write('@attribute avgPwr numeric\n')
# arff_train.write('@attribute varPwr numeric\n')
# arff_train.write('@attribute maxPwr numeric\n')
# arff_train.write('@attribute minPwr numeric\n')
# arff_train.write('@attribute count numeric\n')
# arff_train.write('@attribute dutyCycle numeric\n')
# arff_train.write('@attribute ct5 numeric\n')
# arff_train.write('@attribute spk5 numeric\n')
# arff_train.write('@attribute ct10 numeric\n')
# arff_train.write('@attribute spk10 numeric\n')
# arff_train.write('@attribute ct15 numeric\n')
# arff_train.write('@attribute spk15 numeric\n')
# arff_train.write('@attribute ct25 numeric\n')
# arff_train.write('@attribute spk25 numeric\n')
# arff_train.write('@attribute ct50 numeric\n')
# arff_train.write('@attribute spk50 numeric\n')
# arff_train.write('@attribute ct75 numeric\n')
# arff_train.write('@attribute spk75 numeric\n')
# arff_train.write('@attribute ct100 numeric\n')
# arff_train.write('@attribute spk100 numeric\n')
# arff_train.write('@attribute ct150 numeric\n')
# arff_train.write('@attribute spk150 numeric\n')
# arff_train.write('@attribute ct250 numeric\n')
# arff_train.write('@attribute spk250 numeric\n')
# arff_train.write('@attribute ct500 numeric\n')
# arff_train.write('@attribute spk500 numeric\n')
# arff_train.write('@attribute deviceType ' + typeStr + '\n\n')

# arff_train.write('@data\n')


# arff_test = open('test.arff', 'w')

# arff_test.write('@relation test\n\n')

# arff_test.write('@attribute dayst ' + dateStr + '\n')
# arff_test.write('@attribute deviceMAC ' + devStr + '\n')
# arff_test.write('@attribute avgPwr numeric\n')
# arff_test.write('@attribute varPwr numeric\n')
# arff_test.write('@attribute maxPwr numeric\n')
# arff_test.write('@attribute minPwr numeric\n')
# arff_test.write('@attribute count numeric\n')
# arff_test.write('@attribute dutyCycle numeric\n')
# arff_test.write('@attribute ct5 numeric\n')
# arff_test.write('@attribute spk5 numeric\n')
# arff_test.write('@attribute ct10 numeric\n')
# arff_test.write('@attribute spk10 numeric\n')
# arff_test.write('@attribute ct15 numeric\n')
# arff_test.write('@attribute spk15 numeric\n')
# arff_test.write('@attribute ct25 numeric\n')
# arff_test.write('@attribute spk25 numeric\n')
# arff_test.write('@attribute ct50 numeric\n')
# arff_test.write('@attribute spk50 numeric\n')
# arff_test.write('@attribute ct75 numeric\n')
# arff_test.write('@attribute spk75 numeric\n')
# arff_test.write('@attribute ct100 numeric\n')
# arff_test.write('@attribute spk100 numeric\n')
# arff_test.write('@attribute ct150 numeric\n')
# arff_test.write('@attribute spk150 numeric\n')
# arff_test.write('@attribute ct250 numeric\n')
# arff_test.write('@attribute spk250 numeric\n')
# arff_test.write('@attribute ct500 numeric\n')
# arff_test.write('@attribute spk500 numeric\n')
# arff_test.write('@attribute deviceType ' + typeStr + '\n\n')

# arff_test.write('@data\n')


# for data in total_data:
# 	dataStr = []
# 	for datItem in data:
# 		dataStr.append(str(datItem))
# 		dataStr.append(',')
# 	dataStr[-2] = '"' + dataStr[-2] + '"'
# 	dataStr[-1] = '\n'
# 	dataStr = ''.join(dataStr)

# 	if data[1] in devTrain:
# 		arff_train.write(dataStr)
# 	else:
# 		arff_test.write(dataStr)

# arff_train.write('\n')
# arff_test.write('\n')
# arff_train.close()
# arff_test.close()








