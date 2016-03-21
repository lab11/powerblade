#!/bin/bash

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




