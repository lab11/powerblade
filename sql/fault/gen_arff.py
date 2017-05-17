#!/usr/bin/env python

import mylogin
import MySQLdb
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




aws_c.execute('select deviceName from mr_dat_fault_vector group by deviceName;')
devNames = aws_c.fetchall()
devNames = [x[0] for x in devNames]
for devName in devNames:

	process = 'select * from mr_dat_fault_vector where deviceName=\"' + devName + '\";'

	print('Querying for ' + devName)

	aws_c.execute(process)
	results = aws_c.fetchall()

	# Create arff file for Weka for all devices
	arff = open(devName + '.arff', 'w')

	arff.write('@relation ' + devName + '\n\n')

	arff.write('@attribute avgPwr numeric\n')
	arff.write('@attribute varPwr numeric\n')
	arff.write('@attribute maxPwr numeric\n')
	arff.write('@attribute minPwr numeric\n')
	arff.write('@attribute ct5 numeric\n')
	arff.write('@attribute spk5 numeric\n')
	arff.write('@attribute ct10 numeric\n')
	arff.write('@attribute spk10 numeric\n')
	arff.write('@attribute ct15 numeric\n')
	arff.write('@attribute spk15 numeric\n')
	arff.write('@attribute ct25 numeric\n')
	arff.write('@attribute spk25 numeric\n')
	arff.write('@attribute ct50 numeric\n')
	arff.write('@attribute spk50 numeric\n')
	arff.write('@attribute ct75 numeric\n')
	arff.write('@attribute spk75 numeric\n')
	arff.write('@attribute ct100 numeric\n')
	arff.write('@attribute spk100 numeric\n')
	arff.write('@attribute ct150 numeric\n')
	arff.write('@attribute spk150 numeric\n')
	arff.write('@attribute ct250 numeric\n')
	arff.write('@attribute spk250 numeric\n')
	arff.write('@attribute ct500 numeric\n')
	arff.write('@attribute spk500 numeric\n')
	arff.write('@attribute broken {\"0\", \"1\", \"2\", \"3\"}\n\n')

	arff.write('@data\n')

	for data in results:
		dataStr = []
		for idx, datItem in enumerate(data):
			if(idx > 4):
				dataStr.append(str(datItem))
				dataStr.append(',')
		if dataStr[-2] != '0':
			dataStr[-2] = '"1"'
		else:
			dataStr[-2] = '"0"'
		dataStr[-1] = '\n'
		dataStr = ''.join(dataStr)

		arff.write(dataStr)

	arff.write('\n')
	arff.close()












