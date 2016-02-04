#!/usr/bin/env node

// imports
var noble = require('noble');
var fs = require('fs');
var calib = require('./lib/calibrate_samples');

// input from user
var target_device = 'c0:98:e5:70:45:36';
if (process.argv.length >= 3) {
    target_device = process.argv[2];
}
var wattage = 200;
if (process.argv.length >= 4) {
    wattage = process.argv[3];
}
console.log("Looking for " + target_device);
console.log("Calibrating at " + wattage + " W");

// reference to discovered peripheral
var powerblade_periph;

// raw sample collection service
var rawSample_service_uuid = 'cead01af7cf8cc8c1c4e882a39d41531';
var rawSample_start_uuid   = 'cead01b07cf8cc8c1c4e882a39d41531';
var rawSample_data_uuid    = 'cead01b17cf8cc8c1c4e882a39d41531';
var rawSample_status_uuid  = 'cead01b27cf8cc8c1c4e882a39d41531';
var rawSample_start_char;
var rawSample_data_char;
var rawSample_status_char;
var sampleData = new Buffer(0);

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
var calibration_values = {};

// start BLE scanning
noble.on('stateChange', function(state) {
    if (state === 'poweredOn') {
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
noble.on('discover', function (peripheral) {
    //console.log(peripheral.address);
    if (peripheral.address == target_device) {
        noble.stopScanning();

        console.log('Found PowerBlade (' + peripheral.address +')\n');
        console.log('Connecting...');
        powerblade_periph = peripheral;
        
        peripheral.connect(function (error) {
            console.log('\tConnected\n');

            // delay before discovering services so that connection
            //  parameters can be established
            //XXX: check on a power trace that this is fine
            setTimeout(discover_rawSample, 1000);
        });
    }
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

function discover_rawSample() {
    console.log("Discovering raw sample service");
    powerblade_periph.discoverServices([rawSample_service_uuid], function(error, services) {
        if (error) throw error;
        if (services.length != 1) {
            log_discovery_error(rawSample_service_uuid, services);
            return;
        }
        var rawSample_service = services[0];

        discover_char(rawSample_service, rawSample_start_uuid, function(characteristic) {
            rawSample_start_char = characteristic;

            discover_char(rawSample_service, rawSample_data_uuid, function(characteristic) {
                rawSample_data_char = characteristic;
                rawSample_data_char.on('read', RawSample_data_receive);

                discover_char(rawSample_service, rawSample_status_uuid, function(characteristic) {
                    rawSample_status_char = characteristic;
                    rawSample_status_char.on('data', RawSample_status_receive);
                    rawSample_status_char.notify(true);
                    console.log("\tComplete\n");

                    discover_config();
                });
            });
        });
    });
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

                                    // delay before starting to let power catch up
                                    start_collection();
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

function start_collection() {
    // everything is ready, start raw sample collection
    console.log("Starting raw sample collection");
    rawSample_start_char.write(new Buffer([0x01]));
}

var data_chunk_number = 1;
function RawSample_status_receive(data, isNotify) {

    // check value for next state
    if (data[0] == 1) {
        console.log("New data available (" + data_chunk_number + ")");
        data_chunk_number++;
        //XXX: check on a power trace that this is fine
        read_data();
    } else if (data[0] == 2) {
        console.log("All data has been read\n");

        // calculate calibration numbers
        console.log("Calculating calibration numbers...")
        calibration_values = calib.calculate_constants(wattage, sampleData);

        // write the calculated calibration values back to the powerblade
        write_calibration();
    }
}

function read_data() {
    // next data is available, read characteristic
    console.log("\tReading...");
    rawSample_data_char.read();
}

var output_file_no = 0;
function RawSample_data_receive(data) {
    // do something with the data
    console.log("\tComplete\n");

    //XXX: adjust this to grab sequence number as first byte

    // save data to files in case we want to manually review it
    fs.writeFile('data/rawSamples_num' + output_file_no + '.bin', data);
    output_file_no += 1;

    // also save data to a buffer so we can run through it programmatically
    sampleData = Buffer.concat([sampleData, data]);

    // write status to request next data
    console.log("Requesting next data");
    rawSample_status_char.write(new Buffer([0x01]));
}

function write_calibration() {
    console.log("Writing calibration values to PowerBlade...");
    config_voff_char.write(calibration_values['voff'], false, function(error) {
        if (error) throw error;

        config_ioff_char.write(calibration_values['ioff'], false, function(error) {
            if (error) throw error;

            config_curoff_char.write(calibration_values['curoff'], false, function(error) {
                if (error) throw error;

                config_pscale_char.write(calibration_values['pscale'], false, function(error) {
                    if (error) throw error;

                    config_vscale_char.write(calibration_values['vscale'], false, function(error) {
                        if (error) throw error;

                        config_whscale_char.write(calibration_values['whscale'], false, function(error) {
                            if (error) throw error;

                            // writing complete
                            console.log("\tComplete\n");

                            // calibration is complete
                            console.log("Calibration Finished!");
                            calibration_values = powerblade_periph.disconnect();
                            process.exit(0);
                        });
                    });
                });
            });
        });
    });
}

