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



total_data = {}
aws_c.execute('select testMAC from id_dev_corr group by testMAC;')
devList = [x[0] for x in aws_c.fetchall()]
for dev in devList:
	total_data[dev] = {}



id_cats = ['Computer Monitor', 'Coffee maker', 'Television', 'Blowdryer', 'Toaster', 'Fridge', 'Microwave', 'Phone charger', 
	'Curling iron', 'Lamp', 'Fan', 'Laptop computer', 'Exterior lighting', 'Router/Modem', 'Cable Box', 'Blender']
for dev in total_data:
	for category in id_cats:
		total_data[dev][category] = [[], []]



aws_c.execute('select * from id_dev_corr;')
dev_corr = aws_c.fetchall()



current_dev = 0
for mac, actType, corr, occ, ct, locCt in dev_corr:
	if actType == 'Desk lamp' or actType == 'Small lamp/light' or actType == 'Standing lamp':
		actType = 'Lamp'
	elif actType == 'Router' or actType == 'Modem':
		actType = 'Router/Modem'
	total_data[mac][actType][0].append(corr)
	total_data[mac][actType][1].append(occ)



for mac in total_data:
	for actType in total_data[mac]:
		for idx in range(0, len(total_data[mac][actType])):
			if len(total_data[mac][actType][idx]) > 0:
				total_data[mac][actType][idx] = round(sum(total_data[mac][actType][idx])/len(total_data[mac][actType][idx]), 2)
			else:
				total_data[mac][actType][idx] = 0



# # Print header
# for mac in total_data:
# 	printStr = '\t\t'
# 	for actType in total_data[mac]:
# 		printStr += actType + '\t'
# 	print(printStr)



# # Print correlation
# for mac in total_data:
# 	printStr = mac + '\t'
# 	for actType in total_data[mac]:
# 		printStr += str(round(total_data[mac][actType][0],2)) + '\t'
# 	print(printStr)



# # Print header
# print('\n')
# for mac in total_data:
# 	printStr = '\t\t'
# 	for actType in total_data[mac]:
# 		printStr += actType + '\t'
# 	print(printStr)



# # Print correlation
# for mac in total_data:
# 	printStr = mac + '\t'
# 	for actType in total_data[mac]:
# 		printStr += str(round(total_data[mac][actType][1],2)) + '\t'
# 	print(printStr)



for mac in total_data:
	aws_c.execute('insert into dat_inter_vector (deviceMAC, ' \
		'computer_monitor, coffee_maker, television, blowdryer, toaster, fridge, microwave, phone_charger, ' \
		'curling_iron, lamp, fan, laptop_computer, exterior_lighting, router_modem, cable_box, blender) ' \
		'values (\'' + str(mac) + '\', ' + str(total_data[mac]['Computer Monitor'][1]) + ', ' + str(total_data[mac]['Coffee maker'][1]) + ', ' + str(total_data[mac]['Television'][1]) + ', ' + \
		str(total_data[mac]['Blowdryer'][1]) + ', ' + str(total_data[mac]['Toaster'][1]) + ', ' + str(total_data[mac]['Fridge'][1]) + ', ' + \
		str(total_data[mac]['Microwave'][1]) + ', ' + str(total_data[mac]['Phone charger'][1]) + ', ' + str(total_data[mac]['Curling iron'][1]) + ', ' + \
		str(total_data[mac]['Lamp'][1]) + ', ' + str(total_data[mac]['Fan'][1]) + ', ' + str(total_data[mac]['Laptop computer'][1]) + ', ' + \
		str(total_data[mac]['Exterior lighting'][1]) + ', ' + str(total_data[mac]['Router/Modem'][1]) + ', ' + str(total_data[mac]['Cable Box'][1]) + ', ' + \
		str(total_data[mac]['Blender'][1]) + ');')
	aws_db.commit()




