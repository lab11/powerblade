#!/usr/bin/env python

def gen_arff(label, typeStr, results, printOcc):
	
	# Create arff file for Weka for all devices
	arff = open(label + '.arff', 'w')

	arff.write('@relation ' + label + '\n\n')

	arff.write('@attribute avgPwr numeric\n')
	arff.write('@attribute varPwr numeric\n')
	arff.write('@attribute maxPwr numeric\n')
	arff.write('@attribute minPwr numeric\n')
	arff.write('@attribute count numeric\n')
	arff.write('@attribute dutyCycle numeric\n')
	if printOcc == True:
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
				if printOcc == False:
					if idx == 9 or idx == 10:
						continue
				dataStr.append(str(datItem))
				dataStr.append(',')
		dataStr[-2] = '"' + dataStr[-2] + '"'
		dataStr[-1] = '\n'

		dataStr = ''.join(dataStr)
		arff.write(dataStr)

	arff.write('\n')
	arff.close()









