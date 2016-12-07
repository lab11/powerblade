set terminal postscript enhanced eps solid color font "Helvetica,14" size 3in,2in
set output "configs.eps"

set title "Average Error in each Configuration"
set ylabel "Average Error (W)"
set xlabel "Configuration"

#set xrange [-.5:.5]
#set yrange [-.5:.5]
#set cbtics ("0" 0, "2" 2E-8, "4" 4E-8, "6" 6E-8, "8" 8E-8)

unset key

set xtics  rotate by 45 right font ", 10"
plot 'sorted_configs.dat' u 2:xtic(1)


