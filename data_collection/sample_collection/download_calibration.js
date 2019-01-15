#!/usr/bin/env node

// imports
var noble = require('noble');
var fs = require('fs');

// input from user
var target_device = 'c0:98:e5:70:02:6a';
if (process.argv.length >= 3) {
    target_device = process.argv[2];
} else {
    console.log("Need to specify a device address. For example:\n\tsudo ./download_calibration.js c0:98:e5:70:02:6a");
    process.exit(1);
}
console.log("Looking for " + target_device);

var read_config = true;

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
noble.on('stateChange', function(state) {
    if (noble.state === 'poweredOn') {
        console.log("Starting scan...\n");
        noble.startScanning([], true);
    } else {
        noble.stopScanning();
    }
});

// exit when disconnected
noble.on('disconnect', function () {
    console.log('Disconnected');
    process.exit(0);
});

// find correct device and connect to it
var restart_count = 0;
var found_peripheral;
noble.on('discover', function (peripheral) {

    // print the address of each BLE peripheral
    //console.log('ADV: ' + peripheral.address);

    // found it!
    if (peripheral.address == target_device) {
        noble.stopScanning( function() {
	        console.log('Found PowerBlade (' + peripheral.address +')');
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
        if (error) {
            throw error;
        }
        if (chars.length != 1) {
            log_discovery_error(char_uuid, chars);
            return;
        }
        callback(chars[0]);
    });
}

function discover_calibration() {
    if (powerblade_periph['state']  != 'connected') {
        if (restart_count++ >= 10) {
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
    } else {
        console.log("Discovering services. This takes about 10 seconds.");
        process.stdout.write("Discovering calibration service... ");
        powerblade_periph.discoverServices([calibration_service_uuid], function(error, services) {
            if (error) {
                throw error;
            }
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
                        console.log('done');

                        //calibration_control_char.on('data', Calibration_status_receive);
                        calibration_control_char.notify(true);

                        // discover config service
                        discover_config();
                    });
                });
            });
        });
    }
}

function discover_config() {
    process.stdout.write('Discovering configuration service... ');
    powerblade_periph.discoverServices([config_service_uuid], function(error, services) {
        if (error) {
            throw error;
        }
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
                                    console.log("done\n");

                                    read_calibration();
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

function complete_calibration() {
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
                            console.log("Complete\n");

                            // calibration is complete
                            complete_calibration();
                        });
                    });
                });
            });
        });
    });
}


