#!/bin/bash

# Parse the command line options
while [[ $# > 0 ]]
do
key="$1"

case $key in
	-d|--database)
	DB="$2"
	shift
	;;
    *)
            # unknown option
    ;;
esac
shift # past argument or value
done

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

# echo "${SQLLOGIN} \"show tables;\""
# eval "${SQLLOGIN} \"show tables;\""
# exit

# mysql --login-path="${DB_STRING}" -e "show tables;"

# exit

echo "Generating BLEES binary data"
eval "${SQLLOGIN} \"INSERT INTO ${BBIN} 
SELECT t1.*,t2.avg_lux,
CASE WHEN t1.lux > t2.avg_lux THEN 1 ELSE 0 END AS 'onoff'
FROM ${BDAT} t1
JOIN (
SELECT deviceMAC,AVG(lux) AS avg_lux FROM ${BDAT} GROUP BY deviceMAC
) t2
ON t1.deviceMAC=t2.deviceMAC
WHERE t1.id>(SELECT max(id) FROM ${BBIN})
ORDER BY t1.deviceMAC, t1.timestamp;\""

echo "Generating BLEES power data"
eval "${SQLLOGIN} \"INSERT INTO ${BPWR}
SELECT t1.id, t1.gatewayMAC, t1.deviceMAC, t1.timestamp,
CASE WHEN t1.onoff=1 THEN t2.power ELSE 0 END AS power
FROM ${BBIN} t1
JOIN ${BLL} t2
ON t2.deviceMAC=t1.deviceMAC
WHERE t1.id>(SELECT max(id) FROM ${BPWR})
ORDER BY t1.deviceMAC;\""

echo "Inserting PowerBlade & BLEES data"
eval "${SQLLOGIN} \"INSERT INTO ${OVPWR} (pb_id, gatewayMAC, deviceMAC, power, timestamp)
SELECT id, gatewayMAC, deviceMAC, power, timestamp
FROM ${PDAT} t1 WHERE t1.id>(SELECT max(pb_id) FROM ${OVPWR});
INSERT INTO ${OVPWR} (bl_id, gatewayMAC, deviceMAC, power, timestamp)
SELECT id, gatewayMAC, deviceMAC, power, timestamp
FROM ${BPWR} t2 WHERE t2.id>(SELECT max(bl_id) FROM ${OVPWR});\""

echo "Inserting PowerBlade & BLEES data into recent"
eval "${SQLLOGIN} \"INSERT INTO ${RCPWR} (pb_id, gatewayMAC, deviceMAC, power, timestamp, shortMAC)
SELECT id, gatewayMAC, deviceMAC, power, timestamp, conv(right(deviceMAC,6), 16, 10)
FROM ${PDAT} t1 WHERE t1.id>(SELECT max(pb_id) FROM ${RCPWR});
INSERT INTO ${RCPWR} (bl_id, gatewayMAC, deviceMAC, power, timestamp, shortMAC)
SELECT id, gatewayMAC, deviceMAC, power, timestamp, conv(right(deviceMAC,6), 16, 10)
FROM ${BPWR} t2 WHERE t2.id>(SELECT max(bl_id) FROM ${RCPWR});\""

echo "Inserting PowerBlade & BLEES data into shortMAC"
eval "${SQLLOGIN} \"INSERT INTO ${SHTMC} (pb_id, gatewayMAC, deviceMAC, power, timestamp, shortMAC)
SELECT id, gatewayMAC, deviceMAC, power, timestamp, conv(concat(case when substring(deviceMAC,7,1)='7' then '1' else '0' end, right(deviceMAC,2)),16,10)
FROM ${PDAT} t1 WHERE t1.id>(SELECT max(pb_id) FROM ${SHTMC});
INSERT INTO ${SHTMC} (bl_id, gatewayMAC, deviceMAC, power, timestamp, shortMAC)
SELECT id, gatewayMAC, deviceMAC, power, timestamp, conv(concat(case when substring(deviceMAC,7,1)='7' then '1' else '0' end, right(deviceMAC,2)),16,10)
FROM ${BPWR} t1 WHERE t1.id>(SELECT max(bl_id) FROM ${SHTMC});\""

