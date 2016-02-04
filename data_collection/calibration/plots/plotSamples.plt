set terminal postscript enhanced eps solid color font "Helvetica,14" size 3in,2in
set output "plotSamples.eps"

set xrange [0:570]

plot "rawSamples.dat" u 1:2 with lines title 'Voltage' , \
	"rawSamples.dat" u 1:3 with lines title 'Current', \
	"rawSamples.dat" u 1:4 with lines title 'Int'


