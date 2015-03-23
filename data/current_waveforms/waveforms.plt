set terminal postscript enhanced eps solid color font "Helvetica,14" size 3.25in,2in
set output "waveforms.eps"

#set title "Measured Power and PF for PF=1 Load"

#set xlabel "AC Power (W)"
#set y2label "Measured Power Factor"
#set ylabel "Power (W)"

#set yrange [0:3.5]
#set y2range [0:1.5]

#set y2tics 1

#set key bottom right

plot "blender_puere.dat" u 1:2 with lines title "Measured Power" \
	lw 2 lc rgb "#0000CC" axes x1y1, \
	"blender_puere.dat" u 1:3 with lines title "Current" \
	lw 2 axes x1y1, \
	"blender_stir.dat" u 1:3 with lines  \
	lw 2 axes x1y1, \
