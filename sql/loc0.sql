# Special queries for loc0
# This is in place because we wanted to calculate q1/q3 and doing it with the view approach took too long


# Create a copy of the powerblade data table for loc0
create table loc0_dat_powerblade like dat_powerblade;

insert into loc0_dat_powerblade (gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp)
select gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp 
from dat_powerblade force index (devTimePower)
where timestamp>='2017-03-18 00:00:00' and timestamp<='2017-04-03 23:59:59'
and deviceMAC in (select deviceMAC from valid_powerblades where location=0);

# Stats on loc0 table
select count(*) from loc0_dat_powerblade;


# maxPower view is the same as the maxPower_pb view from plot/plot_data.py
create view loc0_maxPower_pb as
select deviceMAC, max(power) as maxPower from loc0_dat_powerblade force index (devTimePower)
where power != 120.13 group by deviceMAC;


# The abovezero table mimics the aspect of the avgPower_pb query that rejects zero readings
create table loc0_dat_abovezero like dat_powerblade;

insert into loc0_dat_abovezero (gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp)
select t1.gatewayMAC, t1.deviceMAC, t1.seq, t1.voltage, t1.power, t1.energy, t1.pf, t1.flags, t1.timestamp
from loc0_dat_powerblade t1 force index (devDevPower)
where power>(select case when maxPower>10 then 0.1*maxPower else 0.5*maxPower end from loc0_maxPower_pb t2 where t1.deviceMAC=t2.deviceMAC);



# Power calculation

# loc0_avg_power table
# This mimics the avg_power_pb view from plot/plot_data.py but for loc0
# This is replaced by the calculation of loc0_avgPower_pb, below
create table loc0_avg_power 
(id int(11) not null auto_increment, deviceMAC char(12), avgPower decimal(12,6), 
primary key (id), index (deviceMAC), index devPower (deviceMAC, avgPower));

insert into loc0_avg_power (deviceMAC, avgPower)
select deviceMAC, avg(power) from loc0_dat_abovezero force index (devDevPower) 
group by deviceMAC;

# Stats on loc0 avg power table
select count(*) from loc0_avg_power;


# loc0_avgPower_pb replaces loc0_avg_power, above, and includes q1 and q3 for each device
create table loc0_avgPower_pb as
select deviceMAC, min(power) as minPower, avg(power) as avgPower, max(power) as maxPower,
(select avg(power) from loc0_dat_abovezero force index(devDevPower) where deviceMAC=t1.deviceMAC and power<=(select avgPower from loc0_avg_power where deviceMAC=t1.deviceMAC)) as q1Pwr,
(select avg(power) from loc0_dat_abovezero force index(devDevPower) where deviceMAC=t1.deviceMAC and power>=(select avgPower from loc0_avg_power where deviceMAC=t1.deviceMAC)) as q3Pwr
from loc0_dat_abovezero t1 force index(devDevPower)
group by deviceMAC;



# Energy calculation

# day_energy_pb, dev_resets, and dev_actResets all mimic their functionality in plot/plot_data.py
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


# Day energy table for loc 0
create table loc0_day_energy 
(dayst date, deviceMAC char(16), dayEnergy decimal(37,4), 
index (deviceMAC), index devDevEnergy (deviceMAC, dayEnergy, dayst));

# Note that this relies on support from the plot/plot_data.py script to correctly populate blees and ligeiro data
insert into loc0_day_energy (dayst, deviceMAC, dayEnergy)
select * from loc0_day_energy_pb tta where
(select actReset from loc0_dev_actResets ttb where tta.deviceMAC=ttb.deviceMAC and tta.dayst=ttb.dayst)=0
union select * from day_energy_blees
union select * from day_energy_ligeiro;




# Creating full day energy table for loc0 - energy or 0 for all days for all devices
create view loc0_day_energy_days as select dayst from loc0_day_energy group by dayst;
create view loc0_day_energy_devs as select deviceMAC from loc0_day_energy group by deviceMAC;

create view loc0_day_energy_full as
select t1.dayst, t2.deviceMAC, case when t1.dayst in (select dayst from loc0_day_energy t3 where t2.deviceMAC=t3.deviceMAc) then
(select dayEnergy from loc0_day_energy t4 where t2.deviceMAC=t4.deviceMAC and t1.dayst=t4.dayst)
else 0 end as dayEnergy from
loc0_day_energy_days t1
join
loc0_day_energy_devs t2;



# This is actually taken care of, and plotted, with plot/plot_data.py, but included here for reference
select deviceMAC, min(dayEnergy) as minEnergy,
(select avg(dayEnergy) from loc0_day_energy_full where deviceMAC=tday.deviceMAC and dayEnergy<=(select avg(dayEnergy) from loc0_day_energy_full where deviceMAC=tday.deviceMAC)) as q1DayEn,
avg(dayEnergy) as avgEnergy,
(select avg(dayEnergy) from loc0_day_energy_full where deviceMAC=tday.deviceMAC and dayEnergy>=(select avg(dayEnergy) from loc0_day_energy_full where deviceMAC=tday.deviceMAC)) as q3DayEn,
max(dayEnergy) as maxEnergy,
sum(dayEnergy) as totEnergy
from loc0_day_energy_full tday group by deviceMAC;












