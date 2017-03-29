#!/usr/bin/env python

def printEnergy(expData, total_measured_energy, gndTruth, outfileStr):
	if gndTruth == 0 or gndTruth == None:
		return

	# CDF Printout
	pwrData = sorted(expData, key=lambda dev: dev[5])

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
	for mac, name, dayEnergy, var, totEnergy, power in pwrData:
		# Test if this power is the same as the one before it
		if power != curPower:
			print(str(curPower) + " " + str(cdfEnergy) + " " + str(measPct) + " " + str(gndPct))		# Print the last device and the energy sum
			outfile_pwr.write(str(curPower) + "\t" + str(cdfEnergy) + "\t" + str(measPct) + "\t" + str(gndPct) + "\n")
			curPower = power

		cdfEnergy += float(totEnergy) 	# Either way, increment total energy (done after printing because that prints the previous power level)

		measPct = cdfEnergy/total_measured_energy
		gndPct = cdfEnergy/gndTruth

	print(str(curPower) + " " + str(cdfEnergy) + " " + str(measPct) + " " + str(gndPct))		# Print the last device and the energy sum
	outfile_pwr.write(str(curPower) + "\t" + str(cdfEnergy) + "\t" + str(measPct) + "\t" + str(gndPct) + "\n")

	outfile_pwr.close()

	outfile = open(pltFilePath, 'w')
	outfile.write('set terminal postscript enhanced eps solid color font \"Helvetica,14\" size 4in,2.8in\n')
	outfile.write('set output \"' + outfileStr + '_pwrCDF.eps\"\n\n')

	outfile.write('unset key\n\n')

	outfile.write('set logscale x\n\n')

	outfile.write('set xlabel \"Device power (W)\"\n')
	outfile.write('set ylabel \"Percent of MELs Energy (%)\"\n')
	outfile.write('set y2label \"Percent of Total Energy (%)\"\n\n')

	outfile.write('set grid x y mxtics\n\n')

	outfile.write('set xtics .1\n\n')

	outfile.write('set y2tics ' + str(total_measured_percent/10) + '\n')
	outfile.write('set y2range [0:' + str(total_measured_percent) + ']\n')
	outfile.write('set format y2 \"\%.0f\"\n\n')

	outfile.write('set xrange [:2000]\n\n')

	outfile.write('plot \"' + outfilePath + '\" using 1:($3*100) axes x1y1 with lines, \\\n')
	outfile.write('\t\"' + outfilePath + '\" using 1:($4*100) axes x1y2 with lines\n')

	outfile.close()



