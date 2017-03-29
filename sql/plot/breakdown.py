#!/usr/bin/env python

def breakdown(energyCutoff, labelstr, outfileStr):

	outfile = open(outfileStr + '.plt', 'w')
	outfile.write('set terminal postscript enhanced eps solid color font \"Helvetica,14\" size 8in,2.0in\n')
	outfile.write('set output \"' + outfileStr + '.eps\"\n\n')

	outfile.write('# General setup\n\n')
	outfile.write('unset key\n')
	outfile.write('set boxwidth 0.5\n')
	outfile.write('set style fill solid 1.00 border lt -1\n')
	outfile.write('\n')

	outfile.write('set multiplot layout 2,1\n\n')

	outfile.write('# Top plot (energy)\n\n')
	outfile.write('unset xtics\n')
	outfile.write('set lmargin 10\n')
	outfile.write('set ylabel \"Average Daily\\nEnergy (Wh)\" offset 1,0 font \", 12\"\n')
	outfile.write('set yrange[0:' + str(energyCutoff) + ']\n')
	outfile.write('set size 1,0.38\n')
	outfile.write('set origin 0,0.60\n')
	outfile.write('set key top left font \", 12\"\n')
	outfile.write('\n')

	outfile.write(labelstr)

	outfile.write('plot \"' + outfileStr + '_li.dat\" using 1:3 with boxes fc rgb \"#4b97c8\" title \"BLEES/Ligeiro\", \\\n'
		'\t\"' + outfileStr + '_pb.dat\" using 1:3 with boxes fc rgb \"#ac0a0f\" title \"PowerBlade\"\n\n')

	outfile.write('# Bottom plot (power)\n\n')
	outfile.write('unset label\n')
	outfile.write('unset key\n')
	outfile.write('set logscale y\n')
	outfile.write('set bmargin 5.5\n')
	outfile.write('set xtics  rotate by 45 right font \", 10\"\n')
	outfile.write('set size 1,0.66\n')
	outfile.write('set origin 0,0\n')
	outfile.write('set yrange[1:5000]\n')
	outfile.write('set ylabel \"Average Active\\nPower (w)\" offset 1,-1 font \", 12\"\n')

	outfile.write('plot \"' + outfileStr + '_li.dat\" using 1:4:xticlabels(2) with boxes fc rgb \"#4b97c8\" title \"BLEES/Ligeiro\", \\\n'
		'\t\"' + outfileStr + '_pb.dat\" using 1:4:xticlabels(2) with boxes fc rgb \"#ac0a0f\"\n')

	outfile.write('unset multiplot\n')

	outfile.close()





















	# # CDF Printout
	# pwrData = sorted(expData, key=lambda dev: dev[5])

	# total_measured_percent = (total_measured_energy / gndTruth) * 100

	# outfilePath = outfileStr + '_pwrCDF.dat'
	# pltFilePath = outfileStr + '_pwrCDF.plt'

	# outfile_pwr = open(outfilePath, 'w')
	# outfile_pwr.write('# total measured energy: ' + str(total_measured_energy) + '\n')
	# outfile_pwr.write('# gnd truth: ' + str(gndTruth) + '\n')

	# total_measured_energy = float(total_measured_energy)
	# gndTruth = float(gndTruth)

	# curPower = 0
	# cdfEnergy = 0
	# #print(str(cdfEnergy) + " " + str(total_measured_energy) + " " + str(gndTruth))
	# measPct = cdfEnergy/total_measured_energy
	# gndPct = cdfEnergy/gndTruth
	# for mac, name, dayEnergy, var, totEnergy, power in pwrData:
	# 	# Test if this power is the same as the one before it
	# 	if power != curPower:
	# 		print(str(curPower) + " " + str(cdfEnergy) + " " + str(measPct) + " " + str(gndPct))		# Print the last device and the energy sum
	# 		outfile_pwr.write(str(curPower) + "\t" + str(cdfEnergy) + "\t" + str(measPct) + "\t" + str(gndPct) + "\n")
	# 		curPower = power

	# 	cdfEnergy += float(totEnergy) 	# Either way, increment total energy (done after printing because that prints the previous power level)

	# 	measPct = cdfEnergy/total_measured_energy
	# 	gndPct = cdfEnergy/gndTruth

	# print(str(curPower) + " " + str(cdfEnergy) + " " + str(measPct) + " " + str(gndPct))		# Print the last device and the energy sum
	# outfile_pwr.write(str(curPower) + "\t" + str(cdfEnergy) + "\t" + str(measPct) + "\t" + str(gndPct) + "\n")

	# outfile_pwr.close()

	# outfile = open(pltFilePath, 'w')
	# outfile.write('set terminal postscript enhanced eps solid color font \"Helvetica,14\" size 4in,2.8in\n')
	# outfile.write('set output \"' + outfileStr + '_pwrCDF.eps\"\n\n')

	# outfile.write('unset key\n\n')

	# outfile.write('set logscale x\n\n')

	# outfile.write('set xlabel \"Device power (W)\"\n')
	# outfile.write('set ylabel \"Percent of MELs Energy (%)\"\n')
	# outfile.write('set y2label \"Percent of Total Energy (%)\"\n\n')

	# outfile.write('set grid x y mxtics\n\n')

	# outfile.write('set xtics .1\n\n')

	# outfile.write('set y2tics ' + str(total_measured_percent/10) + '\n')
	# outfile.write('set y2range [0:' + str(total_measured_percent) + ']\n')
	# outfile.write('set format y2 \"\%.0f\"\n\n')

	# outfile.write('set xrange [:2000]\n\n')

	# outfile.write('plot \"' + outfilePath + '\" using 1:($3*100) axes x1y1 with lines, \\\n')
	# outfile.write('\t\"' + outfilePath + '\" using 1:($4*100) axes x1y2 with lines\n')

	# outfile.close()



