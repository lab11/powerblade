# This script is used to query information about the statistics of the deployment


# Statistics specific to PowerBlade
# Grouped by location, the start, end, duration, and number of PowerBlades 
alter view inf_dep_pb as
select location, min(startTime) as startTime, least(utc_timestamp(), max(endTime)) as endTime, 
1+datediff(least('2017-04-11 11:00:00', max(endTime)), min(startTime)) as duration,
count(*) as pb_count 
from valid_powerblades 
where location!=10
group by location;


# Statistics specific to gateways
# Grouped by location, start, end, duration, and number of gateways
alter view inf_dep_gw as
select location, min(startTime) as startTime, least(utc_timestamp(), max(endTime)) as endTime,
1+datediff(least('2017-04-11 11:00:00', max(endTime)), min(startTime)) as duration,
count(*) as gw_count
from most_recent_gateways
where location!=10
group by location;


# Statistics specific to BLEES and Ligeiro
# Grouped by location, the number of deployed sensors
alter view inf_dep_blees as 
select location, count(*) as bl_count
from valid_lights
where location!=10
and deviceType='BLEES'
group by location;

# Grouped by location, the number of deployed sensors
alter view inf_dep_lig as 
select location, count(*) as li_count
from valid_lights
where location!=10
and deviceType='Ligeiro'
group by location;


# Statistics specific to Blink
create view inf_dep_bnk as 
select location, count(*) as bnk_count
from valid_blinks
where location!=10
group by location;


# Statistics for ground truth
# Grouped by location, the number of ground truth days
alter view inf_gnd_truth_lookup as
select location,count(*) as gndTruth from most_recent_gnd_truth group by location;


# Total deployment statistics
alter view inf_dep_stats as
select t1.location, t3.gndTruth, 
greatest(t1.startTime, t2.startTime) as startTime, least(t1.endTime, t2.endTime) as endTime, least(t1.duration, t2.duration) as duration, 
t1.pb_count, t2.gw_count, t4.bl_count, t5.li_count, t6.bnk_count from
inf_dep_pb t1
join inf_dep_gw t2 on t1.location=t2.location
left join inf_gnd_truth_lookup t3 on t1.location=t3.location
left join inf_dep_blees t4 on t1.location=t4.location
left join inf_dep_lig t5 on t1.location=t5.location
left join inf_dep_bnk t6 on t1.location=t6.location
order by t1.location;

select * from most_recent_powerblades where location=9;

# View stats for each location
select * from inf_dep_stats order by location asc;
select location from mr_dat_occ group by location;
select location, count(distinct(tsMin)) from mr_dat_occ group by location;
select * from mr_final_gnd_corr order by location asc;

select min(startTime), max(endTime) from inf_dep_stats where location!=1 and location!=2 and location!=3;

# View total numbers across all locations
select count(*) as numDeps, avg(duration) as avgDuration, stddev(duration) as stdDuration, min(duration) as minDuration, max(duration) as maxDuration,
sum(duration) as depDays,
sum(pb_count)+sum(bl_count)+sum(li_count) as devCount, 
sum(pb_count) as sumPb, avg(pb_count) as  avgPb, stddev(pb_count) as stdPb, min(pb_count) as minPb, max(pb_count) as maxPb,
sum(gw_count) as sumGw, avg(gw_count) as avgGw, min(gw_count) as minGw, max(gw_count) as maxGw,
sum(bl_count) as sumBl, avg(bl_count) as avgBl, min(bl_count) as minBl, max(bl_count) as maxBl,
sum(li_count) as sumLi, avg(li_count) as avgLi, min(li_count) as minLi, max(li_count) as maxLi
from inf_dep_stats
where location!=2
and location!=1;

select min(t1.dayst), max(t1.dayst), t2.location from 
(mr_dat_vector t1 
join 
valid_powerblades_no1 t2
on t1.deviceMAC=t2.deviceMAC)
group by t2.location;


select min(t1.dayst), max(t1.dayst), t2.location from 
(mr_dat_occ_vector t1 
join 
valid_powerblades_no1 t2
on t1.deviceMAC=t2.deviceMAC)
group by t2.location;


# Total measured and total ground truth (as daily averages so each location is treated equally)
select avg(totMeas) as meas, avg(fullGnd) as gnd, avg(totMeas)/avg(fullGnd)*100 as pct from mr_final_gnd_corr where location!=1;



# Category query (same as in plot/plot_data.py)
select t1.category, min(t1.catSum) as minCat,
(select avg(catSum) from mr_cat_breakdown t2 where t1.category=t2.category and t2.catSum<avg(t1.catSum)) as q1,
avg(t1.catSum) as meanCat,
(select avg(catSum) from mr_cat_breakdown t3 where t1.category=t3.category and t3.catSum>avg(t1.catSum)) as q3,
max(t1.catSum) as maxCat
from mr_cat_breakdown t1
#where t1.catSum>0
group by t1.category;



# Query total number of recorded packets
select max(t1.id)/1E9 as countPb, max(t2.id)/1E6 as countBl, max(t3.id)/1E6 as countLi
from dat_powerblade t1
join dat_blees t2
join dat_ligeiro t3;



# This is for determining if a PowerBlade has been redeployed
select t1.*, t2.count from
most_recent_powerblades t1 join
(select deviceMAC, count(distinct(deviceName)) as count from most_recent_powerblades group by deviceMAC order by count desc) t2
on t1.deviceMAC=t2.deviceMAC
order by t2.count desc, t1.deviceMAC asc, t1.startTime asc;

