# Pre-fix data
select timestamp,power,pf from dat_powerblade where deviceMAC='c098e570015e' and timestamp between '2017-02-18 18:30:00' and '2017-02-18 18:40:00';
select avg(power) as power, avg(pf) as pf from dat_powerblade where deviceMAC='c098e570015e' and timestamp between '2017-02-18 18:30:00' and '2017-02-18 18:40:00';

# Post-fix data
select timestamp,power,pf from dat_powerblade where deviceMAC='c098e570015e' and timestamp between '2017-02-22 00:35:00' and '2017-02-22 00:45:00';
select avg(power) as power, avg(pf) as pf from dat_powerblade where deviceMAC='c098e570015e' and timestamp between '2017-02-22 00:35:00' and '2017-02-22 00:45:00';