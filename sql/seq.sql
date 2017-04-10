create table temp_powerblade like dat_powerblade;
describe temp_powerblade;
drop table temp_powerblade;

delete from temp_powerblade where id>1;

insert into temp_powerblade (gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp)
select gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp
#from dat_powerblade where timestamp > date_sub(utc_timestamp(), interval 10 minute);
from dat_powerblade where timestamp between '2017-04-08 16:00:00' and '2017-04-08 17:00:00'
and deviceMAC in (select deviceMAC from valid_powerblades where location=0);
#from dat_powerblade where deviceMAC='c098e570005d' order by id desc limit 10000;
#from dat_powerblade where deviceMAC='c098e57000ce' order by id desc limit 10000;
#from dat_powerblade where deviceMAC='c098e5700210' order by id desc limit 10000;
#from dat_powerblade where deviceMAC='c098e5700115' order by id desc limit 10000;

select * from temp_powerblade order by seq;
select count(*) from temp_powerblade;


alter table temp_powerblade add index devTimeSeq (deviceMAC, timestamp, seq);
alter table temp_powerblade add index devDevSeq (deviceMAC, seq, timestamp);
alter table temp_powerblade add index devSeq (deviceMAC, seq);
alter table temp_powerblade add index (seq);
alter table temp_powerblade add index seqDev (seq, deviceMAC);
alter table temp_powerblade add index gwDevSeq (gatewayMAC, deviceMAC, seq);

describe temp_powerblade;

select ttop.deviceMAC, ttop.seqGap, count(*) from
(select t1.deviceMAC, t1.seq, t1.seq - ifnull(t2.seq, 0) as seqGap
from temp_powerblade t1
left join temp_powerblade t2
on t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from temp_powerblade t3 force index(devSeq) where t3.deviceMAC=t1.deviceMAC and t3.seq<t1.seq)) ttop
group by ttop.deviceMAC, ttop.seqGap;

#order by t1.deviceMAC, t1.seq limit 20000;


select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from temp_powerblade t1 force index (devSeq)
left join temp_powerblade t2 force index (devSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from temp_powerblade t3 force index(devSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=(t1.seq-1))) 
order by deviceMAC, seq, gatewayMAC asc limit 100000;

create table powerblade_seqGap as;
select tfull.gatewayMAC, tfull.deviceMAC, tfull.seqGap, count(*) from
(select tt1.gatewayMAC, tt1.deviceMAC, tt1.seq, case when greatest(tt1.seqGap, tt2.seqGap, tt3.seqGap, tt4.seqGap, tt5.seqGap, tt6.seqGap, tt7.seqGap, tt8.seqGap, tt9.seqGap) = 0 
then case when tt1.seq>=10 then 10 else tt1.seq end
else tt1.seq - greatest(tt1.seqGap, tt2.seqGap, tt3.seqGap, tt4.seqGap, tt5.seqGap, tt6.seqGap, tt7.seqGap, tt8.seqGap, tt9.seqGap) end as seqGap from

(select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from temp_powerblade t1 force index (devDevSeq)
left join temp_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from temp_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-1, 0)))) tt1

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from temp_powerblade t1 force index (devDevSeq)
left join temp_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from temp_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-2, 0)))) tt2
on tt1.gatewayMAC=tt2.gatewayMAC and tt1.deviceMAc=tt2.deviceMAC and tt1.seq=tt2.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from temp_powerblade t1 force index (devDevSeq)
left join temp_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from temp_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-3, 0)))) tt3
on tt1.gatewayMAC=tt3.gatewayMAC and tt1.deviceMAc=tt3.deviceMAC and tt1.seq=tt3.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from temp_powerblade t1 force index (devDevSeq)
left join temp_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from temp_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-4, 0)))) tt4
on tt1.gatewayMAC=tt4.gatewayMAC and tt1.deviceMAc=tt4.deviceMAC and tt1.seq=tt4.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from temp_powerblade t1 force index (devDevSeq)
left join temp_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from temp_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-5, 0)))) tt5
on tt1.gatewayMAC=tt5.gatewayMAC and tt1.deviceMAc=tt5.deviceMAC and tt1.seq=tt5.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from temp_powerblade t1 force index (devDevSeq)
left join temp_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from temp_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-6, 0)))) tt6
on tt1.gatewayMAC=tt6.gatewayMAC and tt1.deviceMAc=tt6.deviceMAC and tt1.seq=tt6.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from temp_powerblade t1 force index (devDevSeq)
left join temp_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from temp_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-7, 0)))) tt7
on tt1.gatewayMAC=tt7.gatewayMAC and tt1.deviceMAc=tt7.deviceMAC and tt1.seq=tt7.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from temp_powerblade t1 force index (devDevSeq)
left join temp_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from temp_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-8, 0)))) tt8
on tt1.gatewayMAC=tt8.gatewayMAC and tt1.deviceMAc=tt8.deviceMAC and tt1.seq=tt8.seq

join (select t1.gatewayMAC, t1.deviceMAC, t1.seq, ifnull(t2.seq, 0) as seqGap
from temp_powerblade t1 force index (devDevSeq)
left join temp_powerblade t2 force index (devDevSeq)
on t2.gatewayMAC=t1.gatewayMAC and t2.deviceMAC=t1.deviceMAC and
t2.seq=(select max(seq) from temp_powerblade t3 force index(devDevSeq) where t3.deviceMAC=t1.deviceMAC and t3.gatewayMAC=t1.gatewayMAC and (t3.seq=greatest(cast(t1.seq as signed)-9, 0)))) tt9
on tt1.gatewayMAC=tt9.gatewayMAC and tt1.deviceMAc=tt9.deviceMAC and tt1.seq=tt9.seq
) tfull

group by tfull.gatewayMAC, tfull.deviceMAC, tfull.seqGap;

order by deviceMAC, seq, gatewayMAC asc limit 100000;

select * from temp_powerblade where deviceMAC='c098e570005d' and seq=1398313;









