#!/usr/bin/env node

var noble = require('noble');
var fs = require('fs');

// characteristic UUIDs
var rawSample_service_uuid = 'cead01af7cf8cc8c1c4e882a39d41531';
var rawSample_start_uuid   = 'cead01b07cf8cc8c1c4e882a39d41531';
var rawSample_data_uuid    = 'cead01b17cf8cc8c1c4e882a39d41531';
var rawSample_status_uuid  = 'cead01b27cf8cc8c1c4e882a39d41531';

var target_device = 'c0:98:e5:70:45:36';
if (process.argv.length >= 3) {
    target_device = process.argv[2];
}
console.log("Looking for " + target_device);

noble.on('stateChange', function(state) {
    if (state === 'poweredOn') {
        console.log("Starting scan...");
        noble.startScanning([], true);
    } else {
        noble.stopScanning();
    }
});

var powerblade_periph;
var rawSample_start_char;
var rawSample_data_char;
var rawSample_status_char;

noble.on('discover', function (peripheral) {
    //console.log(peripheral.address);
    if (peripheral.address == target_device) {
        noble.stopScanning();

        console.log('Found PowerBlade (' + peripheral.address +')');
        console.log('Connecting...');
        powerblade_periph = peripheral;
        
        peripheral.connect(function (error) {
            console.log('Connected');

            // delay before discovering services so that connection
            //  parameters can be established
            console.log("Delaying for power");
            setTimeout(discover_services, 5000);
        });
    }
});

function discover_services() {
    powerblade_periph.discoverServices([rawSample_service_uuid], function(error, services) {
        if (error) throw error;
        if (services.length != 1) {
            console.log("Unable to determine correct service");
            console.log("Service List:");
            console.log(services);
            powerblade_periph.disconnect();
        }
        console.log("Found service");
        var rawSample_service = services[0];

        rawSample_service.discoverCharacteristics([rawSample_start_uuid], function(error, chars) {
            if (error) throw error;
            if (services.length != 1) {
                console.log("Unable to determine correct characteristic");
                console.log("Characteristic List:");
                console.log(chars);
                powerblade_periph.disconnect();
            }
            console.log("Found start char");
            rawSample_start_char = chars[0];

            rawSample_service.discoverCharacteristics([rawSample_data_uuid], function(error, chars) {
                if (error) throw error;
                if (services.length != 1) {
                    console.log("Unable to determine correct characteristic");
                    console.log("Characteristic List:");
                    console.log(chars);
                    powerblade_periph.disconnect();
                }
                console.log("Found data char");
                rawSample_data_char = chars[0];
                rawSample_data_char.on('read', RawSample_data_receive);
                rawSample_service.discoverCharacteristics([rawSample_status_uuid], function(error, chars) {
                    if (error) throw error;
                    if (services.length != 1) {
                        console.log("Unable to determine correct characteristic");
                        console.log("Characteristic List:");
                        console.log(chars);
                        powerblade_periph.disconnect();
                    }
                    console.log("Found status char");
                    rawSample_status_char = chars[0];
                    rawSample_status_char.on('data', RawSample_status_receive);
                    rawSample_status_char.notify(true);

                    // delay before starting to let power catch up
                    //console.log("Delaying for power");
                    //setTimeout(start_collection, 5000);
                    start_collection();
                });
            });
        });
    });
}

function start_collection() {
    // everything is ready, start raw sample collection
    console.log("Starting raw sample collection");
    rawSample_start_char.write(new Buffer([0x01]));
}

function RawSample_status_receive(data, isNotify) {
    console.log("Status value received:");
    console.log(data[0]);
    console.log("Is notification?: " + isNotify);

    // check value for next state
    if (data[0] == 1) {
        setTimeout(read_data, 1000);
    } else if (data[0] == 2) {
        // finish up and exit if all data is read
        console.log("Finished! Disconnecting...");
        powerblade_periph.disconnect();
    }
}

function read_data() {
    // next data is available, read characteristic
    console.log("New data available. Reading...");
    rawSample_data_char.read();
}

var output_file_no = 0;

function RawSample_data_receive(data) {
    console.log("Data value received:");
    console.log(data);
    // do something with the data
    fs.writeFile('rawSamples_num' + output_file_no + '.bin', data);
    output_file_no += 1;

    // write status to request next data
    console.log("Requesting next data");
    rawSample_status_char.write(new Buffer([0x01]));
}

noble.on('disconnect', function () {
    console.log('Disconnected');
    process.exit(0);
});

