#!/usr/bin/env python

def gen_arff(label, typeStr, results, printOcc, datCols):
	
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

	# arff.write('@attribute coffee_maker numeric\n')
	# arff.write('@attribute television numeric\n')
	# arff.write('@attribute blowdryer numeric\n')
	# arff.write('@attribute toaster numeric\n')
	# arff.write('@attribute fridge numeric\n')
	# arff.write('@attribute microwave numeric\n')
	# arff.write('@attribute phone_charger numeric\n')
	# arff.write('@attribute curling_iron numeric\n')
	# arff.write('@attribute lamp numeric\n')
	# arff.write('@attribute fan numeric\n')
	# arff.write('@attribute laptop_computer numeric\n')
	# arff.write('@attribute exterior_lighting numeric\n')
	# arff.write('@attribute router_modem numeric\n')
	# arff.write('@attribute cable_box numeric\n')
	# arff.write('@attribute blender numeric\n')

	arff.write('@attribute deviceType ' + typeStr + '\n\n')

	arff.write('@data\n')

	for data in results:
		dataStr = []
		for idx, datItem in enumerate(data):
			if(idx > datCols):
				if datItem == None:
					datItem = 0
				if printOcc == False:
					if idx == (datCols + 7) or idx == (datCols + 8):
						continue
				dataStr.append(str(datItem))
				dataStr.append(',')
		dataStr[-2] = '"' + dataStr[-2] + '"'
		dataStr[-1] = '\n'

		dataStr = ''.join(dataStr)
		arff.write(dataStr)

	arff.write('\n')
	arff.close()









