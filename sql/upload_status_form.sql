
load data local infile 'C:/Users/Sam/Downloads/pb.csv' into table inf_pb_lookup fields terminated by ',' (deviceMAC, deviceName, category, deviceType, permanent, startTime, endTime);
load data local infile 'C:/Users/Sam/Downloads/gw.csv' into table inf_gw_lookup fields terminated by ',' (gatewayMAC, location, startTime, endTime);


