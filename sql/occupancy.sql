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


# Query mr_occ_pb and mr_occ_blink tables
select * from mr_dat_occ_pb;
select * from mr_dat_occ_blink;

# Query together
alter view mr_dat_occ as
select t1.deviceMAC, t3.deviceName, t3.location, t1.room, t1.tsMin, t1.avgPower, t2.minMot from
(mr_dat_occ_pb t1
join mr_dat_occ_blink t2 
on t1.location=t2.location and t1.room=t2.room and t1.tsMin=t2.tsMin
join valid_powerblades_no1 t3
on t1.deviceMAC=t3.deviceMAC);

select * from mr_dat_occ t1 where deviceMAC='c098e570005d' and tsMin>'2017-03-29' and tsMin<'2017-04-05';

describe mr_dat_occ_corr;

select * from mr_dat_occ_corr where deviceType='Fan';

select deviceType, min(crossCorr) as minCrossCorr,
(select avg(crossCorr) from mr_dat_occ_corr where deviceType=ttop.deviceType and crossCorr<=(select avg(crossCorr) from mr_dat_occ_corr where deviceType=ttop.deviceType)) as t1CrossCorr,
avg(crossCorr) as meanCrossCorr, 
(select avg(crossCorr) from mr_dat_occ_corr where deviceType=ttop.deviceType and crossCorr>=(select avg(crossCorr) from mr_dat_occ_corr where deviceType=ttop.deviceType)) as t3CrossCorr,
max(crossCorr) as maxCrossCorr,
min(pOcc) as minPOcc, 
(select avg(pOcc) from mr_dat_occ_corr where deviceType=ttop.deviceType and pOcc<=(select avg(pOcc) from mr_dat_occ_corr where deviceType=ttop.deviceType)) as t1POcc,
avg(pOcc) as meanPOcc, 
(select avg(pOcc) from mr_dat_occ_corr where deviceType=ttop.deviceType and pOcc>=(select avg(pOcc) from mr_dat_occ_corr where deviceType=ttop.deviceType)) as t3POcc,
max(pOcc) as maxPOcc
from mr_dat_occ_corr ttop
group by deviceType
order by avg(pOcc) desc;



