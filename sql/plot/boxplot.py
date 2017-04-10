#!/usr/bin/env python

def boxplot(xsize, xrange, yrange, fileStr):

	pltfile = open(fileStr + '.plt', 'w')

	pltfile.write('set terminal postscript enhanced eps solid color font \"Helvetica,14\" size ' + str(xsize) + 'in,2.8in\n')
	pltfile.write('set output \'' + fileStr + '.eps\'\n\n')

	pltfile.write('set boxwidth 0.2 absolute\n')
	pltfile.write('set bars 4.0\n')
	pltfile.write('set style fill solid 0.50 border lt -1\n\n')


	pltfile.write('set multiplot layout 2,1\n\n')

	pltfile.write('# Top plot (energy)\n')
	pltfile.write('unset xtics\n')
	pltfile.write('set rmargin 3\n')
	pltfile.write('set ylabel \"Average Daily\\nEnergy (Wh)\" offset 1,0 font \", 12\"\n\n')
	pltfile.write('set xrange [-.5:' + str(xrange) + ']\n')
	pltfile.write('set yrange [-100:' + str(yrange) + ']\n')
	pltfile.write('set size 1,0.44\n')
	pltfile.write('set origin 0,0.55\n')
	pltfile.write('set key top left font \", 12\"\n\n')

	pltfile.write('plot \'' + fileStr + '_pb.dat\' using 1:4:3:7:6:13:xticlabels(2) with candlesticks lw 1.5 fc rgb \"#ac0a0f\" title \"PowerBlade\" whiskerbars, \\\n')
  	pltfile.write('\t\'\' using 1:5:5:5:5:13 with candlesticks lt -1 lw 1.5 notitle, \\\n')
  	pltfile.write('\t\'' + fileStr + '_li.dat\' using 1:4:3:7:6:13:xticlabels(2) with candlesticks lw 1.5 fc rgb \"#4b97c8\" title \"BLEES/Ligeiro\" whiskerbars, \\\n')
  	pltfile.write('\t\'\' using 1:5:5:5:5:13 with candlesticks lt -1 lw 1.5 notitle\n\n')

	pltfile.write('# Bottom plot (power)\n\n')

	pltfile.write('unset label\n')
	pltfile.write('unset key\n')
	pltfile.write('set yrange [1:' + str(yrange) + ']\n')
	pltfile.write('set logscale y\n')
	pltfile.write('set bmargin 5.5\n')
	pltfile.write('set ylabel \"Average Active\\nPower (w)\" offset 1,-1 font \", 12\"\n')
	pltfile.write('set xtics  rotate by 45 right font \", 10\"\n')
	pltfile.write('set size 1,0.55\n')
	pltfile.write('set origin 0,0\n')
	pltfile.write('set xrange [-.5:' + str(xrange) + ']\n')
	pltfile.write('set grid y\n\n')

	pltfile.write('plot \'' + fileStr + '_pb.dat\' using 1:9:8:12:11:13:xticlabels(2) with candlesticks lw 1.5 fc rgb \"#ac0a0f\" title \"PowerBlade\" whiskerbars, \\\n')
  	pltfile.write('\t\'\' using 1:10:10:10:10:13 with candlesticks lt -1 lw 1.5 notitle, \\\n')
	pltfile.write('\t\'' + fileStr + '_li.dat\' using 1:9:8:12:11:13:xticlabels(2) with candlesticks lw 1.5 fc rgb \"#4b97c8\" title \"BLEES/Ligeiro\" whiskerbars, \\\n')
  	pltfile.write('\t\'\' using 1:10:10:10:10:13 with candlesticks lt -1 lw 1.5 notitle\n\n')

	pltfile.write('unset multiplot\n')

	pltfile.close()






