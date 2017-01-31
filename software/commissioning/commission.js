#!/usr/bin/env node

/*********************************************************
*
* This is the commissioning script for PowerBlades
* The script performs four functions, 2-4 can be suppressed
*
*	1. Determine Device ID
*		1.1 If the PowerBlade already has a Device ID, save it
*		1.2 If the PowerBlade does not have a Device ID, query AWS for next lowest available
*
*	2. Program the nRF with the newest software image and specified Device ID
*		2.1 Insert entry in AWS specifying date and version
*
*	3. Program the MSP430 with the newest software image
*		3.1 Insert entry in AWS specifying date and version
*
*	4. Run calibration procedure 
*		4.1 Insert entry in AWS specifying date, version, 
*
**********************************************************/

var fs = require('fs');
var ini = require('ini');
var mysql = require('mysql');
var exec = require('child_process').exec

// AWS Configuration
try {
	var aws_config_file = fs.readFileSync('/etc/swarm-gateway/powerblade-aws.conf', 'utf-8');
	var aws_config = ini.parse(aws_config_file);
}
catch (e) {
	console.log(e);
	console.log("\nCannot file config file or config invalid");
	process.exit(1);
}

// Connect to AWS
var test = false;
if(test) {
	console.log("Connecting to " + aws_config.test_ip);
	var db_connection = mysql.createConnection({
		host		: aws_config.test_ip,
		user		: aws_config.test_usr,
		password	: aws_config.test_pw,
		database	: aws_config.test_db
	});
}
else {
	console.log("Connecting to " + aws_config.sql_ip);
	var db_connection = mysql.createConnection({
		host		: aws_config.sql_ip,
		user		: aws_config.sql_usr,
		password	: aws_config.sql_pw,
		database	: aws_config.sql_db
	});	
}

// Step #1: Determine the device's ID, or assign a new ID
var device_id;
//if(/* Check if device has ID */) {
if(false) {
	//device_id = // Device ID;
	program_nrf();
}
else {
	var id_query = 'SELECT CONV(CONV(MAX(deviceMAC), 16, 10) + 1, 10, 16) as newMac from pb_calib;'
	db_connection.query(id_query, function(err, rows, fields) {
		if (err) throw err;
		device_id = rows[0].newMac;
		program_nrf();
	});
}

// Step #2: Program the nrf
function program_nrf() {
	console.log("Device ID: " + device_id);
	var child = exec("make flash ID=c0:98:e5:70:01:5d -C $PB_ROOT/software/nrf51822/apps/powerblade", function(error, stdout, stderr) {
		
	});
}

db_connection.end();












