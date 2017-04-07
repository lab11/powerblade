
create table loc0_dat_powerblade like dat_powerblade;

describe loc0_dat_powerblade;

select * from valid_powerblades where location=0;

insert into loc0_dat_powerblade (gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp)
select gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, flags, timestamp 
from dat_powerblade force index (devTimePower)
where timestamp>='2017-03-18 00:00:00' and timestamp<='2017-04-03 23:59:59'
and deviceMAC in (select deviceMAC from valid_powerblades where location=0);

select deviceMAC from loc0_dat_powerblade group by deviceMAC;
