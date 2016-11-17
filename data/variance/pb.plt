set term postscript eps font "Helvetica,22" size 5in,7in
set output "pb.eps"

#set border 3 lw 2
#set xtics nomirror scale 2
#set ytics nomirror scale 2
#set mxtics 5 
#set mytics 5 

#set label at 0,1 "hello" font "Helvetica,25" tc rgb 'orange'

set datafile separator ","

set yrange [0:2]
set xrange [0:]

unset key

#set xlabel 'the x'
#set ylabel 'the y'
#set format y "%0.1g"

plot 'absLamps_(effectively_surge_strip).dat' u 1:3:4 with errorbars ,\
	'absLamps_(effectively_surge_strip).dat' u 1:3 with lines ,\
	'absFridge.dat' u 1:3:4 with errorbars ,\
	'absFridge.dat' u 1:3 with lines ,\
	'absMicrowave.dat' u 1:3:4 with errorbars ,\
	'absMicrowave.dat' u 1:3 with lines ,\
	'absVacuum.dat' u 1:3:4 with errorbars ,\
	'absVacuum.dat' u 1:3 with lines ,\
	'absApple_TV.dat' u 1:3:4 with errorbars ,\
	'absApple_TV.dat' u 1:3 with lines ,\
	'absAmplifier.dat' u 1:3:4 with errorbars ,\
	'absAmplifier.dat' u 1:3 with lines ,\
	'absMonitor.dat' u 1:3:4 with errorbars ,\
	'absMonitor.dat' u 1:3 with lines ,\
	'absSmall_Aerogarden.dat' u 1:3:4 with errorbars ,\
	'absSmall_Aerogarden.dat' u 1:3 with lines ,\
	'absSmall_Aerogarden.dat' u 1:3:4 with errorbars ,\
	'absSmall_Aerogarden.dat' u 1:3 with lines ,\
	'absXbox_One.dat' u 1:3:4 with errorbars ,\
	'absXbox_One.dat' u 1:3 with lines ,\
	'absTV_60.dat' u 1:3:4 with errorbars ,\
	'absTV_60.dat' u 1:3 with lines ,\
	'absCable_box.dat' u 1:3:4 with errorbars ,\
	'absCable_box.dat' u 1:3 with lines ,\
	'absFloor_lamp.dat' u 1:3:4 with errorbars ,\
	'absFloor_lamp.dat' u 1:3 with lines ,\
	'absFloor_lamp.dat' u 1:3:4 with errorbars ,\
	'absFloor_lamp.dat' u 1:3 with lines ,\
	'absFloor_lamp.dat' u 1:3:4 with errorbars ,\
	'absFloor_lamp.dat' u 1:3 with lines ,\
	'absComputer_Dell.dat' u 1:3:4 with errorbars ,\
	'absComputer_Dell.dat' u 1:3 with lines ,\
	'absClock.dat' u 1:3:4 with errorbars ,\
	'absClock.dat' u 1:3 with lines ,\
	'absLamp.dat' u 1:3:4 with errorbars ,\
	'absLamp.dat' u 1:3 with lines ,\
	'absBox_fan.dat' u 1:3:4 with errorbars ,\
	'absBox_fan.dat' u 1:3 with lines