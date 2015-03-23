set terminal postscript enhanced eps solid color font "Helvetica,14" size 3.25in,2in
set output "waveforms_far.eps"

set title "Vcap and Icore for a charge/discharge cycle"

set xlabel "Time (ms)"
set y2label "System Current (mA)"
set ylabel "Capcitor Voltage (V)"

#set xrange [0:2500]
#set yrange [0:3.5]
#set y2range [0:1.5]

set ytics 2 nomirror
set y2tics

#set key bottom right

plot "far.dat" u 1:2 with lines title "Vcap" \
	lw 2 lc rgb "#0000CC" axes x1y1, \
	"far.dat" u 1:3 with lines title "Node Current" \
	lw 2 axes x1y2, \
