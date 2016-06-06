#!/bin/bash

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

SQLLOGIN="mysql --login-path=${DB_STRING} -e"

echo "Querying most recent data"
eval



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


