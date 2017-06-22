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
select deviceType, count(*) as count from valid_powerblades_no1 group by deviceType order by count desc;
select deviceType, count(*) as count from valid_powerblades_no1 where deviceMAC not in (select * from id_fewcats_mac) group by deviceType order by count desc;
select deviceType from valid_powerblades where deviceType not in (select * from id_categories) group by deviceType;
select count(*) from valid_powerblades_no1 where deviceType in (select * from id_categories);
select count(*) from valid_powerblades_no1;

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
'Cable Box', 'Phone charger', 'Toaster', 'Coffee maker', 'Modem', 'Router', 'Desk lamp', 'Small lamp/light', 'Standing lamp');

select * from valid_powerblades_no1 where deviceType='Other';
select * from valid_powerblades_no1 where deviceMAC='c098e5700235';

select deviceMAC, avg(varPwr), deviceType from mr_dat_occ_vector where deviceType='Lamp'# and varPwr>4
group by deviceMAC order by avg(varPwr) desc;

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
where deviceMAC in ('c098e57001b5', 'c098e57001c5', 'c098e57001b1', 'c098e5700175'
'c098e57001c8', 'c098e5700163', 'c098e5700233', 'c098e57001ed', 'c098e57000ce'
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





# Re-doing the device breakdown based on the classification results
select * from mr_final_results;

create table class_results (deviceMAC char(12), actType varchar(50), classType varchar(50));

load data local infile '/Users/sdebruin/repo/powerblade/sql/devId/csv_ids.dat' into table class_results fields terminated by ',' (deviceMAC, actType, classType);

select * from class_results where actType!=classType;

select * from class_results where deviceMAC not in (select deviceMAC from class_results_category);
delete from class_results;

select * from deviceTypeList;
select * from valid_powerblades_no1 where category='Kitchen';

alter view deviceTypeList as
select deviceType, category from valid_powerblades_no1 where category!='Kitchen' group by deviceType;
select * from deviceTypeList;

alter view class_results_category as
select deviceMAC, actType, classType, category as classCat from
class_results t1 join 
deviceTypeList t2 on t1.classType=t2.deviceType;

select * from class_results_category;

select * from mr_final_results;

create view mr_class_final_results as
select t1.*, t2.classCat from 
mr_final_results t1
left join class_results_category t2 on 
t1.deviceMAC=t2.deviceMAC;

select * from mr_class_final_results;

alter view mr_class_cat_breakdown as
select t2.location, t1.category, case when t1.category in (select category from mr_class_final_results t3 where t2.location=t3.location) then
(select sum(avgEnergy) from mr_class_final_results t4 where deviceMAC!='c098e57001A0' and deviceMAC !='c098e5700193' and t2.location=t4.location and t1.category=t4.classCat)
else 0 end as catSum from
mr_final_categories t1
join
mr_final_locations t2;

select * from mr_class_final_results;

select * from mr_final_results where category='Entertainment' and deviceMAC!='c098e57000E6' and deviceMAC!='c098e570018D';
select location, sum(avgEnergy) from mr_final_results where category='Overhead' group by location;
select * from mr_final_results where category='Screen/Display' group by location;
select * from mr_final_results where category='Lighting';

alter view newClassEnergy as
select ta.deviceMAC, ta.location, ta.category as actCat, ta.avgEnergy as actEnergy, tb.classCat as classCat
from mr_final_results ta
join mr_class_final_results tb
on ta.deviceMAC=tb.deviceMAC
where ta.deviceMAC!='c098e5700195' and ta.deviceMAC!='c098e5700193' and ta.deviceMAC!='c098e57001A0' and ta.deviceMAC!='c098e5700193' and ta.deviceMAC!='c098e57000E6' and ta.deviceMAC!='c098e570018D' and ta.deviceMAC!='c098e57000CE' and ta.deviceMAC!='c098e5700169';

create view newNewClassEnergy as
select * from newClassEnergy union
select deviceMAC, location, category, avgEnergy, category from mr_final_results where category='Entertainment' and deviceType!='Cable Box' union
select deviceMAC, location, category, avgEnergy, category from mr_final_results where category='Computer' and deviceType!='Laptop Computer';
select * from mr_final_results where category='Entertainment' and deviceType!='Cable Box';

alter view class_breakdown as
select location, actCat, sum(actEnergy) as totEnergy from newNewClassEnergy where deviceMAC!='c098e5700195' and deviceMAC!='c098e5700193' and deviceMAC!='c098e57001A0' and deviceMAC!='c098e5700193' and deviceMAC!='c098e57000E6' and deviceMAC!='c098e570018D' and deviceMAC!='c098e57000CE' and deviceMAC!='c098e5700169' group by location, actCat;

alter view class_breakdown_new as
select location, classCat, sum(actEnergy) as totEnergy from newNewClassEnergy where deviceMAC!='c098e5700195' and deviceMAC!='c098e5700193' and deviceMAC!='c098e57001A0' and deviceMAC!='c098e5700193' and deviceMAC!='c098e57000E6' and deviceMAC!='c098e570018D' and deviceMAC!='c098e57000CE' and deviceMAC!='c098e5700169' group by location, classCat;

select * from newNewClassEnergy;
select * from newNewClassEnergy where actCat='Fridge' or classCat='Fridge' or actCat='Screen/Display' or classCat='Screen/Display';

select actCat, sum(totEnergy)/7 from class_breakdown group by actCat;
select sum(totEnergy) from class_breakdown_new;

select ta.*, tb.avgEnergy from 
(select actCat, sum(totEnergy)/7 as avgEnergy from class_breakdown group by actCat) ta
join
(select classCat, sum(totEnergy)/7 as avgEnergy from class_breakdown_new group by classCat) tb
on ta.actCat=tb.classCat;

# Energy distribution by category for all locations
# This uses mr_cat_breakdown and calculates min, max, mean, q1, and q3 for energy
create view mr_class_cat_en as
(select t1.category, min(t1.catSum) as minEn,
(select avg(catSum) from mr_class_cat_breakdown t2 where t1.category=t2.category and t2.catSum<=(select avg(catSum) from mr_class_cat_breakdown t9 where t9.category=t1.category)) as q1En,
avg(t1.catSum) as meanEn,
(select avg(catSum) from mr_class_cat_breakdown t3 where t1.category=t3.category and t3.catSum>=(select avg(catSum) from mr_class_cat_breakdown t10 where t10.category=t1.category)) as q3En,
max(t1.catSum) as maxEn
from mr_class_cat_breakdown t1
group by t1.category);

# Power distribution by category for all locations
# This uses mr_cat_breakdown and calculates min, max, mean, q1, and q3 for power
create view mr_class_cat_pwr as
(select t4.classCat, min(t4.avgPower) as minPwr,
(select avg(avgPower) from mr_class_final_results t5 where t4.classCat=t5.classCat and t5.avgPower<=(select avg(avgPower) from mr_class_final_results t7 where t7.classCat=t4.classCat)) as q1Pwr,
avg(t4.avgPower) as meanPwr,
(select avg(avgPower) from mr_class_final_results t6 where t4.classCat=t6.classCat and t6.avgPower>=(select avg(avgPower) from mr_class_final_results t8 where t8.classCat=t4.classCat)) as q3Pwr,
max(t4.avgPower) as maxPwr
from mr_class_final_results t4
where t4.avgPower>0
group by t4.classCat);

# Total data table for category breakdown
# For each category, min, max, mean, q1, and q3 for both energy and power
create view mr_class_cat_en_pwr as
select tEn.category, tEn.minEn, tEn.q1En, tEn.meanEn, tEn.q3En, tEn.maxEn, tPwr.minPwr, tPwr.q1Pwr, tPwr.meanPwr, tPwr.q3Pwr, tPwr.maxPwr from
mr_class_cat_en tEn
join
mr_class_cat_pwr tPwr
on tEn.category=tPwr.classCat
order by tEn.meanEn asc;

select * from mr_class_cat_en_pwr;
select t1.*, t2.meanEn from 
mr_class_cat_en t1 
join 
mr_cat_en t2 
on t1.category=t2.category
order by t1.meanEn desc;

show processlist;
kill 24915;








