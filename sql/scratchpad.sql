
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

select * from most_recent_powerblades where deviceMAC>='c098e57001a0' and deviceMAC<'c098e57001ab';
select * from most_recent_powerblades where deviceMAC>'c098e570024b' and deviceMAC<'c098e570026e';

select * from most_recent_powerblades where location=5 order by deviceMAC;

select * from dat_powerblade where deviceMAC='c098e570017B' and power>200 order by id desc limit 10;
select * from inf_gw_status order by id desc;

select * from pb_calib order by id asc;

show processlist;

