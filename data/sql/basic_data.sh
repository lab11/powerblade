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
	printf "  -e: (No argument required). Display along-side energy bridge data\n"
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
    *)
            # unknown option
    ;;
esac
shift # past argument or value
done

#echo
#read -s -p 'Enter MySql Password: ' pwd
#echo

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
	ENDTIME="utc_timestamp()"
	echo "Ending now"
fi

echo "Generating BLEES binary data"
mysql --login-path=resistor whisperwood -e "INSERT INTO blees_binary 
SELECT t1.*,t2.avg_lux,
CASE WHEN t1.lux > t2.avg_lux THEN 1 ELSE 0 END AS 'onoff'
FROM blees_test t1
JOIN (
SELECT deviceMAC,AVG(lux) AS avg_lux FROM blees_test GROUP BY deviceMAC
) t2
ON t1.deviceMAC=t2.deviceMAC
WHERE t1.id>(SELECT max(id) FROM blees_binary)
ORDER BY t1.deviceMAC, t1.timestamp;"

echo "Generating BLEES power data"
mysql --login-path=resistor whisperwood -e "INSERT INTO blees_power
SELECT t1.id, t1.gatewayMAC, t1.deviceMAC, t1.timestamp,
CASE WHEN t1.onoff=1 THEN t2.power ELSE 0 END AS power
FROM blees_binary t1
JOIN blees_light_lookup t2
ON t2.deviceMAC=t1.deviceMAC
WHERE t1.id>(SELECT max(id) FROM blees_power)
ORDER BY t1.deviceMAC;"

echo "Inserting PowerBlade & BLEES data"
mysql --login-path=resistor whisperwood -e "INSERT INTO overall_power (pb_id, gatewayMAC, deviceMAC, power, timestamp)
SELECT id, gatewayMAC, deviceMAC, power, timestamp
FROM powerblade_test t1 WHERE t1.id>(SELECT max(pb_id) FROM overall_power) OR
0=(SELECT count(pb_id) FROM overall_power)
ORDER BY timestamp ASC;
INSERT INTO overall_power (bl_id, gatewayMAC, deviceMAC, power, timestamp)
SELECT id, gatewayMAC, deviceMAC, power, timestamp
FROM blees_power t2 WHERE t2.id>(SELECT max(bl_id) FROM overall_power) OR
0=(SELECT count(bl_id) FROM overall_power)
ORDER BY timestamp ASC;"

# echo "Inserting BLEES data"
# mysql --login-path=resistor whisperwood -e "INSERT INTO overall_power (bl_id, gatewayMAC, deviceMAC, power, timestamp)
# SELECT id, gatewayMAC, deviceMAC, power, timestamp
# FROM blees_power t2 WHERE t2.id>(SELECT max(bl_id) FROM overall_power) OR
# 0=(SELECT count(bl_id) FROM overall_power)
# ORDER BY timestamp ASC;"

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
mysql --login-path=resistor whisperwood -e "DROP TABLE IF EXISTS calendar;"
mysql --login-path=resistor whisperwood -e "CREATE TABLE calendar AS
select t2.timestamp as timestamp, t1.deviceMAC as deviceMAC from
(select deviceMAC from overall_power where ${DEVICELIST_TEMP} group by deviceMAC) t1
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
where a.Date between date_sub(${ENDTIME}, INTERVAL ${DURTIME} MINUTE) AND ${ENDTIME} order by a.Date asc) t2;"

echo "Creating Final Overall Power Table. This may take several minutes depending on query"
mysql --login-path=resistor whisperwood -e "DROP TABLE IF EXISTS overall_power_filled;"
mysql --login-path=resistor whisperwood -e "CREATE TABLE overall_power_filled AS
SELECT t1.*, (select power from overall_power where id=max(t2.ID)) as power
FROM calendar t1
JOIN overall_power t2
ON (t2.timestamp BETWEEN date_sub(t1.timestamp, INTERVAL 1 MINUTE) AND t1.timestamp)
AND t1.deviceMAC=t2.deviceMAC
GROUP BY t1.timestamp, t1.deviceMAC;"

DEVICELIST=""
PLTLINE=""
if [[ -n "${FILENAME+1}" ]]; then
	while read dev; do
		if [[ ${dev:0:1} != "#" ]]; then
			DEVICELIST="${DEVICELIST} OR deviceMAC='${dev}'"
			mysql --login-path=resistor whisperwood -e "SELECT timestamp,power from overall_power_filled WHERE deviceMAC='${dev}' and timestampdiff(minute,timestamp,${ENDTIME}) between 0 and ${DURTIME} group by timestamp order by timestamp asc;" > "${dev}".csv
			if [ -s "$dev" ]; then
				PLTLINE="${PLTLINE},\x5C\n\t\"${dev}.csv\" u 1:2 with lines title \"${dev}\" "
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
	mysql --login-path=resistor whisperwood -e "SET @end_time = date_sub(${ENDTIME}, INTERVAL 4 HOUR);SELECT date_add(timestamp,INTERVAL 4 HOUR),((1000*max(power))-0) FROM energy_bridge
	WHERE timestamp BETWEEN date_sub(@end_time, INTERVAL ${DURTIME} MINUTE) and @end_time
	AND house_name != 'test'
	GROUP BY timestamp
	ORDER BY timestamp asc;" > ebridge.csv
	PLTLINE="${PLTLINE},\x5C\n\t\"ebridge.csv\" u 1:2 with lines title \"Energy Bridge\" "
fi


mysql --login-path=resistor whisperwood -e "SELECT timestamp,sum(power) as sum FROM overall_power_filled WHERE ${DEVICELIST} and timestampdiff(minute,timestamp,${ENDTIME}) between 0 and ${DURTIME} group by timestamp order by timestamp asc;" > sumPower.csv

echo "Finishing Plotting File"
cat dataviewer.plt > temp.plt
printf "set xtics ${DURTIME}*60/10 rotate by 70 offset -2.9,-4.65\n" >> temp.plt
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

#rm temp.plt
rm temp.eps


