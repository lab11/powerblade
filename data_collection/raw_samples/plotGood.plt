set terminal postscript enhanced eps solid color font "Helvetica,14" size 3in,2in
set output "plotGood.eps"

#set xrange [0:1000]

plot "goodSamples.dat" u 1:2 with lines title 'Voltage' , \
	"goodSamples.dat" u 1:3 with lines title 'Current'


