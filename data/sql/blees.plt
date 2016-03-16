set terminal postscript enhanced eps solid color font "Helvetica,14" size 3.25in,2in
set output "blees.eps"

set yrange [-2:300]

set datafile separator "\t"
set timefmt "%Y-%m-%d %H:%M:%S"
set xdata time

set format x "%m-%d %H:%M"

set xtics 60*10 rotate by 70 offset -2.9,-4.65
set bmargin 6

unset key

plot "myDump.csv" u 1:2 with points

