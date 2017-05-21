#!/usr/bin/env python

import mylogin
import MySQLdb
from datetime import datetime, timedelta
import sys
from os.path import expanduser
import numpy

from random import sample

sys.path.append('../plot/')
import pytch

script_start = datetime.utcnow()



def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

def upload_vectors(vectors, success, total_uploading):
	for idx, (dayst, devMAC, avgPwr, varPwr, maxPwr, minPwr, count, duty, crossCorr, pOcc, ct5, \
		spk5, ct10, spk10, ct15, spk15, ct25, spk25, ct50, spk50, ct75, spk75, ct100, \
		spk100, ct150, spk150, ct250, spk250, ct500, spk500, deviceType) in enumerate(vectors):

		if crossCorr == None:
			crossCorr = 'NULL'
		if pOcc == None:
			pOcc = 'NULL'

		aws_c.execute('insert into temp_dat_occ_vector_occ (dayst, deviceMAC, ' \
			'avgPwr, varPwr, maxPwr, minPwr, count, duty, ' \
			'crossCorr, pOcc, ' \
			'ct5, spk5, ct10, spk10, ct15, spk15, ' \
			'ct25, spk25, ct50, spk50, ct75, spk75, ' \
			'ct100, spk100, ct150, spk150, ct250, spk250, ' \
			'ct500, spk500, ' \
			'deviceType) ' \
			'values (\'' + str(dayst) + '\', \'' + devMAC + '\', ' + \
			str(avgPwr) + ', ' + str(varPwr) + ', ' + str(maxPwr) + ', ' + str(minPwr) + ', ' + \
			str(count) + ', ' + str(duty) + ', ' + \
			str(crossCorr) + ', ' + str(pOcc) + ', ' + \
			str(ct5) + ', ' + str(spk5) + ', ' + str(ct10) + ', ' + str(spk10) + ', ' + str(ct15) + ', ' + str(spk15) + ', ' + \
			str(ct25) + ', ' + str(spk25) + ', ' + str(ct50) + ', ' + str(spk50) + ', ' + str(ct75) + ', ' + str(spk75) + ', ' + \
			str(ct100) + ', ' + str(spk100) + ', ' + str(ct150) + ', ' + str(spk150) + ', ' + str(ct250) + ', ' + str(spk250) + ', ' + \
			str(ct500) + ', ' + str(spk500) + ', ' + \
			'\'' + str(deviceType) + '\');')
		aws_db.commit()

		success += 1

		duration = chop_microseconds(datetime.utcnow() - script_start)
		remaining = chop_microseconds(((datetime.utcnow() - script_start)*total_uploading/success)-(datetime.utcnow() - script_start))

		sys.stdout.write('Filling ' + deviceType + ' - ' + str(round(100*float(success)/total_uploading,2)) + ' pct complete in ' + \
			str(duration) + ', ' + str(remaining) + ' remaining                          \r')

	return success



# Set up connection
aws_login = mylogin.get_login_info('aws')
aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
aws_c = aws_db.cursor()



# userInput = pytch.input_loop('\nWarning: This will overwrite the contens of temp_dat_occ_vector. Cancel? (y/n): ')
# if userInput == 'y':
# 	exit()


# # Erase the target table
# print("Erasing...")
# aws_c.execute('delete from temp_dat_occ_vector where id>1;')
# aws_c.fetchall()
# exit()



# Get list of categories
aws_c.execute('select deviceType, count(*) as count from mr_dat_occ_vector where crossCorr is not null group by deviceType order by count desc;')
typeList = aws_c.fetchall()

maxVectors = 125

success = 0
total_uploading = sum([min(maxVectors, x[1]) for x in typeList])
print('Total uploading: ' + str(total_uploading) + ' (' + str(len(typeList)) + ' categories, ' + str(maxVectors) + ' maxVal)')




for devType, count in typeList:
	#print('Filling ' + devType)
	new_total = 0

	aws_c.execute('select * from mr_dat_occ_vector where crossCorr is not null and deviceType=\'' + devType + '\';')
	vectors = aws_c.fetchall()

	if count > maxVectors:
		success = upload_vectors(sample(vectors, maxVectors), success, total_uploading)
	else:
		success = upload_vectors(vectors, success, total_uploading)

	print('')



