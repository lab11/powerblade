# Basic table creation stuff
# Only to be run once, but saved for records

# Add keys to dat_powerblade
alter table dat_powerblade add index (timestamp);
alter table dat_powerblade add index (gatewayMAC);
alter table dat_powerblade add index (deviceMAC);
alter table dat_powerblade add index (power);

# Create ss_powerblade table
CREATE TABLE loc1_dat_powerblade LIKE dat_powerblade;
insert into loc1_dat_powerblade select * from dat_powerblade where gatewaymac='c098e5c00003' or gatewaymac='c098e5c00025' or gatewaymac='c098e5c00026';

# Describe
describe dat_powerblade;
describe inf_pb_lookup;
describe loc1_dat_powerblade;

# Create dat_blink table
CREATE TABLE dat_blink 
(id int(11) not null auto_increment, gatewayMAC char(12), deviceMAC char(12), curMot tinyint(1), advMot tinyint(1), minMot tinyint(1), timestamp datetime, 
primary key (id), index(gatewayMAC), index(deviceMAC), index(timestamp));
describe dat_blink;

CREATE TABLE dat_gnd_truth 
(id int(11) not null auto_increment, location int(1), dayst datetime, energy decimal(8,2), primary key (id), index(location), index(dayst), index locTime (location, dayst));

alter table inf_pb_lookup add column remTime datetime after startTime;
alter table inf_gw_lookup add column remTime datetime after startTime;
alter table inf_light_lookup add column remTime datetime after startTime;
alter table inf_blink_lookup add column remTime datetime after startTime;


describe avg_power;
create table final_results (id int(11) not null auto_increment, addedDate datetime, deviceMAC char(12), deviceName varchar(50), location int(1), category varchar(30), deviceType varchar(30), avgEnergy decimal(24,4), stdEnergy decimal(24,4), totEnergy decimal(24,4), avgPower decimal(24,4),
primary key (id), index (deviceMAC));
select * from final_results;

# This is the parallel table to final_results, used to store a reference to the data in final_results
create table final_gnd (id int(11) not null auto_increment, addedDate datetime, location int(1), startDate date, duration int(11), missingDays int(11), totEnergy decimal(24,4), primary key (id), index (location));
select * from final_gnd;

alter table final_gnd add column endDate date after startDate;
alter table final_gnd add column truthDays int(11) after duration;
alter table final_gnd add column totMeas decimal(24,4) after missingDays;
alter table final_gnd change totEnergy totGnd decimal(24,4);

describe final_gnd;

insert into final_results (addedDate) values (utc_timestamp());



# pb_lookup
create table inf_ss_pb_lookup (deviceMAC char(16), deviceName varchar(50));
alter table inf_ss_pb_lookup add column devType varchar(20);
alter table inf_ss_pb_lookup add index (deviceMAC, devType);

# Other useful stuff:
#	substring(timestamp,12,2)
# 	to "delete from": SET SQL_SAFE_UPDATES = 0;
#	load data local infile 'path/inf_ss_pb.txt' into table inf_ss_pb_lookup fields terminated by '\t';
