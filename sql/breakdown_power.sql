# SQL script used for generating an energy breakdown, instantaneous power

# dat_start is the starting datetime
# dat_end is the ending datetime
SET @dat_start='2016-01-01 00:00:00';
SET @dat_end='2016-12-31 22:59:59';

# Generate ebreakdown table
DROP TABLE IF EXISTS ebreakdown;
CREATE TABLE ebreakdown AS
SELECT t1.deviceMAC AS deviceMAC, 
(SELECT t3.deviceName FROM inf_ss_pb_lookup t3 WHERE t1.deviceMAC=t3.deviceMAC) AS devName, 
(SELECT t2.energy FROM ss_powerblade t2 WHERE t1.deviceMAC=t2.deviceMAC AND t2.timestamp between @dat_start and @dat_end order by t2.timestamp desc LIMIT 1) AS finEnergy 
FROM ss_powerblade t1 
GROUP BY t1.deviceMAC 
ORDER BY finEnergy DESC;

# Old instpower method

# Generate instpower table (long running)
create table maxPower_new as select deviceMAC, least(500,max(power)) as maxP from ss_powerblade group by devicemac; 
drop table instpower_new;
create table instpower_new as 
select t1.deviceMAC, 
(select round(t2.power) from ss_powerblade as t2 
where t2.deviceMAC=t1.deviceMAC and 
round(t2.power)>(select 0.1*maxP from maxPower_new t5 where t1.deviceMAC=t5.deviceMAC) 
group by round(t2.power) order by count(*) desc limit 0,1) as topPower 
from ss_powerblade as t1 group by t1.deviceMAC;

# Prepare data for export
# select t1.*, t2.toppower from ebreakdown t1 join instpower_new t2 on t1.devicemac=t2.devicemac where t1.devname is not null order by t1.finenergy desc;
create table ss_data as 
select t1.devicemac, t1.devname, t1.finenergy, t2.toppower 
from ebreakdown t1 
join instpower_new t2 
on t1.devicemac=t2.devicemac 
where t1.devname is not null 
order by t1.finenergy desc;

# Generate CDF from previous two tables
set @csum := 0;
select t1.*, (@csum := @csum + t1.finenergy) as cdf from ss_data t1 order by t1.finenergy desc;

# Create combination graph based on category
select t1.devType as devType, sum(t2.finenergy) as finenergy, AVG(t2.toppower) as toppower 
from inf_ss_pb_lookup t1 
join ss_data t2 
on t1.devicemac=t2.devicemac 
group by t1.devtype order by finenergy desc;
