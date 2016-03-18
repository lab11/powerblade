set terminal postscript enhanced eps solid color font "Helvetica,14" size 3.25in,2.3in
set output "temp.eps"

set xlabel "Timestamp" offset 0,-4
set ylabel "Power (W)"

set yrange [0:]

set datafile separator "\t"
set timefmt "%Y-%m-%d %H:%M:%S"
set xdata time

set format x "%m-%d %H:%M"

set key above

set bmargin 8

