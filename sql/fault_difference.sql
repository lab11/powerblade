# Pre-fix data
select timestamp,power,pf from dat_powerblade where deviceMAC='c098e570015e' and timestamp between '2017-02-18 18:30:00' and '2017-02-18 18:40:00';
select avg(power) as power, avg(pf) as pf from dat_powerblade where deviceMAC='c098e570015e' and timestamp between '2017-02-18 18:30:00' and '2017-02-18 18:40:00';

# Post-fix data
select timestamp,power,pf from dat_powerblade where deviceMAC='c098e570015e' and timestamp between '2017-02-22 00:35:00' and '2017-02-22 00:45:00';
select avg(power) as power, avg(pf) as pf from dat_powerblade where deviceMAC='c098e570015e' and timestamp between '2017-02-22 00:35:00' and '2017-02-22 00:45:00';



# Finding the reset in the router
select t1.deviceMAC, t2.deviceType, t2.location, date(t1.timestamp), min(t1.seq) from 
(dat_powerblade t1 
join valid_powerblades_no1 t2
on t1.deviceMAC=t2.deviceMAC)
where t1.deviceMAC in (select deviceMAC from valid_powerblades_no1 where deviceType='Modem')
and (t1.seq<1000)
group by date(t1.timestamp);

select * from dat_powerblade where
deviceMAC='c098e5700167'
and date(timestamp)='2017-04-17'
and seq=3;


select avg(power) from dat_powerblade where
deviceMAC='c098e5700167'
and timestamp between '2017-04-16 12:00:00' and '2017-04-17 17:00:00';

select avg(power) from dat_powerblade where
deviceMAC='c098e5700167'
and timestamp between '2017-04-17 20:00:00' and '2017-04-17 23:00:00';

show processlist;

select * from dat_powerblade where
deviceMAC='c098e570004b'
and timestamp between '2017-05-01 17:30:00' and '2017-05-01 19:00:00'
order by timestamp asc;


# Reproduce dat_delta
'select t1.dayst, t1.deviceMAC, ' \
		'coalesce(t2.avgPwr, 0) as avgPwr, coalesce(t2.varPwr, 0) as varPwr, coalesce(t2.maxPwr, 0) as maxPwr, coalesce(t2.minPwr, 0) as minPwr, ' \
		't1.count as count, ' \
		'coalesce(t2.count, 0)/t1.count as dutyCycle, ' \
		'coalesce(t4.ct5, 0) as ct5, coalesce(t4.spk5, 0) as spk5, coalesce(t4.ct10, 0) as ct10, coalesce(t4.spk10, 0) as spk10, ' \
		'coalesce(t4.ct15, 0) as ct15, coalesce(t4.spk15, 0) as spk15, coalesce(t4.ct25, 0) as ct25, coalesce(t4.spk25, 0) as spk25, ' \
		'coalesce(t4.ct50, 0) as ct50, coalesce(t4.spk50, 0) as spk50, coalesce(t4.ct75, 0) as ct75, coalesce(t4.spk75, 0) as spk75, ' \
		'coalesce(t4.ct100, 0) as ct100, coalesce(t4.spk100, 0) as spk100, coalesce(t4.ct150, 0) as ct150, coalesce(t4.spk150, 0) as spk150, ' \
		'coalesce(t4.ct250, 0) as ct250, coalesce(t4.spk250, 0) as spk250, coalesce(t4.ct500, 0) as ct500, coalesce(t4.spk500, 0) as spk500, ' \
		't3.deviceType ' \
		'from ' \
		'(select ROUND(unix_timestamp(timestamp)/(24*60*60)) as timekey, date(timestamp) as dayst, ' \
		'deviceMAC, ' \
		'max(power) as maxPwr, ' \
		'count(*) as count ' \
		'from dat_powerblade ' \
		'where deviceMAC in (select deviceMAC from valid_powerblades ' \
			'where deviceType in (\'' + devType + '\') ' \
			'and location!=1) ' \
		'and timestamp>\'2017-03-01 00:00:00\' ' \
		'group by deviceMAC, timekey) t1 ' \
		'left join ' \
		'(select ROUND(unix_timestamp(timestamp)/(24*60*60)) as timekey, date(timestamp) as dayst, ' \
		'deviceMAC, ' \
		'avg(power) as avgPwr, var_pop(power) as varPwr, max(power) as maxPwr, min(power) as minPwr, ' \
		'count(*) as count ' \
		'from dat_powerblade tpa ' \
		'where deviceMAC in (select deviceMAC from valid_powerblades ' \
			'where deviceType in (\'' + devType + '\') ' \
    		'and location!=1) ' \
		'and power>(select case when maxPower>10 then 0.1*maxPower else 0.5*maxPower end from maxPower_pb tpb where tpa.deviceMAC=tpb.deviceMAC) ' \
		'and timestamp>\'2017-03-01 00:00:00\' ' \
		'group by deviceMAC, timekey) t2 ' \
		'on t1.timekey=t2.timekey and t1.deviceMAC=t2.deviceMAC ' \
		'left join ' \
		'(select * from valid_powerblades where location!=1) t3 ' \
		'on t1.deviceMAC=t3.deviceMAC ' \
		'left join ' \
		'mr_dat_delta t4 ' \
		'on t1.deviceMAC=t4.deviceMAC and t1.dayst=t4.dayst ' \
		'where t1.count>100;'








