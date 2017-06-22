#!/usr/bin/env python

def printEnergy(expData, total_measured_energy, gndTruth, outfileStr):
	if gndTruth == 0 or gndTruth == None:
		gndTruth = total_measured_energy

	# CDF Printout
	pwrData = sorted(expData, key=lambda dev: dev[8])

	total_measured_percent = (total_measured_energy / gndTruth) * 100

	outfilePath = outfileStr + '_pwrCDF.dat'
	pltFilePath = outfileStr + '_pwrCDF.plt'

	outfile_pwr = open(outfilePath, 'w')
	outfile_pwr.write('# total measured energy: ' + str(total_measured_energy) + '\n')
	outfile_pwr.write('# gnd truth: ' + str(gndTruth) + '\n')

	total_measured_energy = float(total_measured_energy)
	gndTruth = float(gndTruth)

	curPower = 0
	cdfEnergy = 0
	#print(str(cdfEnergy) + " " + str(total_measured_energy) + " " + str(gndTruth))
	measPct = cdfEnergy/total_measured_energy
	gndPct = cdfEnergy/gndTruth
	countPower = 0
	for mac, name, loc, devCat, devType, dayEnergy, var, totEnergy, power, minEnergy, q1Energy, q3Energy, maxEnergy, minPower, q1Power, q3Power, maxPower in pwrData:
		# Test if this power is the same as the one before it
		if power != curPower:
			#print(str(curPower) + " " + str(cdfEnergy) + " " + str(measPct) + " " + str(gndPct))		# Print the last device and the energy sum
			outfile_pwr.write(str(curPower) + "\t" + str(cdfEnergy) + "\t" + str(measPct) + "\t" + str(gndPct) + "\t" + str(float(countPower)/269) + "\n")
			curPower = power
		countPower += 1

		cdfEnergy += float(dayEnergy) 	# Either way, increment total energy (done after printing because that prints the previous power level)

		measPct = cdfEnergy/total_measured_energy
		gndPct = cdfEnergy/gndTruth

	#print(str(curPower) + " " + str(cdfEnergy) + " " + str(measPct) + " " + str(gndPct))		# Print the last device and the energy sum
	outfile_pwr.write(str(curPower) + "\t" + str(cdfEnergy) + "\t" + str(measPct) + "\t" + str(gndPct) + "\t" + str(float(countPower)/269) + "\n")

	outfile_pwr.close()

	outfile = open(pltFilePath, 'w')
	outfile.write('set terminal postscript enhanced eps solid color font \"Helvetica,14\" size 4in,2.8in\n')
	outfile.write('set output \"' + outfileStr + '_pwrCDF.eps\"\n\n')

	outfile.write('set key top left\n\n')

	#outfile.write('set logscale x\n\n')

	outfile.write('set xlabel \"Device power (W)\"\n')
	outfile.write('set ylabel \"Fraction of Total Energy\"\n')
	outfile.write('set y2label \"Fraction of Devices\"\n\n')

	outfile.write('set grid x y mxtics\n\n')

	#outfile.write('set xtics .1\n\n')

	outfile.write('set y2tics\n\n')

	#outfile.write('set y2range [0:.2]\n\n')

	outfile.write('set ytics ' + str(total_measured_percent/1000) + '\n')
	#outfile.write('set yrange [0:' + str(float(total_measured_percent)*1.05/100) + ']\n')
	outfile.write('set yrange [0:1.05]\n')
	outfile.write('set format y \"\%.2f\"\n\n')
	#outfile.write('set format y2 \"\%.2f\"\n\n')

	outfile.write('set xrange [:' + str(curPower) + ']\n\n')

	outfile.write('d(y) = ($0 == 0) ? (y1 = y, 1/0) : (y2 = y1, y1 = y, y1-y2)\n\n')
	outfile.write('d2(x,y) = ($0 == 0) ? (x1 = x, y1 = y, 1/0) : (x2 = x1, x1 = x, y2 = y1, y1 = y, (y1-y2)/(x1-x2))\n\n')

	outfile.write('plot \"' + outfilePath + '\" using 1:($3) axes x1y1 with lines title \"Energy\", \\\n')
	#outfile.write('\t\"' + outfilePath + '\" using 1:($4*100) axes x1y2 with lines, \\\n')
	outfile.write('\t\"' + outfilePath + '\" using 1:($5) axes x1y1 with lines title \"Devices\", \\\n')
	outfile.write('\t\"' + outfilePath + '\" using 1:(d($3)) axes x1y2 with lines smooth csplines title \"Impact\", \\\n')
	outfile.write('\t\"' + outfilePath + '\" using 1:(d($5)) axes x1y2 with lines smooth csplines title \"Impact2\"\n')

	outfile.close()



