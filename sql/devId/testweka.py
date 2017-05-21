#!/usr/bin/env python

import mylogin
import MySQLdb
import yagmail
from datetime import datetime, timedelta
import os
import sys
import subprocess
from sh import epstopdf, gnuplot, mkdir, cp, mv
from os.path import expanduser

import copy

sys.path.append('../plot/')
import pytch

from gen_arff_v2 import gen_arff

from math import floor
import math

from numpy import percentile

import itertools

import weka.core.jvm as jvm
from weka.classifiers import Classifier, Evaluation
from weka.core.converters import Loader, Saver
from weka.core.classes import Random

import random as pyrandom

arff_idcol = 2

def chop_microseconds(delta):
    return delta - timedelta(microseconds=delta.microseconds)

def is_number(s):
    try:
        float(s)
        return True
    except:
        return False

def print_conf_matrix(conf_matrix, stream, latex, plusSign, textCol):
	# print header:
	correct = 0
	total = 0
	if latex:
		colStr = '| '
		for col in range(0, len(conf_matrix)):
			colStr += 'c | '
		if textCol:
			colStr += '| c |'
		stream.write('\\begin{' + 'tabular}{' + colStr + '} \\hline \n')
		for idx, name in enumerate(conf_matrix):
			stream.write('$\\hskip 0.7em$' + chr(ord('a') + idx) + '$\\hskip 0.7em$\t')
			if not textCol and (idx+1) == len(conf_matrix):
				stream.write('\\\\ \\hline % & ')
			else:
				stream.write('& ')
		stream.write('$<$- Classified as\t\\\\ \\hline \n')
	else:
		stream.write('\n=== Confusion Matrix ===\n\n')
		for idx, name in enumerate(conf_matrix):
			value = chr(ord('a') + idx)
			stream.write('   ' + str(value))
		stream.write('   <-- classified as\n')
	stream.flush()

	for idx, testName in enumerate(conf_matrix):

		if latex:
			stream.write('\t')
		typeTotal = 0
		typeCorrect = 0
		for idy, predName in enumerate(conf_matrix):
			if predName in conf_matrix[testName]:
				value = conf_matrix[testName][predName]
			else:
				value = 0

			if latex:
				if plusSign:
					if value > 0:
						writeVal = '+' + str(value)
					else:
						writeVal = value
				else:
					writeVal = value
				if predName == testName:
					stream.write('\cellcolor{' + 'goodgreen} ' + str(writeVal) + '\t')
				else:
					stream.write(str(writeVal) + '\t')

				if not textCol and (idy+1) == len(conf_matrix):
					stream.write('\\\\ \\hline % & ')
				else:
					stream.write('& ')
			else:
				if value < 10:
					stream.write('  ')
				elif value < 100:
					stream.write(' ')
				stream.write(' ' + str(value))

			if predName == testName:
				correct += value
				typeCorrect += value
			total += value
			typeTotal += value

		writeStr = str(chr(ord('a') + idx)) + ' = ' + str(testName) + ' - ' + str(round(float(typeCorrect)/typeTotal,2)) + ' correct'
		if latex:
			stream.write(writeStr + '\t\\\\ \\hline \n\t')
		else:
			stream.write(' |   ' + writeStr + '\n')
	
	if latex:
		stream.write('\\end{' + 'tabular}\n')
	stream.flush()

	return correct, total

def sub_conf_matrix(orig, subtract):

	output = {}

	for testName in orig:
		orig_test = orig[testName]
		if testName in subtract:
			sub_test = subtract[testName]
		else:
			sub_test = {}

		output[testName] = {}

		for predName in orig:
			if predName in orig_test:
				orig_val = orig_test[predName]
			else:
				orig_val = 0
			if predName in sub_test:
				sub_val = sub_test[predName]
			else:
				sub_val = 0

			output[testName][predName] = orig_val - sub_val

	return output


item_start = datetime.utcnow()

# Set up connection
aws_login = mylogin.get_login_info('aws')
aws_db = MySQLdb.connect(aws_login['host'], aws_login['user'], aws_login['passwd'], 'powerblade')
aws_c = aws_db.cursor()

query_startDay = datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S')
master_saveDir = os.environ['PB_DATA'] + "/savetest/" + str(query_startDay) + '_classify'
mkdir(master_saveDir)

# Get list of devices:
aws_c.execute('select deviceMAC, count(*) as count from temp_dat_occ_vector_2 ' \
	'where count>0 and duty!=0 and deviceMAC not in (select * from vector_reject) ' \
	'group by deviceMAC;')
devList = [x[0] for x in aws_c.fetchall()]

# Get small list of devices:
aws_c.execute('select deviceMAC, count(*) as count from temp_dat_occ_vector_2 ' \
	'where count>0 and duty!=0 and deviceMAC not in (select * from vector_reject) ' \
	'and deviceMAC in (select * from id_fewcats_mac) '
	'group by deviceMAC;')
smallList = [x[0] for x in aws_c.fetchall()]



jvm.start()
loader = Loader(classname="weka.core.converters.ArffLoader")

total_results = {}
total_conf = open('conf_matrix.txt', 'w')

# days_output = open('numDays.txt', 'w')
# days_to_test = 10

totalDevs = 0
devCount = 0

save_orig = ''
save_subtract = ''

total_devices = 0
total_correct = 0

def print_obsResults(conf_matrix, conf_interval, p_d, p_e, p_e_given_d, successItem, outStream):
	global total_devices
	global total_correct
	finalValue = 0
	outStream.write('\n\n' + str(successItem[0]) + '\n')
	for classEvents in range(1, (len(successItem[1])+1)):
		numerator = p_d[successItem[0]]
		for idx, classInst in enumerate(successItem[1]):
			if idx < classEvents:
				numerator *= p_e_given_d[successItem[0]][classInst]
		demoninator = 0
		for otherName in conf_matrix:
			obsValue = p_d[otherName]
			for idx, classInst in enumerate(successItem[1]):
				if idx < classEvents:
					obsValue *= p_e_given_d[otherName][classInst]
			demoninator += obsValue
		finalValue = numerator/demoninator
		outStream.write(str(classEvents) + '\t' + str(numerator/demoninator) + '\t\"' + str(successItem[0]) + '\"\t\"' + successItem[1][classEvents-1] + '\"\n')
		#print(str(classEvents) + '\t' + str(numerator/demoninator) + '\t\"' + str(successItem[0]) + '\"\t\"' + successItem[1][classEvents-1] + '\"')
	#print('')
	if finalValue > 0.4:
		total_correct += 1
	total_devices += 1

def process_classifier(runType, cls, occ, devList, fewCats, label, subtract):
	global devCount
	global save_orig
	global save_subtract
	conf_matrix = {}

	if occ:
		table = 'temp_dat_occ_vector_occ'
	else:
		table = 'temp_dat_occ_vector_2'

	writeStr = '=========================================================================================\n' + \
		'Running ' + runType + ' classifier for \'' + label + '\''
	sys.stdout.write(writeStr + '\r')
	total_conf.write(writeStr + '\n')
	sys.stdout.flush()

	if runType == 'unseen':
		i = 0
		indiv_results = {}
		for dev in devList:
			devCount += 1
			remaining = chop_microseconds(((datetime.utcnow() - item_start)*totalDevs/devCount)-(datetime.utcnow() - item_start))
			sys.stdout.write('Running ' + runType + ' classifier for \'' + label + '\' - ' + \
				str(round(100*float(devCount)/totalDevs,2)) + ' pct complete (' + str(remaining) + ' remaining)                 \r')
			sys.stdout.flush()

			if fewCats:
				aws_c.execute('select * from ' + table + ' ' \
					'where duty!=0 and deviceMAC not in (select * from vector_reject) ' \
					'and deviceMAC in (select * from id_fewcats_mac) '
					'and deviceMAC!=\'' + dev + '\';')
			else:
				aws_c.execute('select * from ' + table + ' ' \
					'where duty!=0 and deviceMAC not in (select * from vector_reject) ' \
					'and deviceMAC!=\'' + dev + '\';')
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

			arff_train = label + '_' + dev + '_train'
			arff_test = label + '_' + dev + '_test'

			gen_arff(arff_train, typeStr, results, occ, arff_idcol)

			if fewCats:
				aws_c.execute('select * from ' + table + ' ' \
					'where duty!=0 and deviceMAC not in (select * from vector_reject) ' \
					'and deviceMAC in (select * from id_fewcats_mac) '
					'and deviceMAC=\'' + dev + '\';')
			else:
				aws_c.execute('select * from ' + table + ' ' \
					'where duty!=0 and deviceMAC not in (select * from vector_reject) ' \
					'and deviceMAC=\'' + dev + '\';')
			gen_arff(arff_test, typeStr, aws_c.fetchall(), occ, arff_idcol)

			train = loader.load_file(arff_train + '.arff')
			train.class_is_last()
			mv(arff_train + '.arff', master_saveDir)
			test = loader.load_file(arff_test + '.arff')
			test.class_is_last()
			mv(arff_test + '.arff', master_saveDir)

			cls.build_classifier(train)

			# output predictions
			testName = ''
			predictions = []
			for index, inst in enumerate(test):
				testName = inst.get_string_value(inst.class_index)
				if testName not in conf_matrix:
					conf_matrix[testName] = {}

				pred = cls.classify_instance(inst)
				# dist = cls.distribution_for_instance(inst)
				# if(pred == inst.get_value(inst.class_index)):
				predName = inst.class_attribute.value(int(pred))
				if predName not in conf_matrix[testName]:
					conf_matrix[testName][predName] = 0
				conf_matrix[testName][predName] += 1
				predictions.append(predName)

			total = 0
			if testName != '':
				for predName in conf_matrix[testName]:
					if predName == testName:
						correct = conf_matrix[testName][predName]
						total += correct
					else:
						total += conf_matrix[testName][predName]

			while (len(predictions) * 2) <= 100:
				predictions += pyrandom.sample(predictions, len(predictions))
			if len(predictions) < 100:
				predictions += pyrandom.sample(predictions, 100 - len(predictions))

			indiv_results[dev] = [testName, pyrandom.sample(predictions, 100)]

			# indiv_results[dev] = [testName, predictions]

			# Prep to print the how-many-days graph
			# days_output.write('\n\n\"' + dev + '\"\n')


			
			#print(str(testName) + ' ' + str(correct) + ' ' + str(total) + ' ' + str(float(correct)/total))

			# i += 1
			# if i == 10:
			# 	break


		correct, total = print_conf_matrix(conf_matrix, sys.stdout, False, False, False)
		correct, total = print_conf_matrix(conf_matrix, total_conf, False, False, False)

		if subtract == 'orig':
			save_orig = copy.deepcopy(conf_matrix)
		elif subtract == 'subtract':
			save_subtract = copy.deepcopy(conf_matrix)

		final_result = round(100*float(correct)/total,2)

		writeStr = '\nCorrectly Classified Instances\t\t' + str(correct) + '\t\t' + str(final_result) + '\n' + \
			'Incorrectly Classified Instances\t' + str(total-correct) + '\t\t' + str(round(100*float(total-correct)/total,2)) + '\n' + \
			'Total Number of Instances\t\t' + str(total) + '\n'
		print(writeStr)
		total_conf.write(writeStr + '\n')

		conf_interval = 10
		total_instances = float(sum([sum([conf_matrix[test][pred] for pred in conf_matrix[test]]) for test in conf_matrix]))

		p_d = {}
		p_e = {}
		p_e_given_d = {}
		for testName in conf_matrix:
			count_d = float(sum([conf_matrix[testName][label] for label in conf_matrix[testName]]))
			p_d[testName] = count_d / total_instances
			p_e[testName] = float(sum([conf_matrix[label][testName] for label in conf_matrix if testName in conf_matrix[label]]) / total_instances)
			p_e_given_d[testName] = {}

			for predName in conf_matrix:
				if predName in conf_matrix[testName]:
					p_e_given_d[testName][predName] = conf_matrix[testName][predName] / count_d
				else:
					p_e_given_d[testName][predName] = 0

		confidence = open('confidence.dat', 'w')
		for testName in conf_matrix:
			confidence.write('\n\n\"' + testName + '\"\n')
			print(testName)

			for classEvents in range(1, (conf_interval+1)):
				numerator = math.pow(p_e_given_d[testName][testName], classEvents) * p_d[testName]
				demoninator = 0
				for otherName in conf_matrix:
					demoninator += math.pow(p_e_given_d[otherName][testName], classEvents) * p_d[otherName]
				confidence.write(str(classEvents) + '\t' + str(numerator/demoninator) + '\n')
				print(str(classEvents) + '\t' + str(numerator/demoninator)) 
			print('')

		for predName in p_e_given_d['Router/Modem']:
			print('P( ' + predName + ' | Router/Modem ):\t' + str(p_e_given_d['Router/Modem'][predName]))

		for predName in p_e_given_d['Cable Box']:
			print('P( ' + predName + ' | Cable Box ):\t' + str(p_e_given_d['Cable Box'][predName]))

		#router = open('router', 'w')
		print('Router Stuff:')
		routerDev = 'Router/Modem'
		lampDev = 'Lamp'
		cableDev = 'Cable Box'
		origClassList = ['Router/Modem', 'Cable Box', 'Lamp', 'Router/Modem', 'Router/Modem', 'Cable Box', 'Router/Modem', 'Lamp', 'Router/Modem']

		classListList =  [['Router/Modem'] + list(listItem) for listItem in set(itertools.permutations(origClassList))]

		classListList = [
			['Router/Modem', 'Router/Modem', 'Lamp', 'Lamp', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Cable Box', 'Router/Modem'],
			['Router/Modem', 'Cable Box', 'Lamp', 'Lamp', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Cable Box', 'Router/Modem'],
			['Router/Modem', 'Router/Modem', 'Lamp', 'Lamp', 'Cable Box', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Cable Box', 'Router/Modem'],
			['Router/Modem', 'Cable Box', 'Lamp', 'Lamp', 'Cable Box', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Cable Box', 'Router/Modem'],
			['Router/Modem', 'Cable Box', 'Router/Modem', 'Lamp', 'Cable Box', 'Router/Modem', 'Router/Modem', 'Lamp', 'Router/Modem', 'Router/Modem'],
			['Router/Modem', 'Router/Modem', 'Router/Modem', 'Lamp', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Lamp', 'Router/Modem', 'Router/Modem'],
			['Router/Modem', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Router/Modem', 'Lamp']
		]

		for idClass, classList in enumerate(classListList):
			print(idClass)
			for classEvents in range(1, (conf_interval+1)):
				numerator_router = p_d[routerDev]
				numerator_lamp = p_d[lampDev]
				numerator_cable = p_d[cableDev]
				for idx, classInst in enumerate(classList):
					if idx < classEvents:
						numerator_router *= p_e_given_d[routerDev][classInst]
						numerator_lamp *= p_e_given_d[lampDev][classInst]
						numerator_cable *= p_e_given_d[cableDev][classInst]
				demoninator = 0
				for otherName in conf_matrix:
					obsValue = p_d[otherName]
					for idx, classInst in enumerate(classList):
						if idx < classEvents:
							obsValue *= p_e_given_d[otherName][classInst]
					demoninator += obsValue
				print(str(classEvents) + '\t' + str(numerator_router/demoninator) + '\t' + str(numerator_lamp/demoninator) + '\t' + str(numerator_cable/demoninator) + '\t\"' + classList[classEvents-1]) + '\"'
			print('')


		eachDev = open('indiv_results.dat', 'w')
		for devItem in indiv_results:
			print_obsResults(conf_matrix, conf_interval, p_d, p_e, p_e_given_d, indiv_results[devItem], eachDev)
		print('')
		print('total devices: ' + str(len(indiv_results)))
		print('total devices: ' + str(total_devices))
		print('total correct: ' + str(total_correct))


	elif runType == 'seen':
		if fewCats:
			aws_c.execute('select * from ' + table + ' ' \
				'where duty!=0 and deviceMAC not in (select * from vector_reject) ' \
				'and deviceMAC in (select * from id_fewcats_mac);')
		else:
			aws_c.execute('select * from ' + table + ' ' \
				'where duty!=0 and deviceMAC not in (select * from vector_reject);')
		results = aws_c.fetchall()

		devCount += 1
		remaining = chop_microseconds(((datetime.utcnow() - item_start)*totalDevs/devCount)-(datetime.utcnow() - item_start))
		sys.stdout.write('Running ' + runType + ' classifier for \'' + label + '\' - ' + \
			str(round(100*float(devCount)/totalDevs,2)) + ' pct complete (' + str(remaining) + ' remaining)                 \r')
		sys.stdout.flush()

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

		arff_file = label + '_train'

		gen_arff(arff_file, typeStr, results, occ, arff_idcol)

		train = loader.load_file(arff_file + '.arff')
		train.class_is_last()
		mv(arff_file + '.arff', master_saveDir)

		cls.build_classifier(train)

		evl = Evaluation(train)
		evl.crossvalidate_model(cls, train, 10, Random(1))

		print('\n')
		#print(evl.percent_correct)
		#print(evl.class_details())
		print(evl.matrix())
		total_conf.write('\n' + evl.matrix())
		print(evl.summary())
		total_conf.write(evl.summary() + '\n')

		final_result = round(evl.percent_correct, 2)

	else:
		success = []
		for startDev in devList:
			for changeToDev in devList:
				if startDev != changeToDev:
					devCount += 1
					remaining = chop_microseconds(((datetime.utcnow() - item_start)*totalDevs/devCount)-(datetime.utcnow() - item_start))
					sys.stdout.write('Running ' + runType + ' classifier for \'' + label + '\' - ' + \
						str(round(100*float(devCount)/totalDevs,2)) + ' pct complete (' + str(remaining) + ' remaining)                 \r')
					sys.stdout.flush()
					
					aws_c.execute('select * from temp_dat_occ_vector_2 ' \
						'where duty!=0 and deviceMAC in (\'' + startDev + '\',\'' + changeToDev + '\');')
					results = [x[:-1] + (x[1],) for x in aws_c.fetchall()]	# Class label is just the deviceMAC

					if len(results) > 10:

						# Generate type list
						typeStr = '{' + startDev + ',' + changeToDev + '}'

						arff_file = label + '_' + startDev + '_' + changeToDev + '_train'

						gen_arff(arff_file, typeStr, results, occ, arff_idcol)

						train = loader.load_file(arff_file + '.arff')
						train.class_is_last()
						mv(arff_file + '.arff', master_saveDir)

						cls.build_classifier(train)

						evl = Evaluation(train)
						evl.crossvalidate_model(cls, train, 10, Random(1))

						print('\n')
						#print(evl.percent_correct)
						#print(evl.class_details())
						print(evl.matrix())
						total_conf.write('\n' + evl.matrix())
						print(evl.summary())
						total_conf.write(evl.summary() + '\n')

						success.append(evl.percent_correct)

		if len(success) > 0:
			final_result = [sum(success)/len(success), percentile(success, 5), percentile(success, 10), percentile(success, 95)]
		else:
			final_result = False

	if label in total_results:
		print('Warning label ' + label + ' exists twice, overwriting...')
	if final_result != False:
		total_results[label] = final_result

process_list = []
def preprocess_classifier(runType, cls, occ, thisDevList, fewcats, label, subtract):
	global totalDevs
	if runType == 'seen':
		totalDevs += 1
	elif runType == 'unseen':
		totalDevs += len(thisDevList)
	else:
		totalDevs += len(thisDevList) * len(thisDevList)
	process_list.append([runType, cls, occ, thisDevList, fewcats, label, subtract])


clsTree = Classifier(classname="weka.classifiers.trees.J48", options=["-C", "0.25", "-M", "2"])
clsBayes = Classifier(classname="weka.classifiers.bayes.NaiveBayes")


# # US Seen Bayes
# preprocess_classifier('seen', clsBayes, False, devList, False, 'full_seen_bayes', '')

# # US Seen J48
# preprocess_classifier('seen', clsTree, False, devList, False, 'full_seen_j48', '')

# # US Unseen Bayes
# preprocess_classifier('unseen', clsBayes, False, devList, False, 'full_unseen_bayes', '')

# # US Unseen J48
preprocess_classifier('unseen', clsTree, False, devList, False, 'full_unseen_j48', 'subtract')

# # Small Seen Bayes
# preprocess_classifier('seen', clsBayes, False, smallList, True, 'small_seen_bayes', '')

# # # Small Seen J48
# preprocess_classifier('seen', clsTree, False, smallList, True, 'small_seen_j48', '')

# # Small Unseen Bayes
# preprocess_classifier('unseen', clsBayes, False, smallList, True, 'small_unseen_bayes', '')

# # Small Unseen J48
# preprocess_classifier('unseen', clsTree, False, smallList, True, 'small_unseen_j48', '')

# # Occ Seen Bayes
# preprocess_classifier('seen', clsBayes, True, devList, False, 'occ_seen_bayes', '')

# # Occ Seen J48
# preprocess_classifier('seen', clsTree, True, devList, False, 'occ_seen_j48', '')

# # Occ Unseen Bayes
# preprocess_classifier('unseen', clsBayes, True, devList, False, 'occ_unseen_bayes', '')

# Occ Unseen J48
# preprocess_classifier('unseen', clsTree, True, devList, False, 'occ_unseen_j48', 'orig')

# # Occ Small Seen Bayes
# preprocess_classifier('seen', clsBayes, True, smallList, True, 'occ_small_seen_bayes', '')

# # Occ Small Seen J48
# preprocess_classifier('seen', clsTree, True, smallList, True, 'occ_small_seen_j48', '')

# # Occ Small Unseen Bayes
# preprocess_classifier('unseen', clsBayes, True, smallList, True, 'occ_small_unseen_bayes', '')

# # Occ Small Unseen J48
# preprocess_classifier('unseen', clsTree, True, smallList, True, 'occ_small_unseen_j48', '')


# Change device success characterization
# preprocess_classifier('change', clsBayes, False, devList, False, 'change_bayes', '')
# preprocess_classifier('change', clsTree, False, devList, False, 'change_j48', '')

# Do the same for each deviceType
# Get list of type:
# aws_c.execute('select deviceType, count(*) as count from temp_dat_occ_vector_2 ' \
# 	'where count>0 and duty!=0 and deviceMAC not in (select * from vector_reject) ' \
# 	'group by deviceType;')
# typeList = [x[0] for x in aws_c.fetchall()]
# for devType in typeList:
# 	# Get list of devices:
# 	aws_c.execute('select deviceMAC, count(*) as count from temp_dat_occ_vector_2 ' \
# 		'where count>0 and duty!=0 and deviceMAC not in (select * from vector_reject) ' \
# 		'and deviceType=\'' + devType + '\' ' \
# 		'group by deviceMAC;')
# 	typeDevList = [x[0] for x in aws_c.fetchall()]
# 	preprocess_classifier('change', clsBayes, False, typeDevList, False, 'change_' + devType.replace(' ', '').replace('/', '') + '_bayes', '')
# 	preprocess_classifier('change', clsTree, False, typeDevList, False, 'change_' + devType.replace(' ', '').replace('/', '') + '_j48', '')



item_start = datetime.utcnow()
for rT, cL, oC, dL, fc, lA, sT in process_list:
	process_classifier(rT, cL, oC, dL, fc, lA, sT)


jvm.stop()

# conf_new = sub_conf_matrix(save_orig, save_subtract)
# print('\nFull Unseen J48\n')
# print_conf_matrix(save_orig, sys.stdout, True, False, True)
# print('\nOcc Unseen J48\n')
# print_conf_matrix(conf_new, sys.stdout, True, True, True)

total_conf.close()
mv('conf_matrix.txt', master_saveDir)

for label in sorted(total_results):
	print(label + ': ' + str(total_results[label]) + ' pct correct')

def print_data(outfile, labels, bayesValues, treeValues):
	outfile.write('\n\n\"Naive Bayes\"\n')
	for idx, value in enumerate(bayesValues):
		outfile.write(str(idx) + '\t\"' + labels[idx] + '\"\t' + str(value) + '\n')

	outfile.write('\n\n\"J48\"\n')
	for idx, value in enumerate(treeValues):
		outfile.write(str(idx) + '\t\"' + labels[idx] + '\"\t' + str(value) + '\n')

	outfile.close()

def rep_none(key):
	if key in total_results:
		return total_results[key]
	else:
		return ''

# Create basic output
print_data(open('classify_basic.dat', 'w'), \
	['SMART, Seen', 'PB Small, Seen', 'SMART Unseen', 'PB Small, Unseen'], \
	[70, rep_none('small_seen_bayes'), 65, rep_none('small_unseen_bayes')], \
	[90, rep_none('small_seen_j48'), 60, rep_none('small_unseen_j48')])
mv('classify_basic.dat', master_saveDir)

# Create full output
print_data(open('classify_full.dat', 'w'),
	['Small, Seen', 'Full, Seen', 'Small, Unseen', 'Full, Unseen'],
	[rep_none('small_seen_bayes'), rep_none('full_seen_bayes'), rep_none('small_unseen_bayes'), rep_none('full_unseen_bayes')],
	[rep_none('small_seen_j48'), rep_none('full_seen_j48'), rep_none('small_unseen_j48'), rep_none('full_unseen_j48')])
mv('classify_full.dat', master_saveDir)

# Craete small occ output
print_data(open('classify_occ_small.dat', 'w'),
	['Small, Seen', 'Occ Sm, Seen', 'Small, Unseen', 'Occ Sm, Unseen'],
	[rep_none('small_seen_bayes'), rep_none('occ_small_seen_bayes'), rep_none('small_unseen_bayes'), rep_none('occ_small_unseen_bayes')],
	[rep_none('small_seen_j48'), rep_none('occ_small_seen_j48'), rep_none('small_unseen_j48'), rep_none('occ_small_unseen_j48')])
mv('classify_occ_small.dat', master_saveDir)

# Create full occ output
print_data(open('classify_occ_full.dat', 'w'),
	['Full, Seen', 'Occ, Seen', 'Full, Unseen', 'Occ, Unseen'],
	[rep_none('full_seen_bayes'), rep_none('occ_seen_bayes'), rep_none('full_unseen_bayes'), rep_none('occ_unseen_bayes')],
	[rep_none('full_seen_j48'), rep_none('occ_seen_j48'), rep_none('full_unseen_j48'), rep_none('occ_unseen_j48')])
mv('classify_occ_full.dat', master_saveDir)


