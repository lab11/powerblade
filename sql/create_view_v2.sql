# Creation of the views for success

SHOW FULL TABLES IN powerblade WHERE TABLE_TYPE LIKE 'VIEW';


# Create views for active gateways, powerblades, blinks, blees, and monjolos
# This is a list of the devices that should be active
# The body of the query selects the highest id value for each device MAC address

CREATE VIEW active_gateways AS
SELECT t1.* FROM inf_gw_lookup t1 WHERE 
t1.id=(SELECT MAX(t2.id) FROM inf_gw_lookup t2 WHERE t1.gatewayMAC=t2.gatewayMAC) AND
((startTime < subdate(curdate(),1)) AND ((endTime is NULL) OR (endtime > curdate())));

CREATE VIEW most_recent_powerblades AS
SELECT t1.* FROM inf_pb_lookup t1 WHERE 
t1.id=(SELECT MAX(t2.id) FROM inf_pb_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC);

CREATE VIEW active_powerblades AS
SELECT t1.* FROM inf_pb_lookup t1 WHERE 
t1.id=(SELECT MAX(t2.id) FROM inf_pb_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC) AND
((startTime < subdate(curdate(),1)) AND ((endTime is NULL) OR (endtime > curdate())));

CREATE VIEW active_blinks AS
SELECT t1.* FROM inf_blink_lookup t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM inf_blink_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC) AND
((startTime < subdate(curdate(),1)) AND ((endTime is NULL) OR (endTime > curdate())));

CREATE VIEW active_lights AS
SELECT t1.* FROM inf_light_lookup t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM inf_light_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC) AND
((startTime < subdate(curdate(),1)) AND ((endTime is NULL) OR (endTime > curdate())));


# Create views for yesterday's data

CREATE VIEW yest_data_pb AS
SELECT * FROM dat_powerblade
WHERE timestamp>subdate(curdate(),1) AND timestamp<curdate();

CREATE VIEW yest_data_blink AS
SELECT * FROM dat_blink
WHERE timestamp>subdate(curdate(),1) AND timestamp<curdate();

CREATE VIEW yest_data_light AS
SELECT gatewayMAC, deviceMAC, timestamp FROM dat_ligeiro
WHERE timestamp>subdate(curdate(),1) AND timestamp<curdate()
UNION
SELECT gatewayMAC, deviceMAC, timestamp FROM dat_blees
WHERE timestamp>subdate(curdate(),1) AND timestamp<curdate();


# Create view for yesterday's gateway data

CREATE VIEW yest_data_gw AS
SELECT gatewayMAC, deviceMAC, timestamp FROM yest_data_pb UNION
SELECT gatewayMAC, deviceMAC, timestamp FROM yest_data_blink UNION
SELECT gatewayMAC, deviceMAC, timestamp FROM yest_data_light;


# Create views for yesterday's hitrate

CREATE VIEW yest_hr_pb AS
SELECT ROUND(UNIX_TIMESTAMP(timestamp)/(15 * 60)) AS timekey, MIN(timestamp) AS ts, gatewayMAC, deviceMAC, COUNT(id) AS count
FROM yest_data_pb
GROUP BY gatewayMAC, deviceMAC, timekey;

CREATE VIEW yest_hr_blink AS
SELECT ROUND(UNIX_TIMESTAMP(timestamp)/(15 * 60)) AS timekey, MIN(timestamp) AS ts, gatewayMAC, deviceMAC, COUNT(id) AS count
FROM yest_data_blink
GROUP BY gatewayMAC, deviceMAC, timekey;

CREATE VIEW yest_hr_light AS
SELECT ROUND(UNIX_TIMESTAMP(timestamp)/(15 * 60)) AS timekey, MIN(timestamp) AS ts, gatewayMAC, deviceMAC, COUNT(*) AS count
FROM yest_data_light
GROUP BY gatewayMAC, deviceMAC, timekey;


# Create viwe for yesterday's gateway hitrate

CREATE VIEW yest_hr_gw AS
SELECT ROUND(UNIX_TIMESTAMP(timestamp)/(15 * 60)) AS timekey, MIN(timestamp) AS ts, gatewayMAC, deviceMAC, COUNT(*) AS count
FROM yest_data_gw
GROUP BY gatewayMAC, deviceMAC, timekey;


# Create view for each device's success

CREATE VIEW success_powerblade AS
SELECT t1.deviceMAC, t1.deviceName, t1.location, t1.permanent, AVG(t2.count) AS count
FROM active_powerblades t1 LEFT JOIN yest_hr_pb t2
ON t1.deviceMAC=t2.deviceMAC
GROUP BY t1.deviceMAC
ORDER BY t1.location ASC, count ASC;

CREATE VIEW success_blink AS
SELECT t1.deviceMAC, t1.room AS deviceName, t1.location, 1 as permanent, AVG(t2.count) AS count
FROM active_blinks t1 LEFT JOIN yest_hr_blink t2
ON t1.deviceMAC=t2.deviceMAC
GROUP BY t1.deviceMAC
ORDER BY t1.location ASC, count ASC;

CREATE VIEW success_light AS
SELECT t1.deviceMAC, t1.deviceName, t1.location, 1 as permanent, AVG(t2.count) AS count
FROM active_lights t1 LEFT JOIN yest_hr_light t2
ON t1.deviceMAC=t2.deviceMAC
GROUP BY t1.deviceMAC
ORDER BY t1.location ASC, count ASC;


# Create view for the gateway success

CREATE VIEW success_gateway AS
SELECT t1.gatewayMAC, '' AS deviceName, t1.location, 1 AS permanent, avg(t2.count) AS count
FROM active_gateways t1 LEFT JOIN yest_hr_gw t2
ON t1.gatewayMAC=t2.gatewayMAC
GROUP BY t1.gatewayMAC
ORDER BY t1.location ASC, count ASC;


# Finally, get last seen for each

CREATE VIEW last_seen_pb AS
SELECT t1.deviceMAC AS deviceMAC, (SELECT t2.timestamp FROM dat_powerblade t2 WHERE t2.id=MAX(t1.id)) AS maxTime 
FROM dat_powerblade t1 GROUP BY t1.deviceMAC;

CREATE VIEW last_seen_blink AS
SELECT t1.deviceMAC AS deviceMAC, (SELECT t2.timestamp FROM dat_blink t2 WHERE t2.id=MAX(t1.id)) AS maxTime 
FROM dat_blink t1 GROUP BY t1.deviceMAC;

CREATE VIEW last_seen_light AS
SELECT t1.deviceMAC AS deviceMAC, (SELECT t2.timestamp FROM dat_blees t2 WHERE t2.id=MAX(t1.id)) AS maxTime
FROM dat_blees t1 GROUP BY t1.deviceMAC UNION
SELECT t3.deviceMAC AS deviceMAC, (SELECT t4.timestamp FROM dat_ligeiro t4 WHERE t4.id=MAX(t3.id)) AS maxTime
FROM dat_ligeiro t3 GROUP BY t3.deviceMAC;

CREATE VIEW dat_gateway AS
select t1.gatewayMAC as deviceMAC, (select t2.timestamp from dat_powerblade t2 where t2.id=max(t1.id)) as maxTime
from dat_powerblade t1 group by t1.gatewaymac
UNION ALL
select t1.gatewayMAC as deviceMAC, (select t2.timestamp from dat_blink t2 where t2.id=max(t1.id)) as maxTime
from dat_blink t1 group by t1.gatewaymac
UNION ALL
select t1.gatewayMAC as deviceMAC, (select t2.timestamp from dat_blees t2 where t2.id=max(t1.id)) as maxTime
from dat_blees t1 group by t1.gatewaymac
UNION ALL
select t1.gatewayMAC as deviceMAC, (select t2.timestamp from dat_ligeiro t2 where t2.id=max(t1.id)) as maxTime
from dat_ligeiro t1 group by t1.gatewaymac;

create view last_seen_gw as
SELECT deviceMAC, MAX(maxTime) FROM dat_gateway
GROUP BY deviceMAC;












-- SELECT * FROM active_gateways;
-- SELECT * FROM active_powerblades;
-- SELECT * FROM active_blinks;
-- SELECT * FROM active_lights;

-- select * from yesterday_data;
-- select * from yesterday_hitrate;
-- select * from gateway_success;
-- select * from powerblade_success;
-- select * from last_seen_gw;
-- select * from last_seen_pb;





-- select deviceMAC, max(timestamp) from dat_powerblade group by deviceMAC;

-- select t1.*, max(t2.timestamp) as 'last seen' from powerblade_success t1 left join dat_powerblade t2 on t1.deviceMAC=t2.deviceMAC;

-- explain select t1.* from dat_powerblade t1 where t1.id = (select max(t2.id) from dat_powerblade t2 where t1.deviceMAC=t2.deviceMAC);





-- select t1.*, t2.maxTime as last_seen from gateway_success t1 left join last_seen_gw t2 on t1.gatewayMAC=t1.gatewayMAC;

-- select t1.*, t2.maxTime as last_seen from powerblade_success t1 left join last_seen_pb t2 on t1.deviceMAC=t2.deviceMAC;

































