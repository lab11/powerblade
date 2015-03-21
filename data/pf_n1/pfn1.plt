set terminal postscript enhanced eps solid color font "Helvetica,14" size 3.25in,2in
set output "pfn1.eps"

set title "Measured Power and PF"

set xlabel "AC Power (W)"
set y2label "Power Factor"
set ylabel "Power (W)"

#set yrange [0:3.5]
set y2range [0:1.5]

set y2tics 1

set key bottom right

plot "pfn1.dat" u 3:3 with linespoints title "Actual Power" \
	lw 2 axes x1y1, \
	"pfn1.dat" u 3:4 with linespoints title "Measured Power" \
	lw 2 axes x1y1, \
	"pfn1.dat" u 3:5 with linespoints title "Actual Power Factor" \
	lw 2 axes x1y2, \
	"pfn1.dat" u 3:6 with linespoints title "Measured Power Factor" \
	lw 2 axes x1y2,

