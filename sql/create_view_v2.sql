# Creation of the views for success

SHOW FULL TABLES IN powerblade WHERE TABLE_TYPE LIKE 'VIEW';


# Create views for active gateways, powerblades, blinks, blees, and monjolos
# This is a list of the devices that should be active
# The body of the query selects the highest id value for each device MAC address

alter VIEW most_recent_gateways AS
SELECT t1.* from inf_gw_lookup t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM inf_gw_lookup t2 WHERE t1.gatewayMAC=t2.gatewayMAC and t1.location=t2.location)
and t1.room is not null;

create view valid_gateways as
SELECT * from most_recent_gateways WHERE
startTime < utc_timestamp() AND
(remTime is NULL OR remTime > utc_timestamp());

ALTER VIEW active_gateways AS
SELECT * from most_recent_gateways WHERE
startTime < utc_timestamp() AND
(remTime is NULL OR remTime > utc_timestamp()) AND
endTime > utc_timestamp();

ALTER VIEW most_recent_powerblades AS
SELECT t1.* FROM inf_pb_lookup t1 WHERE 
t1.id=(SELECT MAX(t2.id) FROM inf_pb_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC and t1.deviceName=t2.deviceName);

CREATE VIEW valid_powerblades AS
SELECT * from most_recent_powerblades WHERE
startTime < utc_timestamp() AND
(remTime is NULL OR remTime > utc_timestamp());

ALTER VIEW active_powerblades AS
SELECT * from most_recent_powerblades WHERE
startTime < utc_timestamp() AND
(remTime is NULL OR remTime > utc_timestamp()) AND
endTime > utc_timestamp();

CREATE VIEW most_recent_blinks AS
SELECT t1.* FROM inf_blink_lookup t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM inf_blink_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC);

ALTER VIEW active_blinks AS
SELECT t1.* FROM inf_blink_lookup t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM inf_blink_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC) AND
((startTime < utc_timestamp()) AND ((remTime is NULL) OR (remTime > utc_timestamp())));

ALTER VIEW active_lights AS
SELECT t1.* FROM inf_light_lookup t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM inf_light_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC) AND
((startTime < utc_timestamp()) AND ((remTime is NULL) OR (remTime > utc_timestamp())));

CREATE VIEW most_recent_lights AS 
SELECT t1.* FROM inf_light_lookup t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM inf_light_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC);

ALTER VIEW active_devices AS
SELECT deviceMAC, deviceName, location, category, deviceType from active_powerblades
UNION SELECT deviceMAC, deviceName, location, 'Lighting', 'Lighting' from active_lights
UNION SELECT deviceMAC, room, location, 'Lighting', 'Lighting' from active_blinks;

create view valid_devices as
SELECT deviceMAC, deviceName, location, category, deviceType from valid_powerblades
UNION SELECT deviceMAC, deviceName, location, 'Lighting', 'Lighting' from active_lights
UNION SELECT deviceMAC, room, location, 'Lighting', 'Lighting' from active_blinks;

ALTER VIEW most_recent_devices AS
SELECT deviceMAC, deviceName, location, category, deviceType from most_recent_powerblades
UNION SELECT deviceMAC, deviceName, location, 'Lighting', 'Lighting' from most_recent_lights
UNION SELECT deviceMAC, room, location, 'Lighting', 'Lighting' from most_recent_blinks;

CREATE VIEW avg_lux AS
SELECT deviceMAC, avg(lux) as avgLux FROM dat_blees FORCE INDEX (devLux)
group by deviceMAC;


# Create views for yesterday's data

CREATE VIEW yest_data_pb AS
SELECT * FROM dat_powerblade
WHERE timestamp>subdate(utc_timestamp(),1) AND timestamp<utc_timestamp();

CREATE VIEW yest_data_blink AS
SELECT * FROM dat_blink
WHERE timestamp>subdate(utc_timestamp(),1) AND timestamp<utc_timestamp();

CREATE VIEW yest_data_light AS
SELECT gatewayMAC, deviceMAC, timestamp FROM dat_ligeiro
WHERE timestamp>subdate(utc_timestamp(),1) AND timestamp<utc_timestamp()
UNION
SELECT gatewayMAC, deviceMAC, timestamp FROM dat_blees
WHERE timestamp>subdate(utc_timestamp(),1) AND timestamp<utc_timestamp();


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




CREATE VIEW most_recent_gnd_truth AS
SELECT t1.* FROM dat_gnd_truth t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM dat_gnd_truth t2
WHERE t1.location=t2.location AND t1.dayst=t2.dayst);




ALTER VIEW mr_maxPower_pb AS
SELECT t1.* from perm_maxPower_pb t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM perm_maxPower_pb t2 WHERE t1.deviceMAC=t2.deviceMAC);

CREATE VIEW mr_avgPower_pb AS
SELECT t1.* from perm_avgPower_pb t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM perm_avgPower_pb t2 WHERE t1.deviceMAC=t2.deviceMAC);

drop view mr_maxPower_pb;
drop view mr_avgPower_pb;


show processlist;
select * from perm_maxPower_pb;
select * from mr_maxPower_pb;
select * from mr_avgPower_pb;

describe final_results;
describe final_gnd;

CREATE VIEW mr_final_results AS
SELECT t1.* from final_results t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM final_results t2 WHERE t1.deviceMAC=t2.deviceMAC);

ALTER VIEW mr_final_gnd AS
SELECT t1.* from final_gnd t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM final_gnd t2 WHERE t1.location=t2.location);

select * from mr_final_gnd;

CREATE VIEW mr_avgPower_pb AS
SELECT t1.* from perm_avgPower_pb t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM perm_avgPower_pb t2 WHERE t1.deviceMAC=t2.deviceMAC);


alter view mr_final_gnd_corr as
select t1.location, t1.startDate, t1.endDate, t1.duration, t1.truthDays, t1.missingDays, t1.totMeas, t1.totGnd, 
(select count(*) from most_recent_gnd_truth t2 where t1.location=t2.location and t1.startDate<=t2.dayst and t1.endDate>=t2.dayst) as fullTruth,
t1.duration-(select count(*) from most_recent_gnd_truth t2 where t1.location=t2.location and t1.startDate<=t2.dayst and t1.endDate>=t2.dayst) as fullMissing,
(select avg(energy) from most_recent_gnd_truth t2 where t1.location=t2.location and t1.startDate<=t2.dayst and t1.endDate>=t2.dayst) as fullGnd
from mr_final_gnd t1;

select * from mr_final_gnd_corr order by location asc;






create view dev_actResets as
select t1.dayst, t1.deviceMAC, t1.minEnergy, t1.devReset, t1.minTs,
case when t1.devReset=1 and (select min(energy) from dat_powerblade force index(devTimeEnergy) 
where deviceMAC=t1.deviceMAC and timestamp=t1.minTs and energy!=2.24)>1.75 then 1 else 0 end as actReset
from dev_resets t1;

select * from dev_actResets;

select * from dat_powerblade where deviceMAC='c098e570005d' and timestamp='2017-03-09 00:00:00';

select * from inf_pb_lookup where location=0;
select * from active_devices where location=0;


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

































