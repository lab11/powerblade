#!/usr/bin/env python

import sys
import os
from printEnergy import printEnergy

# total_measured = 0
# gndTruth = 0
# pwrData = []

epList = {}
epList['power'] = {}
epList['energy'] = {}

for inData in sys.argv[1:]:

	dirNam = inData.split('/')[-2]
	location = dirNam.split('_')[3][1]
	runType = dirNam.split('_')[4]

	# if(runType == 'power'):
	# 	if location in epList['power']:
	# 		print("Error: multiple power lists for location " + str(location))
	# 		exit()
	# 	else:
	# 		epList['power'][location] = {}

	# 		inFile = open(inData + 'tot_power.dat', 'r')
	# 		for line in inFile:
	# 			lineList = line[:-1].split('\t')[1:]
	# 			lineList[-1] = float(lineList[-1]) # Last column is power, convert to float
	# 			epList['power'][location][lineList[0]] = [lineList[1][1:-1], lineList[2]]
	if(runType == 'energy'):
		tmpErgy = {}
		inFile = open(inData + 'tot_energy.dat', 'r')
		for line in inFile:
			if(line[0] == '#'):
				lineList = line[2:-1].split(': ')
				if lineList[0] == 'total measured energy':
					tmpErgy['tM'] =  ['', [float(lineList[1])], [0]]
				elif lineList[1] == 'gnd truth':
					tmpErgy['gT'] = ['', [float(lineList[1])], [0]]
			else:
				lineList = line[:-1].split('\t')[1:]
				tmpErgy[lineList[0]] = [lineList[1][1:-1], lineList[2], lineList[3], [float(lineList[4])], [float(lineList[5])], float(lineList[7])]

		# Now combine with the existing
		if location in epList['energy']:
			for dev in tmpErgy:
				if dev in epList['energy'][location]:
					epList['energy'][location][dev][3].extend(tmpErgy[dev][3])
					epList['energy'][location][dev][4].extend(tmpErgy[dev][4])
					epList['energy'][location][dev][5] = tmpErgy[dev][5]
				else:
					epList['energy'][location][dev] = tmpErgy[dev]
		else:
			epList['energy'][location] = tmpErgy


# Do the combination
for location in epList['energy']:
	for dev in epList['energy'][location]:
		epList['energy'][location][dev][3] = sum(epList['energy'][location][dev][3])/float(len(epList['energy'][location][dev][3]))
		epList['energy'][location][dev][4] = sum(epList['energy'][location][dev][4])/float(len(epList['energy'][location][dev][4]))


# Category-based energy breakdown


# CDF-style energy breakdown



for key in epList:
	print(epList[key])

exit()






# Energy Printout
for idx, (mac, name, dayEnergy, var, totEnergy, power) in enumerate(expData):
	total_measured_energy += dayEnergy
	print(str(idx) + " " + str(mac) + " \"" + str(name) + "\" " + str(dayEnergy) + " " + str(var) + " " + str(totEnergy) + " " + str(power))
	outfile.write(str(idx) + "\t" + str(mac) + "\t\"" + str(name) + "\"\t" + str(dayEnergy) + "\t" + str(var) + "\t" + str(totEnergy) + "\t" + str(power) + "\n")
	if(mac[6:8] == '70'):
		outfile_pb.write(str(idx) + "\t" + str(mac) + "\t\"" + str(name) + "\"\t" + str(dayEnergy) + "\t" + str(var) + "\t" + str(totEnergy) + "\t" + str(power) + "\n")
	else:
		outfile_li.write(str(idx) + "\t" + str(mac) + "\t\"" + str(name) + "\"\t" + str(dayEnergy) + "\t" + str(var) + "\t" + str(totEnergy) + "\t" + str(power) + "\n")
	if(dayEnergy > energyCutoff):
		labelstr += 'set label at ' + str(idx) + ', ' + str(energyCutoff * 1.1) + ' \"' + str(int(dayEnergy)) + '\" center font \", 8\"\n'

outfile.write('# total measured energy: ' + str(total_measured_energy) + '\n')
outfile.write('# gnd truth: ' + str(gndTruth) + '\n')

total_measured_percent = (total_measured_energy / gndTruth) * 100

outfile_pb.close()
outfile_li.close()

outfile = open('breakdown.plt', 'w')
outfile.write('set terminal postscript enhanced eps solid color font \"Helvetica,14\" size 8in,2.0in\n')
outfile.write('set output \"breakdown.eps\"\n\n')

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

outfile.write('plot \"energy_li.dat\" using 1:4 with boxes fc rgb \"#4b97c8\" title \"BLEES/Ligeiro\", \\\n'
	'\t\"energy_pb.dat\" using 1:4 with boxes fc rgb \"#ac0a0f\" title \"PowerBlade\"\n\n')

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

outfile.write('plot \"energy_li.dat\" using 1:7:xticlabels(3) with boxes fc rgb \"#4b97c8\" title \"BLEES/Ligeiro\", \\\n'
	'\t\"energy_pb.dat\" using 1:7:xticlabels(3) with boxes fc rgb \"#ac0a0f\"\n')

outfile.write('unset multiplot\n')

outfile.close()

# Clean up anything left from last time (in the case of errors)
# if(os.path.exists('breakdown.eps')):
# 	os.remove('breakdown.eps')
# if(os.path.exists('breakdown.pdf')):
# 	os.remove('breakdown.pdf')

# Generate plot and convert to PDF
gnuplot('breakdown.plt')
epstopdf('breakdown.eps')

# Show plot file
# img = subprocess.Popen(['open', 'datfile.pdf'])
# img.wait()

# Remove temporary file
os.remove('breakdown.eps')

# Move data to saveDir
mv('tot_energy.dat', qu_saveDir)
mv('energy_pb.dat', qu_saveDir)
mv('energy_li.dat', qu_saveDir)
mv('breakdown.plt', qu_saveDir)
mv('breakdown.pdf', qu_saveDir)

# printEnergy(expData, total_measured_energy, gndTruth, 'energy')

# gnuplot('energy_pwrCDF.plt')
# epstopdf('energy_pwrCDF.eps')

# os.remove('energy_pwrCDF.eps')

# mv('energy_pwrCDF.dat', qu_saveDir)
# mv('energy_pwrCDF.plt', qu_saveDir)
# mv('energy_pwrCDF.pdf', qu_saveDir)































