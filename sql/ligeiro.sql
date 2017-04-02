
select * from dat_powerblade where gatewayMAC='c098e5c00027' order by timestamp desc;# or gatewayMAC='c098e5c00025' or gatewayMAC='c098e5c0002e' order by timestamp asc;

select t1.*, t2.room, t3.deviceName, t3.room from
(select gatewayMAC, deviceMAC, count(*) as count from dat_ligeiro 
where gatewayMAC='c098e5c00027' or gatewayMAC='c098e5c00025' or gatewayMAC='c098e5c0002e' 
group by gatewayMAC, deviceMAC) t1
join active_gateways t2
on t1.gatewayMAC=t2.gatewayMAC
join active_lights t3
on t1.deviceMAC=t3.deviceMAC;


select * from inf_gw_status where gatewayMAC='c098e5c00025' or gatewayMAC='c098e5c0002e' order by timestamp desc;


