# Creation of the view of yesterday_active

-- SELECT LOWER(gatewayMAC), location, 1 FROM 
-- (SELECT t1.* FROM inf_gw_lookup t1 WHERE 
-- 	t1.id=(SELECT MAX(t2.id) FROM inf_gw_lookup t2 WHERE t1.gatewayMAC=t2.gatewayMAC)) yest_gw_active
-- WHERE ((utc_timestamp BETWEEN startTime AND endTime) OR (utc_timestamp > starttime AND endtime is NULL)) 
-- ORDER BY gatewayMAC DESC;

-- SELECT LOWER(deviceMAC), location, permanent FROM 
-- (SELECT t1.* FROM inf_pb_lookup t1 WHERE 
-- 	t1.id=(SELECT MAX(t2.id) FROM inf_pb_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC)) yest_pb_active
-- WHERE ((utc_timestamp BETWEEN startTime AND endTime) OR (utc_timestamp > starttime AND endtime is NULL)) 
-- ORDER BY deviceMAC DESC;

SHOW FULL TABLES IN powerblade WHERE TABLE_TYPE LIKE 'VIEW';

CREATE VIEW most_recent_gateway_entry AS
SELECT t1.* FROM inf_gw_lookup t1 WHERE 
t1.id=(SELECT MAX(t2.id) FROM inf_gw_lookup t2 WHERE t1.gatewayMAC=t2.gatewayMAC);

CREATE VIEW most_recent_powerblade_entry AS
SELECT t1.* FROM inf_pb_lookup t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM inf_pb_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC);

CREATE VIEW gateway_active AS
SELECT LOWER(gatewayMAC) AS gatewayMAC FROM 
most_recent_gateway_entry
WHERE ((utc_timestamp BETWEEN startTime AND endTime) OR (utc_timestamp > starttime AND endtime is NULL));

CREATE VIEW powerblade_active AS
SELECT LOWER(deviceMAC), location, permanent FROM 
(SELECT t1.* FROM inf_pb_lookup t1 WHERE 
	t1.id=(SELECT MAX(t2.id) FROM inf_pb_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC)) yest_pb_active
WHERE ((utc_timestamp BETWEEN startTime AND endTime) OR (utc_timestamp > starttime AND endtime is NULL));




CREATE VIEW yesterday_active AS
SELECT t1.* FROM dat_powerblade t1
WHERE
(t1.deviceMAC IN
(SELECT LOWER(gatewayMAC) FROM 
most_recent_gateway_entry
WHERE ((utc_timestamp BETWEEN startTime AND endTime) OR (utc_timestamp > starttime AND endtime is NULL))) OR
t1.gatewayMAC IN
(SELECT LOWER(deviceMAC) FROM 
most_recent_powerblade_entry
WHERE ((utc_timestamp BETWEEN startTime AND endTime) OR (utc_timestamp > starttime AND endtime is NULL))));

WHERE DATE(t1.timestamp) = DATE(NOW() - INTERVAL 1 DAY) AND
