
select * from inf_pb_lookup where location=0 order by id desc limit 10;
select * from inf_gw_lookup where location=0 order by id desc limit 10;
select * from inf_light_lookup order by id desc limit 10;

explain SELECT t1.* FROM dat_powerblade t1 WHERE 
t1.id=(SELECT MAX(t2.id) FROM dat_powerblade t2 WHERE t1.deviceMAC=t2.deviceMAC);# and t2.timestamp<'2017-03-08 17:00:00');

select * from dat_powerblade where id in (select max(id) from dat_powerblade group by deviceMAC) limit 1;

select * from (select deviceMAC, max(id) as id from dat_powerblade WHERE timestamp>'2017-03-06 17:00:00' AND timestamp<'2017-03-07 20:00:00' group by deviceMAC) t1 join
dat_powerblade t2 on t1.id=t2.id;


select ROUND(UNIX_TIMESTAMP(timestamp)/(5*60)) AS timekey, min(timestamp) as timest, deviceMAC, avg(power) as power from dat_powerblade
where timestamp>date_sub(utc_timestamp(), interval 1 day)
group by timekey, deviceMAC;

explain select UNIX_TIMESTAMP(timestamp) div (5*60) AS timekey, min(timestamp) as timest, deviceMAC, avg(power) as power from dat_powerblade
where timestamp>date_sub(utc_timestamp(), interval 1 day)
group by timekey, deviceMAC;

select date(timestamp) as dayst, deviceMAC, max(energy) as energy from dat_powerblade force index (devEnergy)
where timestamp>date_sub(utc_timestamp(), interval 10 day)
and devicemac in ('c098e570005d', 'c098e570017c')
group by deviceMAC, dayst;


select deviceMAC, avg(dayEnergy) as avgEnergy, var_pop(dayEnergy) as varEnergy from day_energy
group by deviceMAC order by avgEnergy;

select t1.deviceMAC, t1.deviceName, t1.location, t1.permanent, t2.avgPower
from (select * from most_recent_powerblades where location=3) t1
left join avgPower_pb t2
on t1.deviceMAC=t2.deviceMAC
order by t2.avgPower;

describe dat_ligeiro;

select count(*) from dat_ligeiro where timestamp>date_sub(utc_timestamp(), interval 1 day);
select * from dat_ligeiro where deviceMAC!='c098e5d0000a' order by count desc;
select * from inf_light_lookup;
describe avgPower_pb;

select * from most_recent_lights where deviceMAC='c098e5300011';

select * from day_energy union;

select deviceMAC, dayst, sum(onoff) as dayEnergy from
(select ROUND(UNIX_TIMESTAMP(timestamp)/(5*60)) as timekey, deviceMAC, date(timestamp) as dayst,
case when (1+max(count)-min(count)) >= 1 then (select power*5/60 from most_recent_lights t2 where t1.deviceMAC=t2.deviceMAC) else 0 end as 'onoff' 
from dat_ligeiro t1
group by deviceMAC, timekey) t3
group by deviceMAC, dayst;

create view day_energy_blees as
select deviceMAC, dayst, sum(onoff) as dayEnergy from
(select round(unix_timestamp(timestamp)/(5*60)) as timekey, deviceMAC, date(timestamp) as dayst,
case when lux>(select avgLux from avg_lux t2 where t1.deviceMAC=t2.deviceMAC) then
(select power*5/60 from most_recent_lights t3 where t1.deviceMAC=t3.deviceMAC) else 0 end as 'onoff'
from dat_blees t1 force index (devLux)
where timestamp>date_sub(utc_timestamp(), interval 10 day)
group by deviceMAC, timekey) t4
group by deviceMAC, dayst;

create view energy_blees as 
select round(unix_timestamp(timestamp)/(5*60)) as timekey, deviceMAC, date(timestamp) as dayst,
case when lux>(select avgLux from avg_lux t2 where t1.deviceMAC=t2.deviceMAC) then
(select power*5/60 from most_recent_lights t3 where t1.deviceMAC=t3.deviceMAC) else 0 end as 'onoff'
from dat_blees t1 force index (devLux)
where timestamp>date_sub(utc_timestamp(), interval 10 day)
group by deviceMAC, timekey;

create view day_energy_blees as
select dayst, deviceMAC, sum(onoff) as dayEnergy from 
energy_blees group by deviceMAC, dayst;

select * from day_energy_blees;

select * from dat_blees where deviceMAC='c098e5300034' order by id desc;

select deviceMAC, avg(lux) from dat_blees force index (devLux) group by deviceMAC;

select * from most_recent_lights where location=5;

select * from most_recent_powerblades where deviceMAC>='c098e57001a0' and deviceMAC<='c098e57001ab';
select * from most_recent_powerblades where deviceMAC>'c098e570024b' and deviceMAC<'c098e570026e';

select * from active_powerblades where location=0 order by deviceMAC;

select * from dat_powerblade where deviceMAC='c098e570017B' and power>200 order by id desc limit 10;
select * from inf_gw_status order by id desc;

select * from pb_calib order by id asc;

show processlist;




select date(timestamp) as dayst, deviceMAC, (max(energy) - min(energy)) as dayEnergy 
from dat_powerblade force index (devEnergy) 
where timestamp>='2017-3-19  00:00:00' and timestamp<='2017-3-24  23:59:59' 
and deviceMAC in ("c098e570017b") 
and energy!=999999.99 
group by deviceMAC, dayst;

select deviceMAC, max(power) as maxPower from dat_powerblade force index (devPower)
where timestamp>='2017-3-19  00:00:00' and timestamp<='2017-3-24  23:59:59' 
and power != 120.13 and deviceMAC in ("c098e570017b") 
group by deviceMAC;

select deviceMAC, avg(power) as avgPower from dat_powerblade t1 force index(devPower) 
where timestamp>='2017-3-19  00:00:00' and timestamp<='2017-3-24  23:59:59' 
and power>(select 0.1*maxPower from maxPower_pb t2 where t1.deviceMAC=t2.deviceMAC) 
and deviceMAC in ("c098e570017b") group by deviceMAC;

select t1.deviceMAC, t1.deviceName, t2.avgEnergy, t2.stdEnergy, t3.avgPower 
from most_recent_devices t1 
join (select deviceMAC, avg(dayEnergy) as avgEnergy, stddev(dayEnergy) as stdEnergy from day_energy group by deviceMAC) t2 
on t1.deviceMAC=t2.deviceMAC 
join avg_power t3 
on t1.deviceMAC=t3.deviceMAC 
order by t2.avgEnergy;


select * from day_energy;

select * from dat_powerblade where deviceMAC='c098e57001bb' order by id desc limit 1000000;
select * from dat_powerblade where flags>66 limit 10;


alter view day_energy_pb as
select date(timestamp) as dayst, deviceMAC, (max(energy) - min(energy)) as dayEnergy from dat_powerblade force index (devEnergy) 
where timestamp>='2017-03-20 00:00:00' and timestamp<='2017-03-22 23:59:59' 
and deviceMAC in ("c098e570015e","c098e57001b1")
and energy!=999999.99 
group by deviceMAC, dayst;

explain select deviceMAC, avg(power) as maxPower from dat_powerblade# force index (devDevPower) 
where timestamp>='2017-3-20  00:00:00' and timestamp<='2017-03-22 23:59:59'
and power != 120.13 
and deviceMAC in ("c098e570021a") 
group by deviceMAC;

select t1.deviceMAC, t2.deviceName, t1.maxPower from 
(select deviceMAC, max(power) as maxPower from dat_powerblade force index (devTimePower) 
where timestamp>='2017-3-25  00:00:00' and timestamp<='2017-3-27  23:59:59' 
and power != 120.13 
and deviceMAC in ("c098e570015e","c098e57001b1","c098e570019f","c098e57001c4","c098e57001f5","c098e570015e","c098e57001b6","c098e57001c3","c098e5700197","c098e57001b9","c098e57001c0","c098e57001c9","c098e57001be","c098e5700286","c098e570027d","c098e57001b0","c098e570027f","c098e5700284","c098e57001b2","c098e5700190","c098e570019d","c098e570005d","c098e57001bb","c098e57001c2","c098e57001f4","c098e57001b8","c098e57001c1","c098e5700198","c098e57001bd","c098e57001c7","c098e57001f6","c098e57001b3","c098e570027e","c098e5700285","c098e57001af","c098e570027b","c098e5700280","c098e570019b","c098e57001ba","c098e57001c5","c098e57001ed","c098e57001b7","c098e57001c8","c098e57001ee","c098e57001bc","c098e57001c6","c098e57001f3","c098e57001bf","c098e5700283","c098e5700281","c098e57001b4","c098e5700282","c098e570027c") 
group by deviceMAC) t1
join most_recent_powerblades t2
on t1.deviceMAC=t2.deviceMAC;



select * from dat_blink where gatewayMAC='c098e5c00034' and deviceMAC not in ('c098e59000d3', 'c098e59000dd', 'c098e59000d8', 'c098e59000d4') order by id desc;

select * from mr_final_results;
select * from mr_final_gnd;
select location from mr_final_results group by location;
 where deviceType='Fridge';
select location concat_ws(' ', category, deviceType) as catName, sum(avgEnergy), avg(avgPower) as ;

show processlist;


