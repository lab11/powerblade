
select * from dat_powerblade where gatewayMAC='c098e5c00027' order by timestamp desc;# or gatewayMAC='c098e5c00025' or gatewayMAC='c098e5c0002e' order by timestamp asc;

select t1.*, t2.room as troom, t3.deviceName, t3.room, t3.location from
(select gatewayMAC, deviceMAC, count(*) as count from dat_ligeiro 
where gatewayMAC='c098e5c00027' or gatewayMAC='c098e5c00025' or gatewayMAC='c098e5c0002e' 
group by gatewayMAC, deviceMAC) t1
join active_gateways t2
on t1.gatewayMAC=t2.gatewayMAC
join (select * from valid_lights where location=0) t3
on t1.deviceMAC=t3.deviceMAC;

select t1.gatewayMAC, t1.deviceMAC, t1.avgCount, t1.stdCount, t2.room as troom, t3.deviceName, t3.room, t3.location from
(select ttemp.gatewayMAC, ttemp.deviceMAC, avg(ttemp.count) as avgCount, stddev(ttemp.count) as stdCount from 
(select date(timestamp) as dayst, gatewayMAC, deviceMAC, count(*) as count from dat_ligeiro
where gatewayMAC='c098e5c00027' or gatewayMAC='c098e5c00025' or gatewayMAC='c098e5c0002e'
group by dayst, gatewayMAC, deviceMAC) ttemp
group by ttemp.deviceMAC) t1
join active_gateways t2
on t1.gatewayMAC=t2.gatewayMAC
join (select * from valid_lights where location=0) t3
on t1.deviceMAC=t3.deviceMAC;


select * from inf_gw_status where gatewayMAC='c098e5c00025' or gatewayMAC='c098e5c0002e' order by timestamp desc;


select * from dat_ligeiro where deviceMAC in (select deviceMAC from dat_ligeiro where deviceMAC<='c098e5d00024' group by deviceMAC) limit 10000000;

select * from dat_ligeiro limit 10000000;

