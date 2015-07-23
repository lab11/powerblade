set terminal postscript enhanced eps solid color font "Helvetica,14" size 3in,2in
set output "vrms.eps"

set title "Vrms in PowerBlade"

set xlabel "Watts (W) or equiv."
set ylabel "Vrms (V)"

set xrange [0:25]
set yrange [0:0.14]

set key bottom right

plot "vrms_t1.dat" with linespoints title "Original (MCP6V3)", \
	"vrms_t2.dat" with linespoints title "Silver Bullet (MAX4238)", \
	"vrms_t3.dat" with linespoints title "Ideal - Fgen"



