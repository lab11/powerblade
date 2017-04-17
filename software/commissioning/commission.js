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
var readline = require('readline');
var mysql = require('mysql');
var exec = require('child_process').exec;
var spawn = require('child_process').spawn;

var device_id;
var device_id_format = '';
var device_id_short;

var db_connection;

const rl = readline.createInterface({
	input: process.stdin,
	output: process.stdout
});

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
	db_connection = mysql.createConnection({
		host		: aws_config.test_ip,
		user		: aws_config.test_usr,
		password	: aws_config.test_pw,
		database	: aws_config.test_db
	});
}
else {
	console.log("Connecting to " + aws_config.sql_ip);
	db_connection = mysql.createConnection({
		host		: aws_config.sql_ip,
		user		: aws_config.sql_usr,
		password	: aws_config.sql_pw,
		database	: aws_config.sql_db
	});	
}

var argval = process.argv[2];
if(argval == null || argval == '-a') {
	argval = '-a'
	start_process();
}
else if(argval == '-c') {
	console.log("Short run: Calibration")
	device_id_short = process.argv[3];
	device_id = 'c098e570' + device_id_short.replace(':', '');
	device_id_format = 'c0:98:e5:70:' + device_id_short;
	switch_to_calib();
}
else if(argval == '-m') {

	argval = '-a';	// Used to note that the full process will still run (for database purposes)
	device_id_short = process.argv[3];
	device_id = 'c098e570' + device_id_short.replace(':', '');
	device_id_format = 'c0:98:e5:70:' + device_id_short;
	console.log("\nStep 1: Running with device ID " + device_id_format);
	prepare_nrf();
}
else if(argval == '-n') {	// Want a new MAC address (overwrite existing)
	argval = '-a';	// Used to note that the full process will still run (for database purposes)
	gather_device_id(false);
}
else {
	console.log("Unknown input argument: " + argval);
	process.exit();
}

function start_process() {
	/*************************************************************/
	// Step #1: Determine the device's ID, or assign a new ID
	/*************************************************************/
	console.log("\nStep 1: Checking for Device ID");
	var JLinkExe = "JLinkExe";
	var JLinkOptions = "-device nrf51822 -if swd -speed 1000 -AutoConnect 1".split(" ");

	var terminal = spawn(JLinkExe, JLinkOptions);

	var jlink_output = "";

	terminal.stdout.on('data', function (data) {
		jlink_output += data.toString('utf8');
	});

	terminal.stderr.on('data', function (data) {
		console.log("Got error: " + data);
	});

	terminal.on('exit', function (code) {
		if (jlink_output.indexOf("USB...FAILED") !== -1) {
			throw "ERROR: Cannot find JLink hardware. Is USB attached?";
		} else if (jlink_output.indexOf("Can not connect to target.") !== -1) {
			throw "ERROR: Cannot find PowerBlade. Is JTAG connected?";
		} else if (code != 0) {
			console.log(jlink_output);
			throw "ERROR: JTAG returned with error code " + code;
		} else {
			var data_index = jlink_output.indexOf("0001FFF8 =");
			if (data_index === -1) {
				console.log(jlink_output);
				throw "ERROR: JTAG read of BLE address failed";
			} else {
				var hex_str_MSB = jlink_output.substring(data_index+20, data_index+39).trim();
				var hex_str_LSB = jlink_output.substring(data_index+11, data_index+19).trim();
				if (hex_str_MSB == '' || hex_str_LSB == '') {
					throw "ERROR: Could not read address from flash";
				}
				var hex_str = hex_str_MSB.concat(hex_str_LSB).replace(/^0+/, '').toLowerCase();
				if (hex_str == "ffffffffffffffff") {
					gather_device_id(false);
				} else {
					hex_str = hex_str.replace(/(.{2})/g,"$1:").slice(0,-1);
					device_id_format = hex_str;
					gather_device_id(true);
				}
			}
		}
	});

	terminal.stdin.write("r\n");
	terminal.stdin.write("mem32 0x1FFF8, 2 \n");
	terminal.stdin.write("q\n");
	terminal.stdin.end();
}

function gather_device_id(is_success) {
	if(is_success) {
		//device_id = // Device ID;
		console.log("\nDevice ID Found: " + device_id_format + "\n");
		device_id = device_id_format.split(':').join('');
		device_id_short = device_id_format.slice(12, 17);
		program_nrf();
	}
	else {
		var id_query = 'SELECT CONV(CONV(MAX(deviceMAC), 16, 10) + 1, 10, 16) as newMac from dat_pb_calib;'
		db_connection.query(id_query, function(err, rows, fields) {
			if (err) throw err;
			device_id = rows[0].newMac.toLowerCase();
			for (var i = 0; i < 12; i = i + 2) {
				device_id_format += device_id.slice(i, i + 2) + ':';
			}
			device_id_format = device_id_format.slice(0, -1);
			device_id_short = device_id_format.slice(12, 17);
			console.log("\nNew Device, Assigning to Device ID " + device_id_format);
			console.log("Please print out and apply a new address sticker")
			rl.question('Push enter when ready', function(answer) {
				prepare_nrf();
			});
		});
	}
}

/*************************************************************/
// Step #2: Program the nrf
/*************************************************************/
function prepare_nrf() {
	console.log("\nStep 2: Program the nrf51822. Move to the jLink debugger (6 pin interface).");
	rl.question('Push enter when ready', function(answer) {
		program_nrf();
	});
}

function program_nrf() {
	console.log("\nProgramming nRF51822 with Device ID " + device_id_format + " (short: " + device_id_short + ")");
	var child = exec("make flash ID=" + device_id_format + " -C " + process.env.PB_ROOT + "/software/nrf51822/apps/powerblade", function(error, stdout, stderr) {
		if (error) throw error;
		console.log("Done programming nrf51822");
		if(argval != '-a') {
			console.log("Adding database entry");
			var nrf_query = 'INSERT INTO dat_pb_calib (deviceMAC, nrf_prog_date) values (\'' + device_id + '\', now());'
			db_connection.query(nrf_query, function(err, rows, fields) {
				if (err) throw err;
				console.log("Database updated to reflect state of " + device_id_format)
				switch_to_msp();
			});	
		}
		else {
			switch_to_msp();
		}
	});
}

/*************************************************************/
// Step #3: Program the MSP430
/*************************************************************/
function switch_to_msp() {
	console.log("\nStep 3: Program the MSP430. Move to the TI debugger (10 pin interface).");
	rl.question('Push enter when ready', function(answer) {
		program_msp();
	});
}

function program_msp() {
	console.log("\nProgramming the MSP430");
	var child = exec(process.env.PB_ROOT + "/software/msp_images/flash_powerblade", function(error, stdout, stderr) {
		if (error) {
			if(stdout.split('\n').slice(-4, -3)[0].indexOf('Could not reset device') > -1) {
				console.log("Warning: could not reset the MSP430 - likely OK unless problem persists");
			}
			else {
				throw error;
			}
		}
		console.log("Done programming MSP430");
		if(argval != '-a') {
			console.log("Adding database entry");
			var msp_query = 'INSERT INTO dat_pb_calib (deviceMAC, msp_prog_date) values (\'' + device_id + '\', now());'
			db_connection.query(msp_query, function(err, rows, fields) {
				if (err) throw err;
				console.log("Database updated to reflect state of " + device_id_format)
				switch_to_calib();
			});	
		}
		else {
			switch_to_calib();
		}
	});
}

/*************************************************************/
// Step #4: Calibrate the PowerBlade
/*************************************************************/
function switch_to_calib() {
	console.log("\nStep 4: Preparing to calibrate. Move to the calibration rig.");
	rl.question('Push enter when ready', function(answer) {
		calibrate();
	});
}

function calibrate() {
	var error = false;
	console.log("\nRunning calibration")
	var calib = spawn(process.env.PB_ROOT + "data_collection/internal_calibration/calibrate.js", ['-s', '-m', device_id_short]);//, function(error, stdout, stderr) {
	calib.stdout.on('data', function(data) {
		process.stdout.write("\t[calib]: " + data.toString());
		if(data.toString().indexOf('XXXXX') > -1) {
			console.log("Calibration failed, retrying");
			error = true;
			calib.kill();
			calibrate();
		}
	});
	calib.stderr.on('data', function(data) {
		process.stdout.write(data.toString());
	})
	calib.on('exit', function(code) {
		// if (error) throw error;
		// if (stdout.indexOf('XXXXXX') > -1) {
		// 	console.log("Calibration failed, retrying");
		// 	console.log(stdout);
		// 	calibrate();
		// }
		// else if (stdout.indexOf('Calibrating...')) {
		if(error == false) {
			console.log("Done calibrating");
			console.log("Adding database entry");
			var calib_query;
			if(argval == '-a') {
				calib_query = 'INSERT INTO dat_pb_calib (deviceMAC, nrf_prog_date, msp_prog_date, msp_prog_val, msp_calib_date) values (\'' + device_id + '\', now(), now(), \'2.3.0\', now());'
			}
			else {
				calib_query = 'INSERT INTO dat_pb_calib (deviceMAC, msp_calib_date) values (\'' + device_id + '\', now());'
			}
			
			db_connection.query(calib_query, function(err, rows, fields) {
				if (err) throw err;
				console.log("Database updated to reflect state of " + device_id_format)
				clean_up();
			});			
		}
		// }
	});
}

/*************************************************************/
// Clean up
/*************************************************************/
function clean_up() {
	db_connection.end();
	process.exit();
}













