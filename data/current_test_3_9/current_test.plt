set terminal postscript enhanced eps solid color font "Helvetica,14" size 3.25in,1.7in
set output "current_test.eps"

#set title "Power Supplied from AC/DC"

#set style line 1 lt 4  ps 1.2 pt 7 lw 5 lc rgb "#d7191c"
#set style line 2 lt 1  ps 1.2 pt 2 lw 5 lc rgb "#fdae61"

set xlabel "Load Power (W)"
set ylabel "Amplified voltage (V)"

#set xrange [0:6E-8]
#set yrange [0:1.5]
#set y2range [0:15]
#set y2label "I / Vol Ratio (mA/cm^3)"
#set xtics (".01" 1E-8, ".02" 2E-8, ".03" 3E-8, ".04" 4E-8, ".05" 5E-8, ".06" 6E-8)
#set y2tics (5, 10, 15)

unset key

plot "current_test_3_9.dat" u 1:2 with lines linestyle 2 
