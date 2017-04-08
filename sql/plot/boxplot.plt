#set terminal postscript enhanced eps solid color font "Helvetica,14" size 4in,2.8in
set terminal postscript enhanced eps solid color font "Helvetica,14" size 8in,2.8in
set output 'boxplot.eps'

#set style line 1 lt 4  ps 0.8 pt 7 lw 5 lc rgb "#ac0a0f"

set boxwidth 0.2 absolute
# set bars 4.0
#set style fill empty
set style fill solid 0.50 border lt -1


set multiplot layout 2,1

# Top plot (energy)

#set xtics  rotate by 45 right font ", 10"
#set xtics scale 0
unset xtics
#set lmargin 5
set rmargin 3
set ylabel "" offset 1,0 font ", 12"
#set xrange[-.5:15.5]
set xrange[-.5:66.5]
set yrange[:2000]
set size 1,0.44
set origin 0,0.55
set key top left font ", 12"

#bdownbox_pb.dat
#bdownbox_li.dat

#boxplot_pb.dat
#boxplot_li.dat

plot 'bdownbox_pb.dat' using 1:4:3:7:6:13:xticlabels(2) with candlesticks lw 1.5 fc rgb "#ac0a0f" title "PowerBlade" whiskerbars, \
  ''         using 1:5:5:5:5:13 with candlesticks lt -1 lw 1.5 notitle, \
  'bdownbox_li.dat' using 1:4:3:7:6:13:xticlabels(2) with candlesticks lw 1.5 fc rgb "#4b97c8" title "BLEES/Ligeiro" whiskerbars, \
  ''         using 1:5:5:5:5:13 with candlesticks lt -1 lw 1.5 notitle




# Bottom plot (power)

unset label
unset key
set logscale y
set bmargin 5.5
set xtics  rotate by 45 right font ", 10"
#set xtics scale 0
set size 1,0.55
set origin 0,0
#set xrange[-.5:15.5]
set xrange[-.5:66.5]
set yrange[1:5000]
set grid y

set ylabel "" offset 1,-1 font ", 12"



plot 'bdownbox_pb.dat' using 1:9:8:12:11:13:xticlabels(2) with candlesticks lw 1.5 fc rgb "#ac0a0f" title "PowerBlade" whiskerbars, \
  ''         using 1:10:10:10:10:13 with candlesticks lt -1 lw 1.5 notitle, \
  'bdownbox_li.dat' using 1:9:8:12:11:13:xticlabels(2) with candlesticks lw 1.5 fc rgb "#4b97c8" title "BLEES/Ligeiro" whiskerbars, \
  ''         using 1:10:10:10:10:13 with candlesticks lt -1 lw 1.5 notitle


unset multiplot





