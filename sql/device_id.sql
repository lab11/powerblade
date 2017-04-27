# This selects data starting in the beginning of march from several categories

# Select data from televisions (12 devices, 32M rows)
select gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp 
from dat_powerblade 
where deviceMAC in (select deviceMAC from valid_powerblades where deviceType='Television' and location!=1) 
and timestamp>'2017-03-01 00:00:00' limit 1
into outfile '/Users/sdebruin/Downloads/PB_Output.csv'
FIELDS TERMINATED BY ',' 
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n';

# Select data from fridges (9 devices 21M rows)
select count(*) from dat_powerblade 
where deviceMAC in (select deviceMAC from valid_powerblades where deviceType='Fridge')
and timestamp>'2017-03-01 00:00:00';

# Select data from microwaves (10 devices)
select deviceMAC from valid_powerblades where deviceType='Microwave';

# Select data from laptops (15 devices)
select deviceMAC from valid_powerblades where deviceType='Laptop computer';

# Select data from lighting (48 devices)
select deviceMAC from valid_powerblades where category='Lighting';

select * from valid_powerblades where deviceType='Television';

select * from dat_powerblade where gatewayMAC='c098e5c00031' order by id desc limit 10;

select * from valid_powerblades where deviceMAC='c098e57000e6';

show processlist;

select category, deviceType, count(*) as count from valid_powerblades group by deviceType order by count desc;


# Creating the vector for device identification - right now every day
select ROUND(unix_timestamp(timestamp)/(24*60*60)) as timekey, max(timestamp), 
deviceMAC, 
avg(power), var_pop(power), max(power), min(power),
# duty cycle
(select count(*) from dat_powerblade t2 where t1.deviceMAC=t2.deviceMAC and timestamp>'2017-03-01 00:00:00' and power>5) as onCount, count(*) as totCount
# waveform
from dat_powerblade t1
where deviceMAC='c098e570005d'
and timestamp>'2017-03-01 00:00:00'
group by deviceMAC, timekey;


select deviceMAC, seq, power from dat_powerblade 
where deviceMAC='c098e570005d'
and timestamp>'2017-03-01 00:00:00'
order by timestamp asc;

select * from dat_powerblade force index (devTimePower)
where timestamp>'2017-04-10 00:00:00'# and id not in (select id from dat_delta group by id)
order by deviceMAC, timestamp;

select * from dat_powerblade force index (devTimeSeq)
#where timestamp>'2017-03-01 00:00:00' and timestamp<'2017-03-01 01:00:00'
#where id not in (select id from dat_delta group by id)
where deviceMAC='c098e570005d' and date(timestamp)='2017-03-20'
order by deviceMAC, timestamp, seq;

drop table temp_powerblade;
create table temp_powerblade like dat_powerblade;
alter table temp_powerblade add index timeDevSeq (timestamp, deviceMAC, seq);
insert into temp_powerblade select * from dat_powerblade where timestamp>'2017-03-15 00:00:00' limit 1000000;

alter view id_categories as
select deviceType from valid_powerblades
where deviceType in 
('Television', 'Fridge', 'Microwave', 'Laptop computer', 'Phone charger', 
'Blowdryer', 'Coffee maker', 'Fan', 'Cable Box', 'Curling iron', 
'Computer Monitor', 'Toaster', 'Modem', 'Router', 'Blender')
or category='Lighting'
group by deviceType;

create view id_fewcats as
select deviceType from valid_powerblades
where deviceType in
('Television', 'Fridge', 'Microwave', 'Laptop computer', 
'Cable Box', 'Phone charger', 'Toaster', 'Coffee maker')
or category='Lighting';

select * from id_categories order by deviceType asc;

select * from mr_dat_delta;

select t1.dayst, t1.deviceMAC,
coalesce(t2.avgPwr, 0) as avgPwr, coalesce(t2.varPwr, 0) as varPwr, coalesce(t2.maxPwr, 0) as maxPwr, coalesce(t2.minPwr, 0) as minPwr,
t1.count as count,
coalesce(t2.count, 0)/t1.count as dutyCycle,
coalesce(t4.ct5, 0) as ct5, coalesce(t4.spk5, 0) as spk5, coalesce(t4.ct10, 0) as ct10, coalesce(t4.spk10, 0) as spk10, 
coalesce(t4.ct15, 0) as ct15, coalesce(t4.spk15, 0) as spk15, coalesce(t4.ct25, 0) as ct25, coalesce(t4.spk25, 0) as spk25, 
coalesce(t4.ct50, 0) as ct50, coalesce(t4.spk50, 0) as spk50, coalesce(t4.ct75, 0) as ct75, coalesce(t4.spk75, 0) as spk75, 
coalesce(t4.ct100, 0) as ct100, coalesce(t4.spk100, 0) as spk100, coalesce(t4.ct150, 0) as ct150, coalesce(t4.spk150, 0) as spk150, 
coalesce(t4.ct250, 0) as ct250, coalesce(t4.spk250, 0) as spk250, coalesce(t4.ct500, 0) as ct500, coalesce(t4.spk500, 0) as spk500,
t3.deviceType
from
(select ROUND(unix_timestamp(timestamp)/(24*60*60)) as timekey, date(timestamp) as dayst, 
deviceMAC, 
max(power) as maxPwr,
count(*) as count
from dat_powerblade 
where deviceMAC in (select deviceMAC from valid_powerblades 
	where deviceType in ('Blender')#(select * from id_categories)
	and location!=1)
and timestamp>'2017-03-01 00:00:00'
group by deviceMAC, timekey) t1
left join 
(select ROUND(unix_timestamp(timestamp)/(24*60*60)) as timekey, date(timestamp) as dayst, 
deviceMAC, 
avg(power) as avgPwr, var_pop(power) as varPwr, max(power) as maxPwr, min(power) as minPwr,
count(*) as count
from dat_powerblade 
where deviceMAC in (select deviceMAC from valid_powerblades 
	where deviceType in ('Blender')# (select * from id_categories) 
    and location!=1)
and power>17 
and timestamp>'2017-03-01 00:00:00'
group by deviceMAC, timekey) t2
on t1.timekey=t2.timekey and t1.deviceMAC=t2.deviceMAC
left join 
(select * from valid_powerblades where location!=1) t3
on t1.deviceMAC=t3.deviceMAC
left join
mr_dat_delta t4
on t1.deviceMAC=t4.deviceMAC and t1.dayst=t4.dayst;
where t1.count>100;


select ROUND(unix_timestamp(timestamp)/(24*60*60)) as timekey, max(timestamp) as maxTime, 
deviceMAC, 
count(distinct seq) as count
from dat_powerblade force index (devTimeSeq) where deviceMAC='c098e570005d' and timestamp>'2017-03-01 00:00:00' 
group by deviceMAC, timekey;

explain select ROUND(unix_timestamp(timestamp)/(24*60*60)) as timekey, max(timestamp) as maxTime, 
deviceMAC, 
avg(power) as avgPwr, var_pop(power) as varPwr, max(power) as maxPwr, min(power) as minPwr,
count(*) as count
from dat_powerblade where deviceMAC='c098e570005d'and power>17 and timestamp>'2017-03-01 00:00:00'
group by deviceMAC, timekey;



#
select * from valid_powerblades where deviceMAC='c098e57001a0';
select deviceType, count(*) as count from mr_inf_delta group by deviceType order by count desc;
select * from mr_inf_delta where deviceType='Laptop computer';
select * from mr_inf_delta where deviceType='Fridge';
select * from mr_inf_delta where deviceType='Fan';
select * from mr_inf_delta where deviceType='Standing lamp';
select * from mr_inf_delta where deviceType='Modem';
select * from mr_inf_delta where deviceType='Phone charger';
select * from mr_inf_delta where deviceType='Television';

select t2.deviceType, avg(ct5), var_pop(ct5), avg(ct10), var_pop(ct10), avg(ct50), var_pop(ct50), avg(ct100), var_pop(ct100) from
(mr_dat_delta t1
join valid_powerblades t2
on t1.deviceMAC=t2.deviceMAC)
group by t2.deviceType;

