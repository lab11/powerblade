# Deployment stats
alter view inf_dep_stats as
select t1.location, case when t3.gndTruth is not null then 1 else 0 end as gndTruth, greatest(t1.startTime, t2.startTime) as startTime, least(t1.endTime, t2.endTime) as endTime, least(t1.duration, t2.duration) as duration, t1.pb_count, t2.gw_count from
inf_dep_pb t1
join inf_dep_gw t2
on t1.location=t2.location
left join (select location as gndTruth from dat_gnd_truth group by location) t3
on t1.location=t3.gndTruth
order by location;

create view inf_dep_pb as
select location, min(startTime) as startTime, least(utc_date(), max(endTime)) as endTime, 
1+datediff(least(utc_date(), max(endTime)), min(startTime)) as duration,
count(*) as pb_count 
from most_recent_powerblades 
where location!=10
group by location;

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


describe inf_pb_lookup;


select * from dat_powerblade where deviceMAC='c098e5700139' order by id asc limit 100;
select * from dat_powerblade where gatewayMAC in ('c098e5c00029', 'c098e5c00029') and deviceMAC='c098e570005b' order by id desc;

