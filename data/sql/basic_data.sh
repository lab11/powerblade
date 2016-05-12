#!/bin/bash

# Parse the command line options
while [[ $# > 0 ]]
do
key="$1"

case $key in
	-h|--help)
	printf "\n"
	printf "Basic Data Script\n\n"
	printf "To configure:\n"
	printf "  mysql_config_editor set --login-path=resistor --host=[hostname] --user=[user] --password\n"
	printf "  Enter password when prompted.\n  Password will be saved encrypted at ~/.mylogin.cnf\n\n"
	printf "Parameters:\n"
	printf "  -f: Path to device list. List should be deviceMAC without ':', separated by newline\n"
	printf "  -d: Device name, deviceMAC without ':'. -d is ignored if -f is specified\n"
	printf "  -t: Query time in minutes. Currently queries are for the past t minutes ending now in UTC\n"
	printf "  -e: End time in 'YYYY-MM-DD HH:MM:SS'. Defaults to now."
	printf "  -b: (No argument required). Display along-side energy bridge data\n"
	printf "  -o: Specify path to save pdf. Must not exist.\n"
	printf "  -h: Display this help (no query is run)\n\n"
	printf "For a 120 minute query over c098e5700012 (default settings):\n"
	printf "  ./basic_data.sh\n\n"
	printf "For a 60 minute query over the devices listed in deviceList.txt:\n"
	printf "  ./basic_data.sh -f deviceList.txt -t 60\n\n"
	exit
	shift
	;;
	-f|--file)
	FILENAME="$2"
	shift
	;;
	-d|--device)
	SQLDEVICE="$2"
	shift
	;;
	-t|--time)
	DURTIME="$2"
	shift
	;;
	-e|--end)
	ENDTIME="$2"
	shift
	;;
	-b|--bridge)
	echo "Using Energy Bridge Data"
	EBRIDGE=1
	shift
	;;
	-o|--outfile)
	OUTFILE="$2"
	shift
	;;
	-s|--server)
	DB="$2"
	shift
	;;
    *)
            # unknown option
    ;;
esac
shift # past argument or value
done

# Used to extend the figure above the energy bridge line
ebridge_expansion=1.2

if [[ -n "${DURTIME+1}" ]]; then
	echo "Query over ${DURTIME} minutes"
else
	DURTIME="120"
	echo "Query over ${DURTIME} minutes"
fi

if [[ -n "${ENDTIME+1}" ]]; then
	ENDTIME="'${ENDTIME}'"
	echo "Ending at ${ENDTIME}"
else
	ENDTIME=$(date -u +%Y-%m-%d\ %H:%M:%S)
	ENDTIME="'${ENDTIME}'"
	echo "Ending now (${ENDTIME})"
fi

if [[ -n "${DB+1}" ]]; then
	if [ "${DB}" = "aws" ]; then
		DB_STRING="aws powerblade"
		PDAT="dat_powerblade"
		BDAT="dat_blees"
		BLL="inf_blees_light_lookup"
		BBIN="upd_blees_binary"
		BPWR="upd_blees_power"
		OVPWR="upd_overall_power"
		RCPWR="upd_recent_power"
		SHTMC="upd_overall_power_shortmac"
		echo "Accessing AWS"
	else
		DB_STRING="resistor whisperwood"
		PDAT="powerblade_test"
		BDAT="blees_test"
		BLL="blees_light_lookup"
		BBIN="blees_binary"
		BPWR="blees_power"
		OVPWR="overall_power"
		RCPWR="recent_power"
		SHTMC="overall_power_shortmac"
		echo "Accessing Umich"
	fi
else
	DB_STRING="resistor whisperwood"
	PDAT="powerblade_test"
	BDAT="blees_test"
	BLL="blees_light_lookup"
	BBIN="blees_binary"
	BPWR="blees_power"
	OVPWR="overall_power"
	RCPWR="recent_power"
	SHTMC="overall_power_shortmac"
	echo "Accessing Umich"
fi

SQLLOGIN="mysql --login-path=${DB_STRING} -e"

# Update Tables
./update_tables.sh

# This is really shameless... im sorry
DEVICELIST_TEMP=""
if [[ -n "${FILENAME+1}" ]]; then
	while read dev; do
		if [[ ${dev:0:1} != "#" ]]; then
			DEVICELIST_TEMP="${DEVICELIST_TEMP} OR deviceMAC='${dev}'"
		fi
	done <"${FILENAME}"
	DEVICELIST_TEMP="${DEVICELIST_TEMP:3}"
elif [[ -n "${SQLDEVICE+1}" ]]; then
	DEVICELIST_TEMP="deviceMAC='${SQLDEVICE}'"
else
	DEVICELIST_TEMP="deviceMAC='c098e5700012'"
fi
echo "${DEVICELIST_TEMP}"
DEVICELIST_TEMP="(${DEVICELIST_TEMP})"

echo "Creating Calendar"
eval "${SQLLOGIN} \"DROP TABLE IF EXISTS calendar;\""
eval "${SQLLOGIN} \"CREATE TABLE calendar (timestamp datetime,
	deviceMAC char(12), shortMAC int(11), index(timestamp),index(shortMAC));\""
eval "${SQLLOGIN} \"INSERT INTO calendar
select t2.timestamp, t1.deviceMAC, conv(concat(case when substring(deviceMAC,7,1)='7' then '1' else '0' end, right(deviceMAC,2)),16,10) from
(select deviceMAC from device_list where ${DEVICELIST_TEMP} group by deviceMAC) t1
cross join
(select a.Date as timestamp
from (
    select ${ENDTIME} - INTERVAL (a.a + (10 * b.a) + (100 * c.a) + (1000 * d.a) + (10000 * e.a) + (100000 * f.a)) SECOND as Date
    from (select 0 as a union all select 1 union all select 2 union all select 3 union all select 4 union all select 5 union all select 6 union all select 7 union all select 8 union all select 9) as a
    cross join (select 0 as a union all select 1 union all select 2 union all select 3 union all select 4 union all select 5 union all select 6 union all select 7 union all select 8 union all select 9) as b
    cross join (select 0 as a union all select 1 union all select 2 union all select 3 union all select 4 union all select 5 union all select 6 union all select 7 union all select 8 union all select 9) as c
    cross join (select 0 as a union all select 1 union all select 2 union all select 3 union all select 4 union all select 5 union all select 6 union all select 7 union all select 8 union all select 9) as d
    cross join (select 0 as a union all select 1 union all select 2 union all select 3 union all select 4 union all select 5 union all select 6 union all select 7 union all select 8 union all select 9) as e
    cross join (select 0 as a union all select 1 union all select 2 union all select 3 union all select 4 union all select 5 union all select 6 union all select 7 union all select 8 union all select 9) as f
) a
where a.Date between date_sub(${ENDTIME}, INTERVAL ${DURTIME} MINUTE) AND ${ENDTIME} order by a.Date asc) t2;\""

#echo "Creating subset of power table"
#mysql --login-path=resistor whisperwood -e "DROP TABLE IF EXISTS overall_power_window; CREATE TABLE overall_power_window as select * from overall_power_shortmac where timestamp between date_sub(${ENDTIME}, INTERVAL ${DURTIME} MINUTE) and ${ENDTIME}"
echo "Creating Final Overall Power Table. This may take several minutes depending on query"
eval "${SQLLOGIN} \"DROP TABLE IF EXISTS overall_power_filled;\""
eval "${SQLLOGIN} \"CREATE TABLE overall_power_filled AS
SELECT t1.*, (select power from overall_power_shortmac where id=max(t2.ID)) as power
FROM calendar t1
JOIN (select * from overall_power_shortmac where timestamp between date_sub(${ENDTIME}, INTERVAL ${DURTIME} MINUTE) and ${ENDTIME}) t2
ON (t2.timestamp BETWEEN date_sub(t1.timestamp, INTERVAL 1 MINUTE) AND t1.timestamp)
AND t1.shortMAC=t2.shortMAC
GROUP BY t1.timestamp, t1.shortMAC;\""

#(select power from recent_power where id=max(t2.ID)) as power

# mysql --login-path=resistor whisperwood -e "CREATE TABLE overall_power_filled AS
# select t1.*, (select power from recent_power where id=max(t2.ID)) as power
# from calendar_sub t1
# join recent_power t2
# on (t2.timestamp between date_sub(t1.timestamp, INTERVAL 1 MINUTE) and t1.timestamp)
# and t1.deviceMAC=t2.deviceMAC
# GROUP BY t1.timestamp, t1.deviceMAC;"

# mysql --login-path=resistor whisperwood -e "CREATE TABLE overall_power_filled AS
# select t1.*, t2.power
# from calendar_sub t1
# join recent_power t2
# on t2.id=(select max(t2b.id)
# from recent_power t2b 
# where t2b.timestamp between date_sub(t1.timestamp, INTERVAL 1 MINUTE) and t1.timestamp
# and t1.shortMAC=t2b.shortMAC);"



DEVICELIST=""
PLTLINE=""
if [[ -n "${FILENAME+1}" ]]; then
	while read dev; do
		if [[ ${dev:0:1} != "#" ]]; then
			DEVICELIST="${DEVICELIST} OR deviceMAC='${dev}'"
			eval "${SQLLOGIN} \"SELECT date_sub(timestamp, INTERVAL 4 HOUR),power from overall_power_filled WHERE deviceMAC='${dev}' and timestampdiff(minute,timestamp,${ENDTIME}) between 0 and ${DURTIME} group by timestamp order by timestamp asc;\" > \"${dev}\".csv"
			if [ -s "${dev}".csv ]; then
				PLTLINE="${PLTLINE},\x5C\n\t\"${dev}.csv\" u 1:2 with lines notitle "
			else
				echo "No data points for ${dev}"
			fi
		fi
	done <"${FILENAME}"
	DEVICELIST="${DEVICELIST:3}"
elif [[ -n "${SQLDEVICE+1}" ]]; then
	DEVICELIST="deviceMAC='${SQLDEVICE}'"
else
	DEVICELIST="deviceMAC='c098e5700012'"
fi
DEVICELIST="(${DEVICELIST})"
#echo $DEVICELIST

echo
echo "Running MySQL Query"

if [[ -n "${EBRIDGE+1}" ]]; then
	mysql --login-path=resistor whisperwood -e "SET @end_time = date_sub(${ENDTIME}, INTERVAL 4 HOUR);SELECT timestamp,((1000*max(power))-0) FROM energy_bridge
	WHERE timestamp BETWEEN date_sub(@end_time, INTERVAL ${DURTIME} MINUTE) and @end_time
	AND house_name != 'test'
	GROUP BY timestamp
	ORDER BY timestamp asc;" > ebridge.csv
	maxpower=$(mysql --login-path=resistor whisperwood -se "SET @end_time = date_sub(${ENDTIME}, INTERVAL 4 HOUR); SELECT (${ebridge_expansion}*1000*max(power)) FROM energy_bridge WHERE timestamp BETWEEN date_sub(@end_time, INTERVAL ${DURTIME} MINUTE) AND @end_time;")
	PLTLINE="${PLTLINE},\x5C\n\t\"ebridge.csv\" u 1:2 with linespoints title \"Energy Bridge\" "
fi


#mysql --login-path=resistor whisperwood -e "SELECT date_sub(timestamp, INTERVAL 4 HOUR),sum(power) as sum FROM overall_power_filled group by timestamp order by timestamp asc;" > sumPower.csv
eval "${SQLLOGIN} \"SET @weight=1;select date_sub(timestamp, INTERVAL 4 HOUR),@x:=Round((@weight*@x+(10-@weight)*sum(power))/10,2) as sum from overall_power_filled join ( select @x:=1 ) as dummy group by timestamp order by timestamp asc;\" > sumPower.csv"
echo "Finishing Plotting File"
cat dataviewer.plt > temp.plt
printf "set xtics ${DURTIME}*60/10 rotate by 70 offset -2.9,-4.65\n\n" >> temp.plt
printf "set yrange [-2:${maxpower}]\n\n" >> temp.plt
if [ -s sumPower.csv ]; then
	printf "plot \"sumPower.csv\" u 1:2 with lines title \"Calc. Sum\"${PLTLINE}" >> temp.plt
else
	printf "plot 0 with lines title \"Calc. Sum\"${PLTLINE}" >> temp.plt
fi

echo "Plotting"
gnuplot temp.plt
epstopdf temp.eps
open temp.pdf

if [[ -n "${OUTFILE+1}" ]]; then
	if [ -e "${OUTFILE}" ]; then 
		echo "Output file already exists"
	else
		cp temp.pdf "${OUTFILE}"
	fi
fi

rm temp.eps


