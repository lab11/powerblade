set terminal postscript enhanced eps solid color font "Helvetica,14" size 3in,2in
set output "mean.eps"

set title "Mean of reported in PowerBlade"

set xlabel "Watts (W) or equiv."
set ylabel "Vrms (V)"

set xrange [0:25]
set yrange [0:250]

set key bottom right

plot "mean_t1.dat" with linespoints title "Original (MCP6V3)", \
	"mean_t2.dat" with linespoints title "Silver Bullet (MAX4238)", \
	"mean_t3.dat" with linespoints title "Ideal - Fgen"



