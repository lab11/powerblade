# Basic table creation stuff
# Only to be run once, but saved for records


# Create dat_blink table
CREATE TABLE dat_blink 
(id int(11) not null auto_increment, gatewayMAC char(12), deviceMAC char(12), 
curMot tinyint(1), advMot tinyint(1), minMot tinyint(1), 
timestamp datetime, 
primary key (id), index(gatewayMAC), index(deviceMAC), index(timestamp));
describe dat_blink;


# Create dat_gnd_truth table
CREATE TABLE dat_gnd_truth 
(id int(11) not null auto_increment, location int(1), dayst datetime, energy decimal(8,2), 
primary key (id), index(location), index(dayst), index locTime (location, dayst));


# Addition of remTime column to inf tables
alter table inf_pb_lookup add column remTime datetime after startTime;
alter table inf_gw_lookup add column remTime datetime after startTime;
alter table inf_light_lookup add column remTime datetime after startTime;
alter table inf_blink_lookup add column remTime datetime after startTime;


# Final results table - when a long running query is run, the user has the option to store the results
# The most recent entry for each device is used in the final energy calculations
create table final_results 
(id int(11) not null auto_increment, addedDate datetime, 
deviceMAC char(12), deviceName varchar(50), location int(1), category varchar(30), deviceType varchar(30), 
avgEnergy decimal(24,4), stdEnergy decimal(24,4), totEnergy decimal(24,4), avgPower decimal(24,4),
primary key (id), index (deviceMAC));

alter table final_gnd add column endDate date after startDate;
alter table final_gnd add column truthDays int(11) after duration;
alter table final_gnd add column totMeas decimal(24,4) after missingDays;
alter table final_gnd change totEnergy totGnd decimal(24,4);


# This is the parallel table to final_results, used to store a reference to the data in final_results
create table final_gnd 
(id int(11) not null auto_increment, addedDate datetime, 
location int(1), startDate date, duration int(11), missingDays int(11), totEnergy decimal(24,4), 
primary key (id), index (location));



# Deltas table
create table dat_delta (id int(11) not null auto_increment, dayst datetime, deviceMAC char(12), 
ct5 int(11), spk5 int(11), ct10 int(11), spk10 int(11), ct15 int(11), spk15 int(11),
ct25 int(11), spk25 int(11), ct50 int(11), spk50 int(11), ct75 int(11), spk75 int(11), 
ct100 int(11), spk100 int(11), ct150 int(11), spk150 int(11), ct250 int(11), spk250 int(11), 
ct500 int(11), spk500 int(11), primary key (id), index (dayst), index (deviceMAC), index devDay (deviceMAC, dayst));

describe dat_delta;


# Other useful stuff:
# 	to "delete from": SET SQL_SAFE_UPDATES = 0;
