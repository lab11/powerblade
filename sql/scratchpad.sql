
select * from inf_pb_lookup;

select * from dat_powerblade where deviceMAC='c098e570019E';

select * from inf_pb_lookup where location=0 order by id desc limit 10;
select * from inf_gw_lookup where location=0 order by id desc limit 10;
select * from inf_light_lookup order by id desc limit 10;


explain SELECT t1.* FROM dat_powerblade t1 WHERE 
t1.id=(SELECT MAX(t2.id) FROM dat_powerblade t2 WHERE t1.deviceMAC=t2.deviceMAC);# and t2.timestamp<'2017-03-08 17:00:00');


select * from dat_powerblade where id in (select max(id) from dat_powerblade group by deviceMAC) limit 1;

select * from (select deviceMAC, max(id) as id from dat_powerblade WHERE timestamp>'2017-03-06 17:00:00' AND timestamp<'2017-03-07 20:00:00' group by deviceMAC) t1 join
dat_powerblade t2 on t1.id=t2.id;


describe dat_powerblade;

explain select deviceMAC, max(id) from dat_powerblade WHERE timestamp>subdate(curdate(),1) AND timestamp<curdate() group by deviceMAC;

select deviceMAC, max(id) from dat_powerblade WHERE timestamp>date('2017-03-06') AND timestamp<date('2017-03-07') group by deviceMAC;

select date_sub('2017-03-06 17:00:00', interval 1 hour);

describe dat_powerblade;

explain SELECT * FROM dat_powerblade
WHERE timestamp>subdate(curdate(),1) AND timestamp<curdate();

create view startEnergy as 
select t2.deviceMAC, t2.energy from 
(select deviceMAC, max(id) as id from dat_powerblade 
where timestamp>date_sub('2017-03-08 10:00:00', interval 1 hour) 
AND timestamp<'2017-03-08 10:00:00'  group by deviceMAC) t1 
join dat_powerblade t2 on t1.id=t2.id;

select * from dat_powerblade where deviceMAC='c098e570018c' and timestamp<'2017-03-10 22:00:00' order by id desc limit 10000;

select t2.deviceMAC, t2.energy from
(select deviceMAC, max(id) as id 
from dat_powerblade where timestamp>date_sub('2017-03-10 22:00:00', interval 1 hour) AND timestamp<'2017-03-10 22:00:00'
group by deviceMAC) t1
join dat_powerblade t2 on t1.id=t2.id;

select t2.deviceMAC, t2.energy from 
(select deviceMAC, max(id) as id 
from dat_powerblade where timestamp>date_sub('2017-03-10 22:00:00', interval 1 hour) AND timestamp<'2017-03-10 22:00:00'  
group by deviceMAC) t1 
join dat_powerblade t2 on t1.id=t2.id;

select *,DATE_FORMAT(timestamp, '%Y%m%d') from dat_powerblade limit 1;

describe select deviceMAC, max(energy), min(energy) from dat_powerblade group by deviceMAC;

describe dat_powerblade;

select curtime();

drop view yest_data_light;

select ROUND(UNIX_TIMESTAMP(timestamp)/(5*60)) AS timekey, min(timestamp) as timest, deviceMAC, avg(power) as power from dat_powerblade
where timestamp>date_sub(utc_timestamp(), interval 1 day)
group by timekey, deviceMAC;

explain select UNIX_TIMESTAMP(timestamp) div (5*60) AS timekey, min(timestamp) as timest, deviceMAC, avg(power) as power from dat_powerblade
where timestamp>date_sub(utc_timestamp(), interval 1 day)
group by timekey, deviceMAC;

explain select * from dat_powerblade
where timestamp>date_sub(utc_timestamp(), interval 1 day);

select date(timestamp) as dayst, deviceMAC, max(energy) as energy from dat_powerblade force index (devEnergy)
where timestamp>date_sub(utc_timestamp(), interval 10 day)
and devicemac in ('c098e570005d', 'c098e570017c')
group by deviceMAC, dayst;

select deviceMAC, min(energy) from temp_powerblade group by deviceMAC;

select date(timestamp) as dayst, deviceMAC, min(energy) as energy from temp_powerblade
group by deviceMAC, dayst;

select UNIX_TIMESTAMP(timestamp) div (5*60) AS timekey, deviceMAC, avg(power) as power from temp_powerblade
group by timekey, deviceMAC;

select max(id) from dat_powerblade where energy<0;
select * from dat_powerblade where id=268069075;
select * from dat_powerblade where deviceMAC='c098e570005c' order by id asc;

create table temp_powerblade like dat_powerblade;
insert into temp_powerblade (select * from dat_powerblade order by id asc limit 1000000);

alter table temp_powerblade add index devPower (deviceMAC, power, timestamp);
alter table temp_powerblade add index devEnergy (deviceMAC, energy, timestamp);
alter table temp_powerblade drop index devEnergy;
describe temp_powerblade;

select * from dat_powerblade
where timestamp>date_sub(utc_timestamp(), interval 1 day);

select * from dat_powerblade where deviceMAC='c098e570016a' and timestamp>date_sub(utc_timestamp(), interval 1 hour);

select deviceMAC, seq, power, energy, pf, timestamp from dat_powerblade
where timestamp>date_sub(utc_timestamp(), interval 1 day)
group by deviceMAC, seq;

select power from dat_powerblade group by power;
describe dat_powerblade;

CREATE TABLE temp1 (
  id int not null auto_increment primary key,
  i int(11) NOT NULL,
  j int(11) NOT NULL,
  val char(10) NOT NULL,
  KEY i (i),
  KEY j (j)
);
describe temp1;

CREATE TABLE temp2 (
  id int not null auto_increment primary key,
  i int(11) NOT NULL,
  j int(11) NOT NULL,
  val char(10) NOT NULL,
  KEY ij (i,j)
);
describe temp2;

explain select i, avg(j) from temp1
group by i;

select * from dat_powerblade where devicemac='c098e57000ce' and power>5 order by timestamp desc;

alter view day_energy as
select date(timestamp) as dayst, deviceMAc, (max(energy) - min(energy)) as dayEnergy from dat_powerblade force index(devEnergy)
where timestamp>='2017-03-01 00:00:00' and timestamp<='2017-03-03 23:59:59'
and deviceMAC in ("c098e570006b","c098e5700115","c098e57000c0","c098e57000bf","c098e57000cd","c098e57000cf","c098e57000d5","c098e57000d1","c098e57000ce","c098e57000d9","c098e57000e1","c098e57000d6","c098e57000f6","c098e57000f9","c098e57000ed","c098e57000f3","c098e57000ea","c098e57000ee","c098e5700100","c098e57000e3","c098e57000d8","c098e57000f4","c098e57000fb","c098e57000eb","c098e57000ec","c098e57000e8","c098e57000e9")
group by deviceMAC, dayst;

select deviceMAC, avg(dayEnergy) as avgEnergy, var_pop(dayEnergy) as varEnergy from day_energy
group by deviceMAC order by avgEnergy;

alter view avgPower_pb as
select deviceMAC, avg(power) as avgPower from dat_powerblade t1 force index(devPower)
where timestamp>='2017-03-01 00:00:00' and timestamp<='2017-03-10 23:59:59'
and deviceMAC in ("c098e570006b","c098e5700115","c098e57000c0","c098e57000bf","c098e57000cd","c098e57000cf","c098e57000d5","c098e57000d1","c098e57000ce","c098e57000d9","c098e57000e1","c098e57000d6","c098e57000f6","c098e57000f9","c098e57000ed","c098e57000f3","c098e57000ea","c098e57000ee","c098e5700100","c098e57000e3","c098e57000d8","c098e57000f4","c098e57000fb","c098e57000eb","c098e57000ec","c098e57000e8","c098e57000e9")
and power>(select 0.1*maxPower from maxPower_pb t2 where t1.deviceMAC=t2.deviceMAC)
group by deviceMAC
order by avgPower;

select t1.deviceMAC, t2.deviceName, t1.avgPower
from avgPower_pb t1
join most_recent_powerblades t2
on t1.deviceMAC=t2.deviceMAC
order by t1.avgPower;


select * from dat_powerblade where deviceMAC='c098e57000fb' order by id desc;

create view maxPower_pb as
select deviceMAC, max(power) as maxPower from dat_powerblade force index (devPower)
where timestamp>date_sub(utc_timestamp(), interval 10 day) and power != 120.13
group by deviceMAC;

select t1.deviceMAC, t2.deviceName, t1.maxPower from 
(select deviceMAC, max(power) as maxPower from dat_powerblade force index (devPower)
where timestamp>date_sub(utc_timestamp(), interval 10 day) and power != 120.13
group by deviceMAC) t1
join most_recent_powerblades t2 on t1.deviceMAC=t2.deviceMAC
order by t1.maxPower;

select * from inf_pb_lookup where deviceMAC='c098e570019c' or deviceMAC='c098e5700200';

select * from dat_powerblade where deviceMAC='c098e57000f6' order by id desc;



