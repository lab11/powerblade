set terminal postscript enhanced eps solid color font "Helvetica,14" size 3.25in,1.7in
set output "blees.eps"

set datafile separator ","
set timefmt "%Y-%m-%d %H:%M:%S"
set xdata time

set format x "%m-%d\n%H:%M"

plot "outside_light.csv" u 1:2

