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



# Processes:
processes = [

	['wkb_occ', 
		'select * from mr_dat_occ_vector ' \
			'where duty!=0 and ' \
			'deviceMAC not in (select * from vector_reject);'
	],

	['wkb_occ_train', 
		'select * from mr_dat_occ_vector ' \
			'where duty!=0 ' \
			'and deviceMAC not in (select * from vector_test) ' \
			'and deviceMAC not in (select * from vector_reject);'
	],

	['wkb_occ_test',
		'select * from mr_dat_occ_vector ' \
			'where duty!=0 ' \
			'and deviceMAC in (select * from vector_test);'
	],

	['wkb_occ_train_small',
		'select * from mr_dat_occ_vector ' \
			'where duty!=0 ' \
			'and deviceMAC not in (select * from vector_test) ' \
			'and deviceMAC not in (select * from vector_reject) ' \
			'and deviceType in (select * from id_fewcats);'
	],

	['wkb_occ_test_small',
		'select * from mr_dat_occ_vector ' \
			'where duty!=0 ' \
			'and deviceMAC in (select * from vector_test) ' \
			'and deviceType in (select * from id_fewcats);'
	]
]


for process in processes:

	label = process[0]
	query = process[1]

	print('Querying for ' + label)

	aws_c.execute(query)
	results = aws_c.fetchall()

	# Generate type list
	total_types = ['{']
	for data in results:
		if(data[-1] not in total_types):
			total_types.append('\"')
			total_types.append(data[-1])
			total_types.append('\"')
			total_types.append(',')
	total_types[-1] = '}'
	typeStr = ''.join(total_types)

	# Create arff file for Weka for all devices
	arff = open(label + '.arff', 'w')

	arff.write('@relation ' + label + '\n\n')

	arff.write('@attribute avgPwr numeric\n')
	arff.write('@attribute varPwr numeric\n')
	arff.write('@attribute maxPwr numeric\n')
	arff.write('@attribute minPwr numeric\n')
	arff.write('@attribute count numeric\n')
	arff.write('@attribute dutyCycle numeric\n')
	arff.write('@attribute crossCorr numeric\n')
	arff.write('@attribute pOcc numeric\n')
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
	arff.write('@attribute deviceType ' + typeStr + '\n\n')

	arff.write('@data\n')

	for data in results:
		dataStr = []
		for idx, datItem in enumerate(data):
			if(idx > 2):
				if datItem == None:
					datItem = 0
				dataStr.append(str(datItem))
				dataStr.append(',')
		dataStr[-2] = '"' + dataStr[-2] + '"'
		dataStr[-1] = '\n'

		dataStr = ''.join(dataStr)
		arff.write(dataStr)

	arff.write('\n')
	arff.close()












