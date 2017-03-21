set terminal postscript enhanced eps solid color font "Helvetica,14" size 8in,2.0in
set output "breakdown.eps"

#set title "Power Supplied from AC/DC"

#set border 3
#set xtics nomirror
#set ytics nomirror

#set style line 1 lt 4  ps 1.2 pt 7 lw 5 lc rgb "#d7191c"
#set style line 2 lt 1  ps 1.2 pt 2 lw 5 lc rgb "#fdae61"
#set style line 4 lt 1  ps 1.5 pt 7 lw 5 lc rgb "#2b83ba"

#set xlabel "Load Current (uA)"
#set ylabel "Supply Output Power (mW)"

#set xrange [0:6E-8]
#set yrange [0:2000]
#set y2range [0:15]
#set y2label "I / Vol Ratio (mA/cm^3)"
#set xtics (".01" 1E-8, ".02" 2E-8, ".03" 3E-8, ".04" 4E-8, ".05" 5E-8, ".06" 6E-8)
#set y2tics (5, 10, 15)

unset key

set boxwidth 0.5
set style fill solid 1.00 border lt -1

set multiplot layout 2,1

unset xtics

set lmargin 10
set ylabel "Energy Use (kWh)" offset 1,0 font ", 12"
set yrange[0:1000]

set size 1,0.38
set origin 0,0.60

set label at 54.6, 1100 "2299" center font ", 12"
set label at 56.4, 1100 "2613" center font ", 12"
set key top left font ", 12"

plot "energy_bl.dat" using 1:3 with boxes fc rgb "#4b97c8" title "BLEES", \
	 "energy_pb.dat" using 1:3 with boxes fc rgb "#ac0a0f" title "PowerBlade"

unset label
unset key

set logscale y

#set xtics (\
#	"c098e5700059" 0, \
#	"c098e5700039" 1, \
#	"c098e5700037" 2, \
#	"c098e5700060" 3, \
#	"c098e570006F" 4, \
#	"c098e5300056" 5, \
#	"c098e5700048" 6, \
#	"c098e5700066" 7, \
#	"c098e5700063" 8, \
#	"c098e570005D" 9, \
#	"c098e570006D" 10, \
#	"c098e5700052" 11, \
#	"c098e5700065" 12, \
#	"c098e570003E" 13, \
#	"c098e570005B" 14, \
#	"c098e570004C" 15, \
#	"c098e5700055" 16, \
#	"c098e570004F" 17, \
#	"c098e530002C" 18, \
#	"c098e5300031" 19, \
#	"c098e5700053" 20, \
#	"c098e5700050" 21, \
#	"c098e5700051" 22, \
#	"c098e570004D" 23, \
#	"c098e530001B" 24, \
#	"c098e5700068" 25, \
#	"c098e570003C" 26, \
#	"c098e570004A" 27, \
#	"c098e5700054" 28, \
#	"c098e5300033" 29, \
#	"c098e570004E" 30, \
#	"c098e570004B" 31, \
#	"c098e570005A" 32, \
#	"c098e5700061" 33, \
#	"c098e5700038" 34, \
#	"c098e5700049" 35, \
#	"c098e570003A" 36, \
#	"c098e5700071" 37, \
#	"c098e5700033" 38, \
#	"c098e5300048" 39, \
#	"c098e5300049" 40, \
#	"c098e5700036" 41, \
#	"c098e5700035" 42, \
#	"c098e5300034" 43, \
#	"c098e5300029" 44, \
#	"c098e5300038" 45, \
#	"c098e5300030" 46, \
#	"c098e5300052" 47, \
#	"c098e5700070" 48, \
#	"c098e5700020" 49, \
#	"c098e5700030" 50, \
#	"c098e5700012" 51, \
#	"c098e570003D" 52, \
#	"c098e5700034" 53, \
#	"c098e5700009" 54, \
#	"c098e5700046" 55, \
#	"c098e570003B" 56\
#	)

set bmargin 5.5
set xtics (\
	"Desk Lamp" 0, \
	"Phone Charger" 1, \
	"Bedroom Lamp" 2, \
	"Gateway 2" 3, \
	"Laptop Charger" 4, \
	"Bathroom Light" 5, \
	"Bed Lamp" 6, \
	"Night Light" 7, \
	"Box Fan" 8, \
	"Harmony Charger" 9, \
	"Computer Monitor" 10, \
	"Phone Charger" 11, \
	"Box Fan" 12, \
	"Phone Charger" 13, \
	"Ethernet Switch" 14, \
	"Paper Shredder" 15, \
	"Laptop Charger" 16, \
	"Computer Monitor" 17, \
	"Bedroom Light" 18, \
	"Closet Light" 19, \
	"Ethernet Switch" 20, \
	"Desktop Computer" 21, \
	"Speakers" 22, \
	"Clock" 23, \
	"Closet Light" 24, \
	"Toaster" 25, \
	"Printer" 26, \
	"USB Hub" 27, \
	"Phone Charger" 28, \
	"Counter Light" 29, \
	"Gateway 3" 30, \
	"SmartMeter Receiver" 31, \
	"Gateway 1" 32, \
	"Roomba Charger" 33, \
	"Apple TV" 34, \
	"NUC Computer" 35, \
	"Coffee Maker" 36, \
	"Small Lamp" 37, \
	"Microwave" 38, \
	"Outdoor Closet Light" 39, \
	"Bathroom Light" 40, \
	"Smoker" 41, \
	"Laptop Charger" 42, \
	"Dining Room Light" 43, \
	"Guest Room Light" 44, \
	"Stair Light" 45, \
	"Kitchen Light" 46, \
	"Entry Flood Light" 47, \
	"Big Lamp" 48, \
	"Humidifier" 49, \
	"Xbox One" 50, \
	"Refrigerator" 51, \
	"Modem / Router" 52, \
	"Cable Box" 53, \
	"Amplifier" 54, \
	"Aero Garden" 55, \
	"Television" 56\
	)

set xtics  rotate by 45 right font ", 10"

set size 1,0.66
set origin 0,0
set yrange[1:5000]
set ylabel "Average Power (w)" offset 1,-1 font ", 12"
plot "energy_bl.dat" using 1:4 with boxes fc rgb "#4b97c8", \
	 "energy_pb.dat" using 1:4 with boxes fc rgb "#ac0a0f"

unset multiplot








