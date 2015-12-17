#!/usr/bin/env node

var noble = require('noble');

// characteristic UUIDs
var rawSample_service_uuid = 'cead2a887cf8cc8c1c4e882a39d41531';
var rawSample_start_uuid   = 'cead2a897cf8cc8c1c4e882a39d41531';
var rawSample_data_uuid    = 'cead2a8a7cf8cc8c1c4e882a39d41531';
var rawSample_status_uuid  = 'cead2a8b7cf8cc8c1c4e882a39d41531';

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

noble.on('discover', function (peripheral) {
    //console.log(peripheral.address);
    if (peripheral.address == target_device) {
        noble.stopScanning();

        console.log('Found PowerBlade (' + peripheral.address +')');
        console.log('Connecting...');
        
        peripheral.connect(function (error) {
            console.log('Connected');

            peripheral.discoverServices([rawSample_service_uuid], function(error, services) {
                if (error) throw error;
                if (services.length != 1) {
                    console.log("Unable to determine correct service");
                    console.log("Service List:");
                    console.log(services);
                    peripheral.disconnect();
                }
                var rawSample_service = services[0];

                rawSample_service.discoverCharacteristics([rawSample_start_uuid], function(error, chars) {
                    if (error) throw error;
                    if (services.length != 1) {
                        console.log("Unable to determine correct characteristic");
                        console.log("Characteristic List:");
                        console.log(chars);
                        peripheral.disconnect();
                    }
                    var rawSample_start_char = chars[0];

                    rawSample_service.discoverCharacteristics([rawSample_data_uuid], function(error, chars) {
                        if (error) throw error;
                        if (services.length != 1) {
                            console.log("Unable to determine correct characteristic");
                            console.log("Characteristic List:");
                            console.log(chars);
                            peripheral.disconnect();
                        }
                        var rawSample_data_char = chars[0];
                        rawSample_data_char.on('read', RawSample_data_receive);
                        rawSample_service.discoverCharacteristics([rawSample_status_uuid], function(error, chars) {
                            if (error) throw error;
                            if (services.length != 1) {
                                console.log("Unable to determine correct characteristic");
                                console.log("Characteristic List:");
                                console.log(chars);
                                peripheral.disconnect();
                            }
                            var rawSample_status_char = chars[0];
                            rawSample_status_char.on('data', RawSample_status_receive);
                            rawSample_status_char.notify(true);

                            // everything is ready, start raw sample collection
                            console.log("Starting raw sample collection");
                            rawSample_start_char.write(new Buffer([0x01]));
                        });
                    });
                });
            });
        });
    }
});


function RawSample_status_receive(data, isNotify) {
    console.log("Status value received:");
    console.log(data[0]);
    console.log("Is notification?: " + isNotify);

    // check value for next state

        // read data characteristic if next data is available

        // finish up and exit if all data is read
}

function RawSample_data_receive(data) {
    console.log("Data value received:");
    console.log(data);
    // do something with the data

    // write status to request next data
}

noble.on('disconnect', function () {
    console.log('Disconnected');
    process.exit(0);
});

