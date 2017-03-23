set terminal postscript enhanced eps solid color font "Helvetica,14" size 8in,2.0in
set output "breakdown.eps"

# General setup

unset key
set boxwidth 0.5
set style fill solid 1.00 border lt -1

set multiplot layout 2,1

# Top plot (energy)

unset xtics
set lmargin 10
set ylabel "Average Daily\nEnergy (Wh)" offset 1,0 font ", 12"
set yrange[0:1000]
set size 1,0.38
set origin 0,0.60
set key top left font ", 12"

plot "energy_li.dat" using 1:4 with boxes fc rgb "#4b97c8" title "BLEES", \
	"energy_pb.dat" using 1:4 with boxes fc rgb "#ac0a0f" title "PowerBlade"

# Bottom plot (power)

unset label
unset key
set logscale y
set bmargin 5.5
set xtics  rotate by 45 right font ", 10"
set size 1,0.66
set origin 0,0
set yrange[1:5000]
set ylabel "Average Active\nPower (w)" offset 1,-1 font ", 12"
plot "energy_li.dat" using 1:6:xticlabels(3) with boxes fc rgb "#4b97c8" title "BLEES", \
	"energy_pb.dat" using 1:6:xticlabels(3) with boxes fc rgb "#ac0a0f"
unset multiplot
