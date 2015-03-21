set terminal postscript enhanced eps solid color font "Helvetica,14" size 3.25in,2in
set output "pf1.eps"

set title "Measured Power and PF for PF=1 Load"

set xlabel "AC Power (W)"
set y2label "Measured Power Factor"
set ylabel "Power (W)"

#set yrange [0:3.5]
set y2range [0:1.5]

set y2tics 1

set key bottom right

plot "pf1.dat" u 1:2 with linespoints title "Measured Power" \
	lw 2 lc rgb "#0000CC" axes x1y1, \
	"pf1.dat" u 1:3 with linespoints title "Power Factor" \
	lw 2 lc rgb "#CC0000" axes x1y2, \
	"pf1.dat" u 1:1 with linespoints title "Actual Power" \
	lw 2 lc rgb "#00CC00" axes x1y1,

