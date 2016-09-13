#set terminal postscript enhanced eps solid color font "Helvetica,14" size 8in,4.0in
set terminal postscript enhanced eps solid color font "Helvetica,14" size 4in,4in
set output "breakdown.eps"

unset key

set boxwidth 0.5
set style fill solid 1.00 border lt -1

set multiplot layout 2,1

unset xtics

set title "Total Energy for a 34 day period"

set lmargin 10
set ylabel "Energy Use (kWh)" offset 1,0 font ", 12"
#set yrange[0:1000]

set size 1,.4
set origin 0,.6

#set label at 54.6, 1100 "2299" center font ", 12"
#set label at 56.4, 1100 "2613" center font ", 12"
#set key top left font ", 12"

set datafile separator ","


#set logscale y

plot "energy_group.csv" using ($2/1000):xtic(1) with boxes fc rgb "#ac0a0f" title "PowerBlade"

unset label
unset key

#set logscale y
set xtics  rotate by 45 right font ", 10"
set title "Average On Power for a 34 day period"

#set size 1,.75
set size 1,.55
set origin 0,0
#set yrange[1:5000]
set ylabel "Average Power (w)" offset 1,-1 font ", 12"
plot "energy_group.csv" using 3:xtic(1) with boxes fc rgb "#4b97c8"

unset multiplot


#set bmargin 3.5











