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
drop view yesterday_hitrate;
create view yesterday_hitrate as
select ROUND(UNIX_TIMESTAMP(t1.timestamp)/(15 * 60)) AS timekey, min(t1.timestamp) as ts, t1.gatewayMAC, t1.deviceMAC, count(t1.id) as count
from yesterday_data t1
group by t1.gatewayMAC, t1.deviceMAC, timekey;

CREATE VIEW yesterday_data AS
SELECT * FROM dat_powerblade
where timestamp>subdate(curdate(),1) and timestamp<curdate();

select * from yesterday_data;
select * from yesterday_hitrate;
select * from active_gateways;
select * from active_powerblades;
select * from gateway_success;
select * from powerblade_success;
select * from last_seen_gw;
select * from last_seen_pb;

create view gateway_success as
select t1.gatewayMAC, '' as deviceName, t1.location, 1 as permanent, avg(t2.count) as count
from active_gateways t1 left join yesterday_hitrate t2
on t1.gatewayMAC=t2.gatewayMAC
group by t1.gatewayMAC
order by t1.location asc, count asc;

create view powerblade_success as
select t1.deviceMAC, t1.deviceName, t1.location, t1.permanent, avg(t2.count) as count
from active_powerblades t1 left join yesterday_hitrate t2
on t1.deviceMAC=t2.deviceMAC
group by t1.deviceMAC
order by t1.location asc, count asc;

select deviceMAC, max(timestamp) from dat_powerblade group by deviceMAC;

select t1.*, max(t2.timestamp) as 'last seen' from powerblade_success t1 left join dat_powerblade t2 on t1.deviceMAC=t2.deviceMAC;

explain select t1.* from dat_powerblade t1 where t1.id = (select max(t2.id) from dat_powerblade t2 where t1.deviceMAC=t2.deviceMAC);

create view last_seen_gw as
select t1.gatewaymac as deviceMAC, (select t2.timestamp from dat_powerblade t2 where t2.id=max(t1.id)) as maxTime
from dat_powerblade t1 group by t1.gatewaymac;

create view last_seen_pb as
select t1.deviceMAC as deviceMAC, (select t2.timestamp from dat_powerblade t2 where t2.id=max(t1.id)) as maxTime 
from dat_powerblade t1 group by t1.deviceMAC;

select t1.*, t2.maxTime as last_seen from gateway_success t1 left join last_seen_gw t2 on t1.gatewayMAC=t1.gatewayMAC;

select t1.*, t2.maxTime as last_seen from powerblade_success t1 left join last_seen_pb t2 on t1.deviceMAC=t2.deviceMAC;





-- select * from dat_powerblade
-- where timestamp>'2016-10-12 00:00:00' and timestamp<'2016-10-13 00:00:00';

-- SELECT   *, ROUND(UNIX_TIMESTAMP(timestamp)/(15 * 60)) AS timekey
-- FROM     dat_powerblade_2
-- GROUP BY timekey limit 10;

create view active_gateways as
SELECT t1.* FROM inf_gw_lookup t1 WHERE 
t1.id=(SELECT MAX(t2.id) FROM inf_gw_lookup t2 WHERE t1.gatewayMAC=t2.gatewayMAC) and
((startTime < subdate(curdate(),1)) and ((endTime is NULL) OR (endtime > curdate())));

create view active_powerblades as
SELECT t1.* FROM inf_pb_lookup t1 WHERE 
t1.id=(SELECT MAX(t2.id) FROM inf_pb_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC) and
((startTime < subdate(curdate(),1)) and ((endTime is NULL) OR (endtime > curdate())));

SHOW FULL TABLES IN powerblade WHERE TABLE_TYPE LIKE 'VIEW';

-- CREATE VIEW most_recent_gateway_entry AS
-- SELECT t1.* FROM inf_gw_lookup t1 WHERE 
-- t1.id=(SELECT MAX(t2.id) FROM inf_gw_lookup t2 WHERE t1.gatewayMAC=t2.gatewayMAC);

-- CREATE VIEW most_recent_powerblade_entry AS
-- SELECT t1.* FROM inf_pb_lookup t1 WHERE
-- t1.id=(SELECT MAX(t2.id) FROM inf_pb_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC);

-- CREATE VIEW gateway_active AS
-- SELECT LOWER(gatewayMAC) AS gatewayMAC FROM 
-- most_recent_gateway_entry
-- WHERE ((utc_timestamp BETWEEN startTime AND endTime) OR (utc_timestamp > starttime AND endtime is NULL));

-- CREATE VIEW powerblade_active AS
-- SELECT LOWER(deviceMAC), location, permanent FROM 
-- (SELECT t1.* FROM inf_pb_lookup t1 WHERE 
-- 	t1.id=(SELECT MAX(t2.id) FROM inf_pb_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC)) yest_pb_active
-- WHERE ((utc_timestamp BETWEEN startTime AND endTime) OR (utc_timestamp > starttime AND endtime is NULL));




-- CREATE VIEW yesterday_active AS
-- SELECT t1.* FROM dat_powerblade t1
-- WHERE
-- (t1.deviceMAC IN
-- (SELECT LOWER(gatewayMAC) FROM 
-- most_recent_gateway_entry
-- WHERE ((utc_timestamp BETWEEN startTime AND endTime) OR (utc_timestamp > starttime AND endtime is NULL))) OR
-- t1.gatewayMAC IN
-- (SELECT LOWER(deviceMAC) FROM 
-- most_recent_powerblade_entry
-- WHERE ((utc_timestamp BETWEEN startTime AND endTime) OR (utc_timestamp > starttime AND endtime is NULL))));

-- WHERE DATE(t1.timestamp) = DATE(NOW() - INTERVAL 1 DAY) AND
