#! /usr/bin/env node

// Collect BLE packets over MQTT
//  Push to SQL for storage

var fs = require('fs');
var ini = require('ini');
var mysql = require('mysql');
var getmac = require('getmac');
var mqtt = require('mqtt'); // connect to the local MQTT broker

var cron = require('node-cron');
var os = require('os');

var debug = false;
var test = false;
process.argv.forEach(function (val, index, array) {
    if(val == "-d" || val == "--debug") {
        debug = true;
        console.log("Running with verbose output");
    }
    else if(val == "-t" || val == "--test") {
        test = true;
        console.log("Running with testbed database");
    }
});

// configuration
try {
    var aws_config_file = fs.readFileSync('/etc/swarm-gateway/powerblade-aws.conf', 'utf-8');
    var aws_config = ini.parse(aws_config_file);
} catch (e) {
    console.log(e);
    console.log("\nCannot find /etc/swarm-gateway/powerblade-aws.conf or configuration invalid.");
    process.exit(1);
}

if(test == false) {
    console.log("Connecting to " + aws_config.sql_ip);
    var db_connection = mysql.createConnection({
      host     : aws_config.sql_ip,
      user     : aws_config.sql_usr,
      password : aws_config.sql_pw,
      database : aws_config.sql_db
    });
}
else {
    console.log("Connecting to " + aws_config.test_ip);
    var db_connection = mysql.createConnection({
      host     : aws_config.test_ip,
      user     : aws_config.test_usr,
      password : aws_config.test_pw,
      database : aws_config.test_db
    }); 
}

// Get gateway mac address
var gateway_mac;
getmac.getMac(function(err,macAddress) {
    if (err) throw err;
    gateway_mac = macAddress.replace(new RegExp(':', 'g'), '');
});

cron.schedule('0,45 * * * *', function() {

	if(debug) {
		console.log("Running status process")
	}

    // Get local gateway IP address
    var gateway_ip;
    var ifaces = os.networkInterfaces();
    ifaces.eth0.forEach( function(element) {
        if(element.family == 'IPv4') {
            gateway_ip = element.address;
        }
    });

    // Get public gateway IP address
    var public_ip;
    var getIP = require('external-ip')();
    getIP( function(err, ip) {
        if(err) throw err;
        public_ip = ip;
    
        // Post all three values to SQL
        var loadQuery = 'INSERT INTO inf_gw_status (timestamp, gatewayMAC, gatewayIP, gatewayStrIP, publicIP, publicStrIP) VALUES (now(), \'' + gateway_mac + '\', INET_ATON(\'' + gateway_ip + '\'), \'' + gateway_ip + '\', INET_ATON(\'' + public_ip + '\'), \'' + public_ip + '\');';
        console.log(loadQuery);

        db_connection.query(loadQuery, function(err, rows, fields) {
            if (err) {
            	if(err == "ETIMEDOUT") {
            		console.log("Error " + err + ": retrying");
            		db_connection.query(loadQuery, function(err, rows, fields) {
            			if (err) throw err;
            			console.log("Uploaded on second try for " + gateway_mac + " at " + gateway_ip + ", " + public_ip);
            		});
            	}
            	else {
            		throw err;
            	}
            }
            else if(debug) {
                console.log("Done uploading status for " + gateway_mac + " at " + gateway_ip + ", " + public_ip);
            }
        });
    });
});

