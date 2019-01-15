#!/usr/bin/env node

// imports
var noble = require('noble');
var fs = require('fs');

// input from user
var target_device = 'c0:98:e5:70:45:36';
if (process.argv.length >= 3) {
    target_device = process.argv[2];
} else {
    console.log("Need to specify a device address. For example:\n\tsudo ./collect_samples.js c0:98:e5:70:02:6a");
    process.exit(1);
}
console.log("Looking for " + target_device);

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
    // print the address of each BLE peripheral
    //console.log('ADV: ' + peripheral.address);

    // found it!
    if (peripheral.address == target_device) {
        noble.stopScanning( function() {
	        console.log('Found PowerBlade (' + peripheral.address +')');
	        process.stdout.write('Connecting... ');
	        powerblade_periph = peripheral;
	        
	        peripheral.connect(function (error) {
	            console.log('done\n');

	            // delay before discovering services so that connection
	            //  parameters can be established
                setTimeout(discover_rawSample, 100);
	        });
    	});
    }
});

// print when warnings occur
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

function discover_rawSample() {
    console.log("Discovering services. This takes about 10 seconds.");
    process.stdout.write("  Discovering raw sample service... ");
    powerblade_periph.discoverServices([rawSample_service_uuid], function(error, services) {
        if (error) {
            throw error;
        }
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
                    console.log("done");

                    discover_config();
                });
            });
        });
    });
}

function discover_config() {
    process.stdout.write('  Discovering configuration service... ');
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

function read_calibration() {
    console.log("Reading calibration values from PowerBlade...");
    config_voff_char.read(function(error, data) {
        if (error) throw error;
        calibration_values['voff'] = data.readInt8();
        console.log("  Voff= " + data.readInt8() + ' (' + data.toString('hex') + ')');

        config_ioff_char.read(function(error, data) {
            if (error) throw error;
            calibration_values['ioff'] = data.readInt8();
            console.log("  Ioff= " + data.readInt8() + ' (' + data.toString('hex') + ')');

            config_curoff_char.read(function(error, data) {
                if (error) throw error;
                calibration_values['curoff'] = data.readInt8();
                console.log("  Curoff= " + data.readInt8() + ' (' + data.toString('hex') + ')');

                config_pscale_char.read(function(error, data) {
                    if (error) throw error;
                    calibration_values['pscale'] = data.readUInt16LE();
                    console.log("  PScale= " + data.readUInt16LE() + ' (' + data.toString('hex') + ')');

                    config_vscale_char.read(function(error, data) {
                        if (error) throw error;
                        calibration_values['vscale'] = data.readUInt8();
                        console.log("  VScale= " + data.readUInt8() + ' (' + data.toString('hex') + ')');

                        config_whscale_char.read(function(error, data) {
                            if (error) throw error;
                            calibration_values['whscale'] = data.readUInt8();
                            console.log("  WHScale= " + data.readUInt8() + ' (' + data.toString('hex') + ')');

                            console.log("Complete\n");
                            start_collection();
                        });
                    });
                });
            });
        });
    });
}

function start_collection() {
    // everything is ready, start raw sample collection
    console.log("Starting raw sample collection. This takes about 30 seconds and reads 10 times.");
    rawSample_start_char.write(new Buffer([0x01]));
}

var data_chunk_number = 1;
function RawSample_status_receive(data, isNotify) {

    // check value for next state
    if (data[0] == 1) {
        console.log("  New data available (" + data_chunk_number + ")");
        data_chunk_number++;
        read_data();
    } else if (data[0] == 2) {
        console.log("  All data has been read\nComplete\n");

        // apply calibration values to data and save results
        console.log("Applying calibration and saving results in 'data/'");
        adjust_and_save(calibration_values, sampleData);

        // finished
        console.log("Complete");
        powerblade_periph.disconnect();
        process.exit(0);
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
    console.log("\tComplete");

    // save data to files in case we want to manually review it
    fs.writeFileSync('data/rawSamples_num' + output_file_no + '.bin', data);
    output_file_no += 1;

    // also save data to a buffer so we can run through it programmatically
    sampleData = Buffer.concat([sampleData, data]);

    // write status to request next data
    console.log("  Requesting next data");
    rawSample_status_char.write(new Buffer([0x01]), false, function(error) {
        if (error) throw error;
        console.log("\tWrite Complete");
    });
}

function adjust_and_save(calibration_values, dataArr) {

    // split data array into current and voltage samples
    var dataLen = dataArr.length / 4;
    var dataBuf = new Buffer(dataArr);
    var voltageArr = [];
    var currentArr = [];
    var voltageIndex = 0;
    var currentIndex = 2;
    for(var i = 0; i < dataLen; i++) {
        voltageArr.push(dataBuf.readInt16BE(4*i + voltageIndex));
        currentArr.push(dataBuf.readInt16BE(4*i + currentIndex));
    }

    // calibration values for the powerblade
    var voff = calibration_values['voff'];
    var ioff = calibration_values['ioff'];
    var curoff = calibration_values['curoff'];
    var pscale = calibration_values['pscale'];
    var vscale = calibration_values['vscale'];

    // set calibration values per powerblade specification
    pscale = (pscale & 0xFFF) * Math.pow(10,-1*((pscale & 0xF000) >> 12));
    vscale = vscale / 200;

    // integrate current values, also write raw samples to file while iterating them
    var integrate = [];
    var aggCurrent = 0;
    fs.writeFileSync('data/rawSamples.dat', '# Count\tVoltage\tCurrent\tInt\n');
    for(var i = 0; i < dataLen; i++) {
        var newCurrent = currentArr[i] - ioff;
        aggCurrent += (newCurrent + (newCurrent >> 1));
        aggCurrent -= aggCurrent >> 5;
        integrate[i] = (aggCurrent >> 3);

        fs.appendFileSync('data/rawSamples.dat', i + '\t' + voltageArr[i] + '\t' + currentArr[i] + '\t' + integrate[i] + '\n');
    }

    // write adjusted results to file
    fs.writeFileSync('data/realSamples.dat', '# Count\tVoltage\tCurrent\n');
    for (var i=0; i < dataLen; i++) {
        var real_voltage = vscale*(voltageArr[i] - voff);
        var real_integrate = (pscale/vscale)*(integrate[i] - curoff);

        fs.appendFileSync('data/realSamples.dat', i + '\t' + real_voltage + '\t' + real_integrate + '\n');
    }
}

