create table seq_powerblade like dat_powerblade;
describe seq_powerblade;
drop table seq_powerblade;

delete from seq_powerblade where id>1;

insert into seq_powerblade (gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp)
select gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp
#from dat_powerblade where timestamp > date_sub(utc_timestamp(), interval 10 minute);
from dat_powerblade where timestamp between '2017-04-08 16:00:00' and '2017-04-08 17:00:00'
and deviceMAC in (select deviceMAC from valid_powerblades where location=0);
#from dat_powerblade where deviceMAC='c098e570005d' order by id desc limit 10000;
#from dat_powerblade where deviceMAC='c098e57000ce' order by id desc limit 10000;
#from dat_powerblade where deviceMAC='c098e5700210' order by id desc limit 10000;
#from dat_powerblade where deviceMAC='c098e5700115' order by id desc limit 10000;

select * from seq_powerblade order by seq;
select count(*) from seq_powerblade;




create table powerblade_seqGap as;
select tfull.gatewayMAC, tfull.deviceMAC, tfull.seqGap, count(*) from
(select tt1.gatewayMAC, tt1.deviceMAC, tt1.seq, case when greatest(tt1.seqGap, tt2.seqGap, tt3.seqGap, tt4.seqGap, tt5.seqGap, tt6.seqGap, tt7.seqGap, tt8.seqGap, tt9.seqGap) = 0 
then case when tt1.seq>=10 then 10 else tt1.seq end
else tt1.seq - greatest(tt1.seqGap, tt2.seqGap, tt3.seqGap, tt4.seqGap, tt5.seqGap, tt6.seqGap, tt7.seqGap, tt8.seqGap, tt9.seqGap) end as seqGap from

(select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from seq_powerblade t1 force index (devDevSeq)
left join seq_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from seq_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-1, 0)))) tt1

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from seq_powerblade t1 force index (devDevSeq)
left join seq_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from seq_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-2, 0)))) tt2
on tt1.gatewayMAC=tt2.gatewayMAC and tt1.deviceMAc=tt2.deviceMAC and tt1.seq=tt2.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from seq_powerblade t1 force index (devDevSeq)
left join seq_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from seq_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-3, 0)))) tt3
on tt1.gatewayMAC=tt3.gatewayMAC and tt1.deviceMAc=tt3.deviceMAC and tt1.seq=tt3.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from seq_powerblade t1 force index (devDevSeq)
left join seq_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from seq_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-4, 0)))) tt4
on tt1.gatewayMAC=tt4.gatewayMAC and tt1.deviceMAc=tt4.deviceMAC and tt1.seq=tt4.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from seq_powerblade t1 force index (devDevSeq)
left join seq_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from seq_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-5, 0)))) tt5
on tt1.gatewayMAC=tt5.gatewayMAC and tt1.deviceMAc=tt5.deviceMAC and tt1.seq=tt5.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from seq_powerblade t1 force index (devDevSeq)
left join seq_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from seq_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-6, 0)))) tt6
on tt1.gatewayMAC=tt6.gatewayMAC and tt1.deviceMAc=tt6.deviceMAC and tt1.seq=tt6.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from seq_powerblade t1 force index (devDevSeq)
left join seq_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from seq_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-7, 0)))) tt7
on tt1.gatewayMAC=tt7.gatewayMAC and tt1.deviceMAc=tt7.deviceMAC and tt1.seq=tt7.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from seq_powerblade t1 force index (devDevSeq)
left join seq_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from seq_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-8, 0)))) tt8
on tt1.gatewayMAC=tt8.gatewayMAC and tt1.deviceMAc=tt8.deviceMAC and tt1.seq=tt8.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from seq_powerblade t1 force index (devDevSeq)
left join seq_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from seq_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-9, 0)))) tt9
on tt1.gatewayMAC=tt9.gatewayMAC and tt1.deviceMAc=tt9.deviceMAC and tt1.seq=tt9.seq
) tfull

group by tfull.gatewayMAC, tfull.deviceMAC, tfull.seqGap;











