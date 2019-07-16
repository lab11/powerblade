#!/usr/bin/env node

// imports
var noble = require('noble');
var fs = require('fs');
var keypress = require('keypress');
var rimraf = require('rimraf');
var args = require('command-line-args');
const child_process = require('child_process');

const optionsDef = [
    { name: 'device', type: String, multiple: false, defaultOption: true },
    { name: 'save', alias: 's', type: Boolean },
    { name: 'unique', alias: 'u', type: Boolean }
]

const options = args(optionsDef);

// input from user
var target_device = 'c0:98:e5:70:02:6a';
if ('device' in options) {
    target_device = options['device'];
} else {
    console.log("Need to specify a device address. For example:\n\tsudo ./visualize_waveforms.js c0:98:e5:70:02:6a");
    process.exit(1);
}
console.log("Looking for " + target_device);

var store_data = false;
if ('store' in options) {
    store_data = options['store'];
    if (store_data) {
        console.log("Waveform data will be saved in `data\\`");
        rimraf.sync('./data/waveform_*.bin');
    }
}

// reference to discovered peripheral
var powerblade_periph;

// waveform collection service
var waveform_service_uuid = '6171e3f16cda409b931ca83234603b33';
var waveform_status_uuid  = '6171e3f26cda409b931ca83234603b33';
var waveform_data_uuid    = '6171e3f36cda409b931ca83234603b33';
if ('unique' in options && options['unique']) {
    waveform_service_uuid = '4e889b3ddab242c3901541b5391326dd';
    waveform_status_uuid  = '4e889b3edab242c3901541b5391326dd';
    waveform_data_uuid    = '4e889b3fdab242c3901541b5391326dd';
}
var waveform_status_char;
var waveform_data_char;

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

// plotting service
var plotter = child_process.spawn('python3', ['-u', 'plotter.py']);
plotter.stdout.on('data', (data) => {
    console.log('Plotter: ' + data);
});
plotter.on('close', (code) => {
    console.log('Plotter exited with code ' + code);
});

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
                    setTimeout(discover_waveform_service, 100);
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

function discover_waveform_service() {
    console.log("Discovering services. This takes about 10 seconds.");
    process.stdout.write("  Discovering waveform service... ");
    powerblade_periph.discoverServices([waveform_service_uuid], function(error, services) {
        if (error) {
            throw error;
        }
        if (services.length != 1) {
            log_discovery_error(waveform_service_uuid, services);
            return;
        }
        var waveform_service = services[0];

        discover_char(waveform_service, waveform_status_uuid, function(characteristic) {
            waveform_status_char = characteristic;
            waveform_status_char.on('data', waveform_status_receive);
            waveform_status_char.notify(true);

            discover_char(waveform_service, waveform_data_uuid, function(characteristic) {
                waveform_data_char = characteristic;
                waveform_data_char.on('read', waveform_data_receive);
                console.log("done");

                discover_config_service();
            });
        });
    });
}

function discover_config_service() {
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

                            // wait for user keypress
                            console.log("Press any key to start waveform visualization...\n");
                            keypress(process.stdin)
                            process.stdin.on('keypress', function (ch, key) {
                                if (key) {
                                    if (key.ctrl && key.name =='c') {
                                        console.log("Killing...\n");
                                        powerblade_periph.disconnect();
                                        process.exit(0);
                                    } else {
                                        start_collection();
                                    }
                                }
                            });
                            process.stdin.setRawMode(true);
                            process.stdin.resume();
                        });
                    });
                });
            });
        });
    });
}

function start_collection() {
    // everything is ready, start raw sample collection
    console.log("Starting waveform visualization.\n");
    waveform_status_char.write(new Buffer([0xFF]));
}

function waveform_status_receive(data, isNotify) {

    // check value for next state
    if (data[0] == 1) {
        console.log("  New data available");
        read_data();
    } else if (data[0] == 0) {
        console.log("  All data has been read\nPress any key to exit\n");
        keypress(process.stdin)
        process.stdin.on('keypress', function (ch, key) {
            // finished
            console.log("Complete");
            powerblade_periph.disconnect();
            process.exit(0);

        });
    }
}

function read_data() {
    // next data is available, read characteristic
    console.log("\tReading...");
    waveform_data_char.read();
}

var output_file_no = 0;
function waveform_data_receive(data) {
    console.log("\tComplete");
    console.log(data.length);

    // send data to python
    // slice off adv data + length info
    plotter.stdin.write(data.slice(24 + 2 + 2).toString('hex') + '\n');

    // save data if desired
    if (store_data) {
        console.log("\tSaving data file waveform_" + output_file_no + ".bin");

        // save data to files in case we want to manually review it
        fs.writeFileSync('data/waveform_' + output_file_no + '.bin', data);
        output_file_no += 1;
    }

    // write status to request next data
    console.log("  Requesting next data");
    waveform_status_char.write(new Buffer([0xFF]), false, function(error) {
        if (error) throw error;
        console.log("\tWrite Complete");
    });
}

function visualize_data(data) {
    //
    var voltageArr = [];
    var currentArr = [];
}

