# Deployment stats
alter view inf_dep_stats as
select t1.location, case when t3.gndTruth is not null then 1 else 0 end as gndTruth, greatest(t1.startTime, t2.startTime) as startTime, least(t1.endTime, t2.endTime) as endTime, least(t1.duration, t2.duration) as duration, t1.pb_count, t2.gw_count from
inf_dep_pb t1
join inf_dep_gw t2
on t1.location=t2.location
left join inf_gnd_truth_lookup t3
on t1.location=t3.location
order by location;

create view inf_dep_pb as
select location, min(startTime) as startTime, least(utc_date(), max(endTime)) as endTime, 
1+datediff(least(utc_date(), max(endTime)), min(startTime)) as duration,
count(*) as pb_count 
from most_recent_powerblades 
where location!=10
group by location;

select * from inf_dep_pb;

create view inf_dep_gw as
select location, min(startTime) as startTime, least(utc_date(), max(endTime)) as endTime,
1+datediff(least(utc_date(), max(endTime)), min(startTime)) as duration,
count(*) as gw_count
from most_recent_gateways
where location!=10
group by location;

create view inf_gnd_truth_lookup as
select location,1 as gndTruth from dat_gnd_truth group by location;

select * from inf_dep_stats;

select count(*) as numDeps, avg(duration) as avgDuration, stddev(duration) as stdDuration, min(duration) as minDuration, max(duration) as maxDuration, 
sum(pb_count) as sumPb, avg(pb_count) as  avgPb, stddev(pb_count) as stdPb, min(pb_count) as minPb, max(pb_count) as maxPb,
sum(gw_count) as sumGw, avg(gw_count) as avgGw, min(gw_count) as minGw, max(gw_count) as maxGw 
from inf_dep_stats;
where duration > 7 and duration < 168;

select * from most_recent_powerblades where location=3;

select * from inf_pb_lookup where deviceMAC='c098e57000cd';
select * from most_recent_powerblades where deviceMAC='c098e57000cd';
select * from active_powerblades;# where deviceMAC='c098e57000cd';

select gatewayMAC, count(distinct(location)) from inf_gw_lookup group by gatewayMAC;
select * from inf_gw_lookup where gatewayMAC='c098e5c00026';
select * from most_recent_gateways order by location;
select * from active_gateways order by location;


# This is for determining if a PowerBlade has been redeployed (IMPORTANT!)
select t1.*, t2.count from
most_recent_powerblades t1 join
(select deviceMAC, count(distinct(deviceName)) as count from most_recent_powerblades group by deviceMAC order by count desc) t2
on t1.deviceMAC=t2.deviceMAC
order by t2.count desc, t1.deviceMAC asc, t1.startTime asc;

select timestamp, deviceMAC, max(power) as maxPower from dat_powerblade force index (devPower)
where timestamp>='2017-3-27  00:00:00'# and timestamp<='2017-3-27  23:59:59' 
and power != 120.13 
and deviceMAC in ("c098e57000f6","c098e57000d9","c098e57000e8","c098e57000d5","c098e57000fb","c098e57000bf","c098e57000e3","c098e570006b","c098e57000ea","c098e57000f9","c098e57000e1","c098e57000e9","c098e57000d1","c098e57000eb","c098e57000cd","c098e57000d8","c098e5700115","c098e57000ee","c098e57000ed","c098e57000d6","c098e57000ce","c098e57000ec","c098e57000cf","c098e57000f4","c098e57000c0","c098e5700100","c098e57000f3") 
group by timestamp, deviceMAC;

select deviceMAC, timestamp, min(power) from dat_powerblade force index (devPower) group by timestamp, deviceMAC;

select * from dat_powerblade where timestamp<'2017-01-13' order by timestamp desc limit 1;

describe inf_pb_lookup;


select * from dat_powerblade where deviceMAC='c098e5700139' order by id asc limit 100;
select * from dat_powerblade where gatewayMAC in ('c098e5c00029', 'c098e5c00029') and deviceMAC='c098e570005b' order by id desc;



'alter view maxPower_pb as ' \
		'select deviceMAC, max(power) as maxPower from dat_powerblade force index (devPower) ' \
		'where timestamp>=\'' + config['startDay'] + ' 00:00:00\' and timestamp<=\'' + config['endDay'] + ' 23:59:59\' ' \
		'and power != 120.13 ' \
		'and deviceMAC in ' + dev_powerblade + ' group by deviceMAC;'
        
select deviceMAC, max(power) as maxPower from dat_powerblade force index (devPower)
where timestamp>(select startTime from ;

select deviceMAC, count(*) as count from most_recent_powerblades group by deviceMAC order by count desc;

select * from most_recent_powerblades where deviceMAC='c098e57000f3';


select * from dat_powerblade force index (devEnergy)
where timestamp<'2017-03-26 23:59:59'
and deviceMAC='c098e57000f3';


