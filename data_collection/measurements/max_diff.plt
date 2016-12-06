set terminal postscript enhanced eps solid color font "Helvetica,14" size 6.2in,4.2in
set output "max_diff.eps"

set boxwidth 0.4
set style fill solid

set ylabel "Absolute Error (W)"
set y2label "Percent Error (%)"

#set logscale y

offset = 5

set y2tics

set y2range [0:100]

#plot "sorted_maxDiff_power.dat" u :xtic(2) notitle, \
#	"" u ($1-1.2):3 with boxes axes x1y1 title "Absolute Error", \
#	"" u ($1-.8):($4*100) with boxes axes x1y2 title "Percent Error"

plot "sorted_maxDiff_power.dat" u :xtic(2) notitle, \
	"" u ($3+offset) with boxes, \
	"" u ($3) with boxes lc "grey" notitle, \
	"" u ($4+offset) with boxes, \
	"" u ($4) with boxes lc "grey" notitle, \
	"" u ($5+offset) with boxes, \
	"" u ($5) with boxes lc "grey" notitle, \
	"" u ($6+offset) with boxes, \
	"" u ($6) with boxes lc "grey" notitle, \
	"" u ($7+offset) with boxes, \
	"" u ($7) with boxes lc "grey" notitle, \
	"" u ($8+offset) with boxes, \
	"" u ($8) with boxes lc "grey" notitle, \
	"" u ($9+offset) with boxes, \
	"" u ($9) with boxes lc "grey" notitle, \
	"" u ($10+offset) with boxes, \
	"" u ($10) with boxes lc "grey" notitle, \
	"" u ($11+offset) with boxes, \
	"" u ($11) with boxes lc "grey" notitle, \
	"" u ($12+offset) with boxes, \
	"" u ($12) with boxes lc "grey" notitle, \
	"" u ($13+offset) with boxes, \
	"" u ($13) with boxes lc "grey" notitle, \
	"" u ($14+offset) with boxes, \
	"" u ($14) with boxes lc "grey" notitle, \
	"" u ($15+offset) with boxes, \
	"" u ($15) with boxes lc "grey" notitle, \
	"" u ($16+offset) with boxes, \
	"" u ($16) with boxes lc "grey" notitle, \
	"" u ($17+offset) with boxes, \
	"" u ($17) with boxes lc "grey" notitle
