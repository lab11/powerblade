# This selects data starting in the beginning of march from several categories
# This isnt really used anymore

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



# Create full vector - this is replicated in calc_vectors
# This isnt really used anymore since the script
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



# Various queries against mr_inf_delta
select * from valid_powerblades where deviceMAC='c098e57001a0';
select deviceType, count(*) as count from mr_inf_delta group by deviceType order by count desc;
select * from mr_inf_delta where deviceType='Laptop computer';
select * from mr_inf_delta where deviceType='Fridge';
select * from mr_inf_delta where deviceType='Fan';
select * from mr_inf_delta where deviceType='Standing lamp';
select * from mr_inf_delta where deviceType='Modem';
select * from mr_inf_delta where deviceType='Phone charger';
select * from mr_inf_delta where deviceType='Television';


# These set up the categories for the device identification
# Also the smaller category list

alter view id_categories as
select deviceType from valid_powerblades
where deviceType in 
('Television', 'Fridge', 'Microwave', 'Laptop computer', 'Phone charger', 
'Blowdryer', 'Coffee maker', 'Fan', 'Cable Box', 'Curling iron', 
'Computer Monitor', 'Toaster', 'Modem', 'Router', 'Blender')
or category='Lighting'
group by deviceType;

alter view id_fewcats as
select deviceType from valid_powerblades
where deviceType in
('Television', 'Fridge', 'Microwave', 'Laptop computer', 
'Cable Box', 'Phone charger', 'Toaster', 'Coffee maker')
or category='Lighting';



# The following queries are used to observe the data for identification

select * from mr_dat_vector where deviceMAC='c098e5700220';
select * from valid_powerblades where deviceMAC='c098e570026a';

select deviceMAC, deviceType, avg(avgPwr) as avgAvgPwr, avg(varPwr) as avgVarPwr, min(maxPwr) as minMaxPwr, avg(maxPwr) as avgMaxPwr, max(maxPwr) as maxMaxPwr
from mr_dat_vector
where duty!=0
and (deviceType = 'Blender')
group by deviceMAC;

select deviceType, avg(avgPwr) as avgAvgPwr, avg(varPwr) as avgVarPwr, min(maxPwr) as minMaxPwr, avg(maxPwr) as avgMaxPwr, max(maxPwr) as maxMaxPwr
from mr_dat_vector
where duty!=0
group by deviceType
order by avgMaxPwr asc;







# The following views and queries work with mr_dat_vector, the output of calc_vectors

# Devices for the test set (the second most quantity of each category)
create view vector_test as 
select deviceMAC from valid_powerblades
where deviceMAC in ('c098e570005d', 'c098e5700211', 
'c098e5700183', 'c098e570016a', 'c098e570026e', 'c098e57000eb', 
'c098e5700164', 'c098e57001b2', 'c098e57001b4', 'c098e570016e', 
'c098e5700282', 'c098e57001ad', 'c098e5700195', 'c098e5700262', 
'c098e57000ed', 'c098e570023a', 'c098e5700285', 'c098e5700170')
group by deviceMAC;

# Devices for the reject set (errors, bad calibration, etc)
create view vector_reject as
select deviceMAC from valid_powerblades
where deviceMAC in ('c098e57001b5', 'c098e57001c5', 
'c098e57001c8', 'c098e5700163', 'c098e5700233', 'c098e57001ed', 
'c098e570026a', 'c098e57001a0', 'c098e570027d', 'c098e5700238')
group by deviceMAC;


# WKB All - Full Set
select * from mr_dat_vector
where duty!=0
and deviceMAC not in (select * from vector_reject);

# WKB Train - Full Set
select * from mr_dat_vector
where duty!=0
and deviceMAC not in (select * from vector_test)
and deviceMAC not in (select * from vector_reject);

# WKB Test - Full Set
select * from mr_dat_vector
where duty!=0
and deviceMAC in (select * from vector_test);

# WKB Train - Smaller Set
select * from mr_dat_vector
where duty!=0
and deviceMAC not in (select * from vector_test)
and deviceMAC not in (select * from vector_reject)
and deviceType in (select * from id_fewcats);

# WKB Test - Smaller Set
select * from mr_dat_vector
where duty!=0
and deviceMAC in (select * from vector_test)
and deviceType in (select * from id_fewcats);


