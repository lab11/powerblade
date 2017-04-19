
create table loc0_dat_powerblade like dat_powerblade;

describe loc0_dat_powerblade;

select * from valid_powerblades where location=0;

insert into loc0_dat_powerblade (gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp)
select gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp 
from dat_powerblade force index (devTimePower)
where timestamp>='2017-03-18 00:00:00' and timestamp<='2017-04-03 23:59:59'
and deviceMAC in (select deviceMAC from valid_powerblades where location=0);

select deviceMAC from loc0_dat_powerblade group by deviceMAC;

select count(*) from loc0_dat_powerblade;

create table loc0_avg_power (id int(11) not null auto_increment, deviceMAC char(12), avgPower decimal(12,6), primary key (id), index (deviceMAC), index devPower (deviceMAC, avgPower));

insert into loc0_avg_power (deviceMAC, avgPower)
select deviceMAC, avg(power) from loc0_dat_abovezero force index (devDevPower) group by deviceMAC;


select count(*) from loc0_avg_power;

select * from loc0_avg_power;

create table loc0_dat_abovezero like dat_powerblade;

select count(*) from loc0_dat_abovezero;

describe loc0_dat_abovezero;

create view loc0_maxPower_pb as
select deviceMAC, max(power) as maxPower from loc0_dat_powerblade force index (devTimePower)
where power != 120.13 group by deviceMAC;

insert into loc0_dat_abovezero (gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp)
select t1.gatewayMAC, t1.deviceMAC, t1.seq, t1.voltage, t1.power, t1.energy, t1.pf, t1.flags, t1.timestamp
from loc0_dat_powerblade t1 force index (devDevPower)
where power>(select case when maxPower>10 then 0.1*maxPower else 0.5*maxPower end from loc0_maxPower_pb t2 where t1.deviceMAC=t2.deviceMAC);

drop view avgPower_pb;
create table loc0_avgPower_pb as
select deviceMAC, min(power) as minPower, avg(power) as avgPower, max(power) as maxPower,
(select avg(power) from loc0_dat_abovezero force index(devDevPower) where deviceMAC=t1.deviceMAC and power<=(select avgPower from loc0_avg_power where deviceMAC=t1.deviceMAC)) as q1Pwr,
(select avg(power) from loc0_dat_abovezero force index(devDevPower) where deviceMAC=t1.deviceMAC and power>=(select avgPower from loc0_avg_power where deviceMAC=t1.deviceMAC)) as q3Pwr
from loc0_dat_abovezero t1 force index(devDevPower)
group by deviceMAC;



select * from avgPower_pb;



select * from day_energy_pb;
select date(timestamp) as dayst, deviceMAC, (max(energy) - min(energy)) as dayEnergy
from loc0_dat_powerblade force index (devDevEnergy)
where energy!=999999.99 group by deviceMAC, dayst;

select * from dev_resets;
select date(timestamp) as dayst, deviceMAC,
min(energy) as minEnergy,
case when min(energy)<1.75 then 1 else 0 end as devReset, min(timestamp) as minTs
from loc0_dat_powerblade force index(devTimeEnergy)
group by dayst, deviceMAC;

describe day_energy;
select * from day_energy;
drop view day_energy;
create table day_energy (dayst date, deviceMAC char(16), dayEnergy decimal(37,4), index (deviceMAC), index devDevEnergy (deviceMAC, dayEnergy, dayst));
rename table day_energy to loc0_day_energy;

create view loc0_day_energy_pb as
select date(timestamp) as dayst, deviceMAC, (max(energy) - min(energy)) as dayEnergy
from loc0_dat_powerblade force index (devTimeEnergy)
where energy!=999999.99 group by deviceMAC, dayst;

create view loc0_dev_resets as
select date(timestamp) as dayst, deviceMAC,
min(energy) as minEnergy,
case when min(energy)<1.75 then 1 else 0 end as devReset, min(timestamp) as minTs
from loc0_dat_powerblade force index(devTimeEnergy)
group by dayst, deviceMAC;

create view loc0_dev_actResets as
select t1.dayst, t1.deviceMAC, t1.minEnergy, t1.devReset, t1.minTs,
case when t1.devReset=1 and (select min(energy) from dat_powerblade force index(devTimeEnergy) 
where deviceMAC=t1.deviceMAC and timestamp=t1.minTs and energy!=2.24)>1.75 then 1 else 0 end as actReset
from loc0_dev_resets t1;

insert into loc0_day_energy (dayst, deviceMAC, dayEnergy)
select * from loc0_day_energy_pb tta where
(select actReset from loc0_dev_actResets ttb where tta.deviceMAC=ttb.deviceMAC and tta.dayst=ttb.dayst)=0
union select * from day_energy_blees
union select * from day_energy_ligeiro;


(select avg(power) from loc0_dat_abovezero force index(devDevPower) where deviceMAC=t1.deviceMAC and power<=(select avgPower from loc0_avg_power where deviceMAC=t1.deviceMAC)) as q1Pwr,;



select deviceMAC, min(dayEnergy) as minEnergy,
(select avg(dayEnergy) from loc0_day_energy_full where deviceMAC=tday.deviceMAC and dayEnergy<=(select avg(dayEnergy) from loc0_day_energy_full where deviceMAC=tday.deviceMAC)) as q1DayEn,
avg(dayEnergy) as avgEnergy,
(select avg(dayEnergy) from loc0_day_energy_full where deviceMAC=tday.deviceMAC and dayEnergy>=(select avg(dayEnergy) from loc0_day_energy_full where deviceMAC=tday.deviceMAC)) as q3DayEn,
max(dayEnergy) as maxEnergy,
sum(dayEnergy) as totEnergy
from loc0_day_energy_full tday group by deviceMAC;


select * from loc0_day_energy_full where deviceMAC='c098e5300052';


create view loc0_day_energy_days as select dayst from loc0_day_energy group by dayst;
create view loc0_day_energy_devs as select deviceMAC from loc0_day_energy group by deviceMAC;



create view loc0_day_energy_full as
select t1.dayst, t2.deviceMAC, case when t1.dayst in (select dayst from loc0_day_energy t3 where t2.deviceMAC=t3.deviceMAc) then
(select dayEnergy from loc0_day_energy t4 where t2.deviceMAC=t4.deviceMAC and t1.dayst=t4.dayst)
else 0 end as dayEnergy from
loc0_day_energy_days t1
join
loc0_day_energy_devs t2;


