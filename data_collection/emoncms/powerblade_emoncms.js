#!/usr/bin/env node

var noble = require('noble');
var request = require('request');

var UMICH_COMPANY_ID = 0x02E0;
var POWERBLADE_SERVICE_ID = 0x11;
var OLD_COMPANY_ID = 0x4908;

var INPUT_URL = 'http://inductor.eecs.umich.edu/input/post.json';
var APIKEY = 'none';

if (process.argv.length == 3) {
    APIKEY = process.argv[2];
} else {
    console.log('Must include emoncms APIKEY as first argument.');
    process.exit(1);
}


// {BLE Address: Most recent sequence number} for each PowerBlade
var powerblade_sequences = {};

noble.on('stateChange', function(state) {
    if (state === 'poweredOn') {
        console.log("Starting scan...");
        noble.startScanning([], true);
    } else {
        console.log('Scanning error: ' + state);
        noble.stopScanning();
    }
});

noble.on('error', function (err) {
    console.log(err);
})

noble.on('discover', function (peripheral) {

    // Advertisement found. Check if it is a PowerBlade
    //  PowerBlade data advertisements:
    //      Have a Manufacturer Specific Data section
    //      Have a Company Identifier of 0x02E0 (assigned to the University of Michigan, first two bytes of data)
    //      Have a service id of 0x11 (assigned to PowerBlade [internally], third byte of data)
    var advertisement = peripheral.advertisement;
    var company_id = 0;
    var service_id = 0;
    if (advertisement.manufacturerData !== undefined && advertisement.manufacturerData
            && advertisement.manufacturerData.length >= 3) {
        company_id = advertisement.manufacturerData.readUIntLE(0,2);
        service_id = advertisement.manufacturerData.readUInt8(2);
    }

    if ((company_id == UMICH_COMPANY_ID && service_id == POWERBLADE_SERVICE_ID) ||
            company_id == OLD_COMPANY_ID) {
        // Found a PowerBlade
        var address  = peripheral.address;
        var data = advertisement.manufacturerData.slice(3);
        if (company_id == OLD_COMPANY_ID) {
            data = advertisement.manufacturerData.slice(2);
        }
        var recv_time = (new Date).getTime()/1000;

        // check length of data
        if (data.length < 19) {
            console.log("ERROR: Bad PowerBlade packet");
            return;
        }

        // check software version number
        var version_num = data.readUIntBE(0,1);
        if (version_num == 1) {

            // check for duplicate advertisements
            var sequence_num = data.readUIntBE(1,4);
            if (!(address in powerblade_sequences)) {
                powerblade_sequences[address] = -1;
            }
            if (powerblade_sequences[address] == sequence_num) {
                // duplicate advertisement. Don't display
                return;
            }
            powerblade_sequences[address] = sequence_num;

            // parse fields from advertisement
            var pscale             = data.readUIntBE(5,2);
            var vscale             = data.readUIntBE(7,1);
            var whscale            = data.readUIntBE(8,1);
            var v_rms_raw          = data.readUIntBE(9,1);
            var real_power_raw     = data.readUIntBE(10,2);
            var apparent_power_raw = data.readUIntBE(12,2);
            var watt_hours_raw     = data.readUIntBE(14,4);
            var flags              = data.readUIntBE(18,1);

            // calculate scaling values
            var volt_scale  = vscale / 50;
            var power_scale = (pscale & 0x0FFF) * Math.pow(10,-1*((pscale & 0xF000) >> 12));
            var wh_shift    = whscale;

            // scale measurements from PowerBlade
            var v_rms      = v_rms_raw*volt_scale;
            var real_power = real_power_raw*power_scale;
            var app_power  = apparent_power_raw*power_scale;
            if (volt_scale > 0) {
              var watt_hours = (watt_hours_raw << wh_shift)*(power_scale/3600);
            } else {
              var watt_hours = watt_hours_raw;
            }
            var pf = real_power / app_power;

            // Display data for logging purposes
            console.log(new Date() +
                ' PowerBlade[' + address +'] #' +
                sequence_num + ' ' +
                v_rms.toFixed(2)+'V '  + 
                 real_power.toFixed(2) + 'W ' +
                 app_power.toFixed(2) + 'VA ' +
                watt_hours.toFixed(2) + 'Wh ' +
                pf.toFixed(2));

            // Generate the object we send to emoncms
            var post_data = {
                seq:              sequence_num,
                voltage_rms:      v_rms.toFixed(1),
                power_w:          real_power.toFixed(1),
                apparent_power_w: app_power.toFixed(1),
                energy_kwh:       watt_hours.toFixed(1),
                pf:               pf.toFixed(1)
            };

            // Check if we have an address to identify this PowerBlade
            if (address != 'unknown') {
                // Send to emoncms
                var url = INPUT_URL + '?node=' + address + '&json=' + JSON.stringify(post_data) + '&apikey=' + APIKEY;
                var p = request.post(url);
                p.on('error', function (err) {
                    console.log('Error when posting to emoncms: ' + err);
                });
            } else {
                console.log('ERROR - could not send to emoncms because address is unknown.');
            }

        } else {
            // This version of PowerBlade is not supported by this script
            console.log('ERROR: PowerBlade version ' + version_num + ' unsupported.');
        }
        
    }
});

