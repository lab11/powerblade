# Creation of the views for success

# Create views for active gateways, powerblades, blinks, blees, and monjolos

# most_recent_[device] - for each inf_[device] table, the most recent entry for each device
# Select the highest id value for each device MAC address

alter VIEW most_recent_gateways AS
SELECT t1.* from inf_gw_lookup t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM inf_gw_lookup t2 WHERE t1.gatewayMAC=t2.gatewayMAC and t1.location=t2.location)
and t1.room is not null;

ALTER VIEW most_recent_powerblades AS
SELECT t1.* FROM inf_pb_lookup t1 WHERE 
t1.id=(SELECT MAX(t2.id) FROM inf_pb_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC and t1.deviceName=t2.deviceName);

ALTER VIEW most_recent_lights AS 
SELECT t1.* FROM inf_light_lookup t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM inf_light_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC);

ALTER VIEW most_recent_blinks AS
SELECT t1.* FROM inf_blink_lookup t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM inf_blink_lookup t2 WHERE t1.deviceMAC=t2.deviceMAC);

ALTER VIEW most_recent_devices AS
SELECT deviceMAC, deviceName, location, category, deviceType from most_recent_powerblades
UNION SELECT deviceMAC, deviceName, location, 'Overhead', 'Overhead' from most_recent_lights
UNION SELECT deviceMAC, room, location, 'Overhead', 'Overhead' from most_recent_blinks;


# valid_[device] - all devices in a most_recent_[device] table that have been installed and not removed
# removed means the device was removed from the study and should not be considered
# this is different than endTime, which is the time when that location is ended (and is no longer active)

create view valid_gateways as
SELECT * from most_recent_gateways WHERE
startTime < utc_timestamp() AND
(remTime is NULL OR remTime > utc_timestamp());

CREATE VIEW valid_powerblades AS
SELECT * from most_recent_powerblades WHERE
startTime < utc_timestamp() AND
(remTime is NULL OR remTime > utc_timestamp());

CREATE VIEW valid_lights AS
SELECT * FROM most_recent_lights WHERE
startTime < utc_timestamp() AND 
(remTime is NULL OR remTime > utc_timestamp());

CREATE VIEW valid_blinks AS
SELECT * FROM most_recent_blinks WHERE
startTime < utc_timestamp() AND 
(remTime is NULL OR remTime > utc_timestamp());

alter view valid_devices as
SELECT deviceMAC, deviceName, location, room, category, deviceType from valid_powerblades
UNION SELECT deviceMAC, deviceName, location, room, 'Overhead', 'Overhead' from valid_lights
UNION SELECT deviceMAC, room, location, room, 'Overhead', 'Overhead' from valid_blinks;



# active_[device] - all devices in a most_recent_[device] that are valid (see above) and that are active 
# active means that the endTime, the time that location is ended, has not yet happened

ALTER VIEW active_gateways AS
SELECT * from most_recent_gateways WHERE
startTime < utc_timestamp() AND
(remTime is NULL OR remTime > utc_timestamp()) AND
endTime > utc_timestamp();

ALTER VIEW active_powerblades AS
SELECT * from most_recent_powerblades WHERE
startTime < utc_timestamp() AND
(remTime is NULL OR remTime > utc_timestamp()) AND
endTime > utc_timestamp();

ALTER VIEW active_lights AS
SELECT * FROM most_recent_lights WHERE
startTime < utc_timestamp() AND 
(remTime is NULL OR remTime > utc_timestamp()) AND
endTime > utc_timestamp();

ALTER VIEW active_blinks AS
SELECT * FROM most_recent_blinks WHERE
startTime < utc_timestamp() AND 
(remTime is NULL OR remTime > utc_timestamp()) AND
endTime > utc_timestamp();

ALTER VIEW active_devices AS
SELECT deviceMAC, deviceName, location, category, deviceType from active_powerblades
UNION SELECT deviceMAC, deviceName, location, 'Overhead', 'Overhead' from active_lights
UNION SELECT deviceMAC, room, location, 'Overhead', 'Overhead' from active_blinks;


# yest_data_[device] - data for each device recorded in the last 24 hours
# 24 hours is the scope of the status script sql_status_v2.py - hitrate over the past 24 hours
# Because this is used for hitrate, BLEES and Ligeiro data is combined

CREATE VIEW yest_data_pb AS
SELECT * FROM dat_powerblade
WHERE timestamp>subdate(utc_timestamp(),1) AND timestamp<utc_timestamp();

CREATE VIEW yest_data_light AS
SELECT gatewayMAC, deviceMAC, timestamp FROM dat_ligeiro
WHERE timestamp>subdate(utc_timestamp(),1) AND timestamp<utc_timestamp()
UNION
SELECT gatewayMAC, deviceMAC, timestamp FROM dat_blees
WHERE timestamp>subdate(utc_timestamp(),1) AND timestamp<utc_timestamp();

CREATE VIEW yest_data_blink AS
SELECT * FROM dat_blink
WHERE timestamp>subdate(utc_timestamp(),1) AND timestamp<utc_timestamp();

CREATE VIEW yest_data_gw AS
SELECT gatewayMAC, deviceMAC, timestamp FROM yest_data_pb UNION
SELECT gatewayMAC, deviceMAC, timestamp FROM yest_data_blink UNION
SELECT gatewayMAC, deviceMAC, timestamp FROM yest_data_light;

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


# yest_hr_[device] - For each 15 minute interval in the yesterday data, total number of packets
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

CREATE VIEW yest_hr_gw AS
SELECT ROUND(UNIX_TIMESTAMP(timestamp)/(15 * 60)) AS timekey, MIN(timestamp) AS ts, gatewayMAC, deviceMAC, COUNT(*) AS count
FROM yest_data_gw
GROUP BY gatewayMAC, deviceMAC, timekey;


# success_[device] - average hitrate for each device

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

CREATE VIEW success_gateway AS
SELECT t1.gatewayMAC, '' AS deviceName, t1.location, 1 AS permanent, avg(t2.count) AS count
FROM active_gateways t1 LEFT JOIN yest_hr_gw t2
ON t1.gatewayMAC=t2.gatewayMAC
GROUP BY t1.gatewayMAC
ORDER BY t1.location ASC, count ASC;


# last_seen_[device] - last seen for each

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

create view last_seen_gw as
SELECT deviceMAC, MAX(maxTime) FROM dat_gateway
GROUP BY deviceMAC;





# Avg lux for BLEES
CREATE VIEW avg_lux AS
SELECT deviceMAC, avg(lux) as avgLux FROM dat_blees FORCE INDEX (devLux)
group by deviceMAC;





# Most recent ground truth entries for each location and each day
CREATE VIEW most_recent_gnd_truth AS
SELECT t1.* FROM dat_gnd_truth t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM dat_gnd_truth t2
WHERE t1.location=t2.location AND t1.dayst=t2.dayst);





# Most recent entry for each location from final_results
CREATE VIEW mr_final_results AS
SELECT t1.* from final_results t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM final_results t2 WHERE t1.deviceMAC=t2.deviceMAC);

# Most recent entry for each location from final_gnd
ALTER VIEW mr_final_gnd AS
SELECT t1.* from final_gnd t1 WHERE
t1.id=(SELECT MAX(t2.id) FROM final_gnd t2 WHERE t1.location=t2.location);

# Values of mr_final_gnd with the addition of any extra data found in most_recent_gnd_truth
alter view mr_final_gnd_corr as
select t1.location, t1.startDate, t1.endDate, t1.duration, t1.truthDays, t1.missingDays, t1.totMeas, t1.totGnd, 
(select count(*) from most_recent_gnd_truth t2 where t1.location=t2.location and t1.startDate<=t2.dayst and t1.endDate>=t2.dayst) as fullTruth,
t1.duration-(select count(*) from most_recent_gnd_truth t2 where t1.location=t2.location and t1.startDate<=t2.dayst and t1.endDate>=t2.dayst) as fullMissing,
(select avg(energy) from most_recent_gnd_truth t2 where t1.location=t2.location and t1.startDate<=t2.dayst and t1.endDate>=t2.dayst) as fullGnd,
t1.totMeas/(select avg(energy) from most_recent_gnd_truth t2 where t1.location=t2.location and t1.startDate<=t2.dayst and t1.endDate>=t2.dayst)*100 as pct
from mr_final_gnd t1;





# actResets - this view goes through the dev_resets (devices and days when the minimum energy is low) and determines if it was an actual reset
# In this case, an actual reset is: the minimum energy is low (device+day is in dev_resets) AND the earliest energy on that day is not low
# This means that the device started the day plugged in, and was then reset 
# This ignores non-permanent devices that were plugged in, used, and unplugged
# This misses non-permanent devices that are plugged and unplugged several times
# All powerblades with the new version (2.3.0) do not need this, as energy is actually stored non-volatile
create view dev_actResets as
select t1.dayst, t1.deviceMAC, t1.minEnergy, t1.devReset, t1.minTs,
case when t1.devReset=1 and (select min(energy) from dat_powerblade force index(devTimeEnergy) 
where deviceMAC=t1.deviceMAC and timestamp=t1.minTs and energy!=2.24)>1.75 then 1 else 0 end as actReset
from dev_resets t1;





# Lists of all categories and locations from the final results
# Used below to create mr_cat_breakdown
create view mr_final_categories as select category from mr_final_results group by category;
create view mr_final_locations as select location from mr_final_results group by location;

# Total category-based energy breakdown, filled in for all locations and categories
# The result is a list of [location, category, sum for that category]
# This is the equivalent of loc0_day_energy_full but for categories
alter view mr_cat_breakdown as
select t2.location, t1.category, case when t1.category in (select category from mr_final_results t3 where t2.location=t3.location) then
(select sum(avgEnergy) from mr_final_results t4 where deviceMAC!='c098e57001A0' and deviceMAC !='c098e5700193' and t2.location=t4.location and t1.category=t4.category)
else 0 end as catSum from
mr_final_categories t1
join
mr_final_locations t2;


# Energy distribution by category for all locations
# This uses mr_cat_breakdown and calculates min, max, mean, q1, and q3 for energy
create view mr_cat_en as
(select t1.category, min(t1.catSum) as minEn,
(select avg(catSum) from mr_cat_breakdown t2 where t1.category=t2.category and t2.catSum<=(select avg(catSum) from mr_cat_breakdown t9 where t9.category=t1.category)) as q1En,
avg(t1.catSum) as meanEn,
(select avg(catSum) from mr_cat_breakdown t3 where t1.category=t3.category and t3.catSum>=(select avg(catSum) from mr_cat_breakdown t10 where t10.category=t1.category)) as q3En,
max(t1.catSum) as maxEn
from mr_cat_breakdown t1
group by t1.category);

# Power distribution by category for all locations
# This uses mr_cat_breakdown and calculates min, max, mean, q1, and q3 for power
alter view mr_cat_pwr as
(select t4.category, min(t4.avgPower) as minPwr,
(select avg(avgPower) from mr_final_results t5 where t4.category=t5.category and t5.avgPower<=(select avg(avgPower) from mr_final_results t7 where t7.category=t4.category)) as q1Pwr,
avg(t4.avgPower) as meanPwr,
(select avg(avgPower) from mr_final_results t6 where t4.category=t6.category and t6.avgPower>=(select avg(avgPower) from mr_final_results t8 where t8.category=t4.category)) as q3Pwr,
max(t4.avgPower) as maxPwr
from mr_final_results t4
where t4.avgPower>0
group by t4.category);

# Total data table for category breakdown
# For each category, min, max, mean, q1, and q3 for both energy and power
create view mr_cat_en_pwr as
select tEn.category, tEn.minEn, tEn.q1En, tEn.meanEn, tEn.q3En, tEn.maxEn, tPwr.minPwr, tPwr.q1Pwr, tPwr.meanPwr, tPwr.q3Pwr, tPwr.maxPwr from
mr_cat_en tEn
join
mr_cat_pwr tPwr
on tEn.category=tPwr.category
order by tEn.meanEn asc;





# This is used for the device ID
create view mr_dat_delta as
select t1.* from dat_delta t1 where
t1.id=(select max(t2.id) from dat_delta t2 where t1.deviceMAC=t2.deviceMAC and t1.dayst=t2.dayst);

create view valid_powerblades_no1 as
select * from valid_powerblades where location!=1;

alter view mr_inf_delta as
select t1.*, t2.deviceName, t2.deviceType from
(mr_dat_delta t1
join valid_powerblades_no1 t2
on t1.deviceMAC=t2.deviceMAC);


create view mr_dat_vector as
select t1.* from dat_vector t1 where
t1.id=(select max(t2.id) from dat_vector t2 where t1.deviceMAC=t2.deviceMAC and t1.dayst=t2.dayst);

alter view mr_dat_vector as
select t1.id, t1.dayst, t1.deviceMAC, t1.avgPwr, t1.varPwr, t1.maxPwr, t1.minPwr, t1.count, t1.duty,
t1.ct5, t1.spk5, t1.ct10, t1.spk10, t1.ct15, t1.spk15, t1.ct25, t1.spk25, t1.ct50, t1.spk50,
t1.ct75, t1.spk75, t1.ct100, t1.spk100, t1.ct150, t1.spk150, t1.ct250, t1.spk250, t1.ct500, t1.spk500,
case when t1.deviceType='Desk lamp' or t1.deviceType='Small lamp/light' or t1.deviceType='Standing lamp'
then 'Lamp' else 
case when t1.deviceType='Router' or t1.deviceType='Modem'
then 'Router/Modem' else
t1.deviceType end end as deviceType
from dat_vector t1 where
t1.id=(select max(t2.id) from dat_vector t2 where t1.deviceMAC=t2.deviceMAC and t1.dayst=t2.dayst);



# Occupancy
create view mr_dat_occ_blink as
select t1.* from dat_occ_blink t1 where
t1.id=(select max(t2.id) from dat_occ_blink t2 where t1.deviceMAC=t2.deviceMAC and t1.tsMin=t2.tsMin);

create view mr_dat_occ_pb as
select t1.* from dat_occ_pb t1 where
t1.id=(select max(t2.id) from dat_occ_pb t2 where t1.deviceMAC=t2.deviceMAC and t1.tsMin=t2.tsMin);



