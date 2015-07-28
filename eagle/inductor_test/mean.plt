set terminal postscript enhanced eps solid color font "Helvetica,14" size 3in,2in
set output "mean.eps"

set title "Mean of reported in PowerBlade - Low Range"

set xlabel "Watts (W) or equiv."
set ylabel "Vrms (V)"

set xrange [0:200]
set yrange [0:]

set key bottom right

plot "mean_t1.dat" with errorbars title "Original (MCP6V3)" ls 1, \
	"mean_t1.dat" with lines notitle ls 1, \
	"mean_t2.dat" with errorbars title "Silver Bullet (MAX4238)" ls 2, \
	"mean_t2.dat" with lines notitle ls 2, \
	"mean_t4.dat" with errorbars title "Ideal - Fgen" ls 3, \
	"mean_t4.dat" with lines notitle ls 3



