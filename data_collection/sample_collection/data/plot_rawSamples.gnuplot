set terminal postscript enhanced eps solid color font "Helvetica,14" size 3in,2in
set output "plot.eps"
#set xrange [0:500]
set yrange [-600:600]

set xlabel 'Sample count'
set ylabel 'ADC Reading'

plot 'rawSamples.dat' u 1:2 with lines title 'Voltage', \
	'rawSamples.dat' u 1:3 with lines title 'Current', \
	'rawSamples.dat' u 1:4 with lines title 'Integrate'
