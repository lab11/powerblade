#!/usr/bin/env node

// imports
var noble = require('noble');
var fs = require('fs');
var SSH = require('simple-ssh');

// input from user
var target_device = 'c0:98:e5:70:45:36';
var wattage = 200;
var voltage = 120;
var read_config = false;
var local = false;
var server = false;
for(var i = 0; i < process.argv.length; i++) {
    var val = process.argv[i];
    if(val == "-m") {
        target_device = "c0:98:e5:70:" + process.argv[++i];  // Additional increment of i
    }
    else if(val == "--mac") {
        target_device = process.argv[++i];   // Additional increment of i
    }
    else if(val == "-v" || val == "--voltage") {
        if(server) {
            console.log("Error: cannot specify both -s (server) and -v (voltage) or -p (power)");
            process.exit();
        }
        else {
            local = true;
        }

        voltage = process.argv[++i];        // Additional increment of i
    }
    else if(val == "-p" || val == "--power") {
        if(server) {
            console.log("Error: cannot specify both -s (server) and -v (voltage) or -p (power)");
            process.exit();
        }
        else {
            local = true;
        }

        wattage = process.argv[++i];        // Additional increment of i
    }
    else if(val == "-r" || val == "--read") {
        read_config = true;
    }
    else if(val == "-s" || val == "server") {
        if(local) {
            console.log("Error: cannot specify both -s (server) and -v (voltage) or -p (power)");
            process.exit();
        }
        else {
            console.log("Connecting to load...")
            server = true;
        }

        var ssh = new SSH ({
            host: 'lab11power.ddns.net',
            user: 'pi',
            key: require('fs').readFileSync('/home/powerblade/.ssh/id_rsa_pb')
        });

        console.log("Reading power and voltage values from load...")
        ssh.exec('./aps-3b12/aps_3B12.py read', {
            out: function(stdout) {
                stdlist = stdout.replace('[','').replace(']','').replace('\n','').split(',');
                voltage = parseFloat(stdlist[0]);
                wattage = parseFloat(stdlist[1]);

                if(wattage < 98 || wattage > 102) {
                    console.log("Wattage out of correct band, setting to 100 W...")
                    ssh.exec('./aps-3b12/aps_3B12.py 100', {
                        out: function(stdout) {
                            stdlist = stdout.replace('[','').replace(']','').replace('\n','').split(',');
                            voltage = parseFloat(stdlist[0]);
                            wattage = parseFloat(stdlist[1]);
                            startScanningOnPowerOn(voltage, wattage, target_device);
                        }
                    }).start();
                }
                else {
                    startScanningOnPowerOn(voltage, wattage, target_device);
                }
            }
        }).start();
    }
}

if(server == false) {
	startScanningOnPowerOn(voltage, wattage, target_device);
}

// Start up BLE scanning
function startScanningOnPowerOn(voltage, wattage, target_device) {
    if (noble.state === 'poweredOn') {
        noble.startScanning([], true);
        console.log("Looking for " + target_device);
		console.log("Calibrating at " + wattage + " W and " + voltage + " V");
    } else {
        noble.once('stateChange', startScanningOnPowerOn);
    }
};

// function fn_calibrate(voltage, wattage, target_device) {
// reference to discovered peripheral
var powerblade_periph;

// internal calibration service
var calibration_service_uuid = '57c4ed0b9461d99e844ed5aa70304b49';
var calibration_wattage_uuid = '57c4ed0c9461d99e844ed5aa70304b49';
var calibration_voltage_uuid = '57c4ed0d9461d99e844ed5aa70304b49';
var calibration_control_uuid = '57c4ed0e9461d99e844ed5aa70304b49';
var calibration_wattage_char;
var calibration_voltage_char;
var calibration_control_char;

/*XXX REMOVE
// raw sample collection service
var rawSample_service_uuid = 'cead01af7cf8cc8c1c4e882a39d41531';
var rawSample_start_uuid   = 'cead01b07cf8cc8c1c4e882a39d41531';
var rawSample_data_uuid    = 'cead01b17cf8cc8c1c4e882a39d41531';
var rawSample_status_uuid  = 'cead01b27cf8cc8c1c4e882a39d41531';
var rawSample_start_char;
var rawSample_data_char;
var rawSample_status_char;
var sampleData = new Buffer(0);
*/

// device configuration service
var config_service_uuid = '50804da1b988f888ec43b957e5acf999';
var config_status_uuid  = '50804da2b988f888ec43b957e5acf999';
var config_voff_uuid    = '50804da3b988f888ec43b957e5acf999';
var config_ioff_uuid    = '50804da4b988f888ec43b957e5acf999';
var config_curoff_uuid  = '50804da5b988f888ec43b957e5acf999';
var config_pscale_uuid  = '50804da6b988f888ec43b957e5acf999';
var config_vscale_uuid  = '50804da7b988f888ec43b957e5acf999';
var config_whscale_uuid = '50804da8b988f888ec43b957e5acf999';
var config_status_char;
var config_voff_char;
var config_ioff_char;
var config_curoff_char;
var config_pscale_char;
var config_vscale_char;
var config_whscale_char;

// start BLE scanning
// noble.on('stateChange', function(state) {
if (noble.state === 'poweredOn') {
    console.log("Starting scan...\n");
    noble.startScanning([], true);
} else {
    noble.stopScanning();
}
// });

// exit when disconnected
noble.on('disconnect', function () {
    console.log('Disconnected');
    process.exit(0);
});

// find correct device and connect to it
var restart_count = 0;
var found_peripheral;
noble.on('discover', function (peripheral) {
    //console.log(peripheral.address);
    if (peripheral.address == target_device) {
        noble.stopScanning( function() {
	        console.log('Found PowerBlade (' + peripheral.address +')\n');
	        process.stdout.write('Connecting... ');
	        powerblade_periph = peripheral;
	        
	        found_peripheral = peripheral;
	        peripheral.connect(function (error) {
	            console.log('done\n');

	            // delay before discovering services so that connection
	            //  parameters can be established
	            setTimeout(discover_calibration, 100);
	        });
    	});
    }
});

noble.on('warning', function () {
	console.log("Noble Warning Captured");
});

// print errors if they occur during service/characteristic discovery
function log_discovery_error(desired_char, discovered_list) {
    console.log("Unable to determine correct service/char");
    console.log("Searching for " + desired_char);
    console.log("Service/char List:");
    console.log(discovered_list);
    powerblade_periph.disconnect();
}

// wrapper for discovering a characteristic
function discover_char(service, char_uuid, callback) {
    service.discoverCharacteristics([char_uuid], function(error, chars) {
        if (error) throw error;
        if (chars.length != 1) {
            log_discovery_error(char_uuid, chars);
            return;
        }
        callback(chars[0]);
    });
}

function discover_calibration() {
    if(powerblade_periph['state']  != 'connected') {
    	if(restart_count++ >= 10) {
    		console.log('Restart limit reached, exiting');
    		console.log('\nXXXXXXXXXXXXX Calibration Not Complete! XXXXXXXXXXXXX')
    		process.exit();
    	}
    	process.stdout.write('Connection error, re-trying connection (Attempt #' + restart_count + ')...')
    	found_peripheral.connect(function (error) {
			console.log('done\n');

			// delay before discovering services so that connection
			//  parameters can be established
			setTimeout(discover_calibration, 100);
		});
    }
    else {
    	process.stdout.write("Discovering calibration service... ");
	    powerblade_periph.discoverServices([calibration_service_uuid], function(error, services) {
	        if (error) throw error;
	        if (services.length != 1) {
	            log_discovery_error(calibration_service_uuid, services);
	            return;
	        }
	        var calibration_service = services[0];
	        console.log('done');

	        process.stdout.write('Discovering wattage characteristic... ');
	        discover_char(calibration_service, calibration_wattage_uuid, function(characteristic) {
	            calibration_wattage_char = characteristic;
	            console.log('done');

	            process.stdout.write('Discovering voltage characteristic... ');
	            discover_char(calibration_service, calibration_voltage_uuid, function(characteristic) {
	                calibration_voltage_char = characteristic;
	                console.log('done');

	                process.stdout.write('Discovering control characteristic... ');
	                discover_char(calibration_service, calibration_control_uuid, function(characteristic) {
	                    calibration_control_char = characteristic;
	                    console.log('done\n');

	                    calibration_control_char.on('data', Calibration_status_receive);
	                    calibration_control_char.notify(true);

	                    // only bother discovering config service if we need it
	                    if (read_config) {
	                        discover_config();
	                    } else {
	                        start_calibration();
	                    }
	                });
	            });
	        });
	    });
	}
}

function discover_config() {
    console.log("Discovering configuration service");
    powerblade_periph.discoverServices([config_service_uuid], function(error, services) {
        if (error) throw error;
        if (services.length != 1) {
            log_discovery_error(config_service_uuid, services);
            return;
        }
        var config_service = services[0];

        discover_char(config_service, config_status_uuid, function(characteristic) {
            config_status_char = characteristic;
            config_status_char.on('data', Config_status_receive);
            config_status_char.notify(true);

            discover_char(config_service, config_voff_uuid, function(characteristic) {
                config_voff_char = characteristic;

                discover_char(config_service, config_ioff_uuid, function(characteristic) {
                    config_ioff_char = characteristic;

                    discover_char(config_service, config_curoff_uuid, function(characteristic) {
                        config_curoff_char = characteristic;

                        discover_char(config_service, config_pscale_uuid, function(characteristic) {
                            config_pscale_char = characteristic;

                            discover_char(config_service, config_vscale_uuid, function(characteristic) {
                                config_vscale_char = characteristic;

                                discover_char(config_service, config_whscale_uuid, function(characteristic) {
                                    config_whscale_char = characteristic;
                                    console.log("\tComplete\n");

                                    start_calibration();
                                });
                            });
                        });
                    });
                });
            });
        });
    });
}

function Config_status_receive(data, isNotify) {
    if (!isNotify) {
        console.log("Got a non-notification config status?");
    }
    console.log("Received PowerBlade status code:");
    console.log("\t\t" + data[0]);
}

function start_calibration() {
    // everything is read, start calibration
    console.log("Starting calibration");

    // write wattage value
    var buf = new Buffer([0x00, 0x00]);
    buf.writeInt16BE(wattage*10);
    calibration_wattage_char.write(buf, false, function(error) {
        if (error) throw error;
        
        // write voltage value
        buf.writeInt16BE(voltage*10);
        calibration_voltage_char.write(buf, false, function(error) {
            if (error) throw error;

            // begin calibration
            calibration_control_char.write(new Buffer([0x01]), false, function(error) {
                if (error) throw error;
            });
        });
    });
}

function Calibration_status_receive(data, isNotify) {
    if (!isNotify) {
        console.log("Got a non-notificiation calibration status?");
    }

    // check value
    if (data[0] == 1) {
        process.stdout.write("Calibrating... ");
    } else if (data[0] == 2) {
        console.log("done\n");

        if (read_config) {
            setTimeout(read_calibration, 1200);
        } else {
            complete_calibration();
        }
    } else {
        console.log("Unknown calibration value: " + data[0]);
    }
}

function complete_calibration() {
    // calibration is complete
    //console.log("Calibration Finished!");
    powerblade_periph.disconnect();
    process.exit(0);
}

function read_calibration() {
    console.log("Reading calibration values from PowerBlade...");
    config_voff_char.read(function(error, data) {
        if (error) throw error;
        console.log("Voff= " + data.readInt8() + ' (' + data.toString('hex') + ')');

        config_ioff_char.read(function(error, data) {
            if (error) throw error;
            console.log("Ioff= " + data.readInt8() + ' (' + data.toString('hex') + ')');

            config_curoff_char.read(function(error, data) {
                if (error) throw error;
                console.log("Curoff= " + data.readInt8() + ' (' + data.toString('hex') + ')');

                config_pscale_char.read(function(error, data) {
                    if (error) throw error;
                    console.log("PScale= " + data.readUInt16LE() + ' (' + data.toString('hex') + ')');

                    config_vscale_char.read(function(error, data) {
                        if (error) throw error;
                        console.log("VScale= " + data.readUInt8() + ' (' + data.toString('hex') + ')');

                        config_whscale_char.read(function(error, data) {
                            if (error) throw error;
                            console.log("WHScale= " + data.readUInt8() + ' (' + data.toString('hex') + ')');

                            // writing complete
                            console.log("\tComplete\n");

                            // calibration is complete
                            complete_calibration();
                        });
                    });
                });
            });
        });
    });
}


//}

