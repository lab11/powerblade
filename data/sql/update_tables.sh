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
FROM powerblade_test t1 WHERE t1.id>(SELECT max(pb_id) FROM overall_power);
INSERT INTO overall_power (bl_id, gatewayMAC, deviceMAC, power, timestamp)
SELECT id, gatewayMAC, deviceMAC, power, timestamp
FROM blees_power t2 WHERE t2.id>(SELECT max(bl_id) FROM overall_power);"

echo "Inserting PowerBlade & BLEES data into recent"
mysql --login-path=resistor whisperwood -e "INSERT INTO recent_power (pb_id, gatewayMAC, deviceMAC, power, timestamp, shortMAC)
SELECT id, gatewayMAC, deviceMAC, power, timestamp, conv(right(deviceMAC,6), 16, 10)
FROM powerblade_test t1 WHERE t1.id>(SELECT max(pb_id) FROM recent_power);
INSERT INTO recent_power (bl_id, gatewayMAC, deviceMAC, power, timestamp, shortMAC)
SELECT id, gatewayMAC, deviceMAC, power, timestamp, conv(right(deviceMAC,6), 16, 10)
FROM blees_power t2 WHERE t2.id>(SELECT max(bl_id) FROM recent_power);"

# OR
#0=(SELECT count(pb_id) FROM overall_power)
#ORDER BY timestamp ASC;

# OR
#0=(SELECT count(bl_id) FROM overall_power)
#ORDER BY timestamp ASC;

echo "Inserting PowerBlade & BLEES data into shortMAC"
mysql --login-path=resistor whisperwood -e "INSERT INTO overall_power_shortmac (pb_id, gatewayMAC, deviceMAC, power, timestamp, shortMAC)
SELECT id, gatewayMAC, deviceMAC, power, timestamp, conv(concat(case when substring(deviceMAC,7,1)='7' then '1' else '0' end, right(deviceMAC,2)),16,10)
FROM powerblade_test t1 WHERE t1.id>(SELECT max(pb_id) FROM overall_power_shortmac);
INSERT INTO overall_power_shortmac (bl_id, gatewayMAC, deviceMAC, power, timestamp, shortMAC)
SELECT id, gatewayMAC, deviceMAC, power, timestamp, conv(concat(case when substring(deviceMAC,7,1)='7' then '1' else '0' end, right(deviceMAC,2)),16,10)
FROM blees_power t1 WHERE t1.id>(SELECT max(bl_id) FROM overall_power_shortmac);"

