# Basic testing for blink queries

# Basic contents of dat_blink, including in location 0
SELECT * FROM dat_blink where deviceMAC in (SELECT deviceMAC from active_blinks where location=0) order by id desc;
select count(*) from dat_blink;
select max(id) from dat_blink;
describe dat_blink;

# Group by time period, if active during that time
# This was only temporary, current queries use sum during that time
select t1.deviceMAC, t2.room, t1.ts, t1.minMot from
(SELECT ROUND(unix_timestamp(timestamp)/(5*60)) as timekey, min(timestamp) as ts, deviceMAC, max(minMot) as minMot
from dat_blink force index (devMIN)
where deviceMAC in (SELECT deviceMAC from active_blinks where location=0 group by deviceMAC)
and timestamp>'2017-04-15 00:00:00'
group by timekey, deviceMAC) t1
join
active_blinks t2
on t1.deviceMAC=t2.deviceMAC
order by t1.deviceMAC, t1.timekey;