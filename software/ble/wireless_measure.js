#!/usr/bin/env node
var async = require('async');
var noble = require('noble');
var BitArray = require('node-bitarray');

// mangled version of 0x4908
var CompanyID = 37392;

var ble_devices = [];
var device_count = 0;
var powerblades = {};
var TIME_WINDOW = 10;

console.log('Looking for PowerBlades!');

noble.on('stateChange', function(state) {
    if (state === 'poweredOn') {
        console.log("Starting scan...");
        noble.startScanning([], true);
    } else {
        noble.stopScanning();
    }
});

noble.on('discover', function(peripheral) {

    // device found!
    var peripheral_uuid = peripheral.uuid;
    if (ble_devices.indexOf(peripheral_uuid) == -1) {
        device_count += 1;
        ble_devices += peripheral_uuid;
    }

    // check if device is actually a PowerBlade
    if (peripheral_uuid in powerblades) {
        // existing powerblade
        var curr_time = Date.now()/1000
        powerblades[peripheral_uuid]['total_times'].push(curr_time)
        var data = peripheral.advertisement.manufacturerData.slice(2);
        var sequence_num = BitArray.fromBuffer(data.slice(1,5)).toNumber();
        if (powerblades[peripheral_uuid]['sequence_num'] != sequence_num) {
            powerblades[peripheral_uuid]['unique_times'].push(curr_time);
            powerblades[peripheral_uuid]['sequence_num'] = sequence_num;
        }
    } else {
        var advertisement = peripheral.advertisement;
        if (typeof advertisement.manufacturerData !== undefined && advertisement.manufacturerData) {
            var manufacturer_id = BitArray.fromBuffer(advertisement.manufacturerData.slice(0,2)).toNumber();
            if (manufacturer_id == CompanyID) {
                // new powerblade!
                var curr_time = Date.now()/1000
                powerblades[peripheral_uuid] = {
                    'start_time': curr_time,
                    'total_times': [curr_time],
                    'unique_times': [curr_time],
                    'sequence_num': -1,
                    };
            }
        }
    }

    // print data to user
    console.log("Total Devices: " + device_count);
    console.log("\t\tUnique per Second\tTotal per second\tWindow Good?");
    for (var id in powerblades) {
        // remove old samples
        var curr_time = Date.now()/1000;
        var new_total_times = powerblades[id]['total_times'].filter(function(x) {
            return x > (curr_time - TIME_WINDOW);
        });
        powerblades[id]['total_times'] = new_total_times;
        var new_unique_times = powerblades[id]['unique_times'].filter(function(x) {
            return x > (curr_time - TIME_WINDOW);
        });
        powerblades[id]['unique_times'] = new_unique_times;

        // print data
        var unique_per_second = powerblades[id]['unique_times'].length/TIME_WINDOW;
        var total_per_second = powerblades[id]['total_times'].length/TIME_WINDOW;
        var good = ((curr_time - powerblades[id]['start_time']) > TIME_WINDOW);
        console.log(id + ":\t" + unique_per_second + '\t\t\t' + total_per_second + '\t\t\t' + good);
    }
    console.log('\n\n\n');
});

