#!/usr/bin/env node
// original file: https://github.com/lab11/powerblade/tree/master/data_collection/advertisements

var noble = require('noble');
var config = require('./config');
var influx;

function getDateTime() {

    var date = new Date();

    var hour = date.getHours();
    hour = (hour < 10 ? "0" : "") + hour;

    var min  = date.getMinutes();
    min = (min < 10 ? "0" : "") + min;

    var sec  = date.getSeconds();
    sec = (sec < 10 ? "0" : "") + sec;

    var year = date.getFullYear();

    var month = date.getMonth() + 1;
    month = (month < 10 ? "0" : "") + month;

    var day  = date.getDate();
    day = (day < 10 ? "0" : "") + day;

    return year + ":" + month + ":" + day + ":" + hour + ":" + min + ":" + sec;

}

if (config.connect_to_influx == true) {
    const Influx = require('influx');
    influx = new Influx.InfluxDB({
     host: config.influx.host,
     port: config.influx.port,
     database: config.influx.db,
     username: config.influx.username,
     password: config.influx.password,
     schema: [
       {
         measurement: config.influx.measurement,
         fields: {
           Powerblade_P: Influx.FieldType.FLOAT,
           Powerblade_E: Influx.FieldType.FLOAT,
           scaling_factor: Influx.FieldType.FLOAT
         },
         tags: [
           'device',
           'unit'
         ]
       }
     ]
    })
}

var dedup = true;
if (process.argv.length >= 3 && process.argv[2] == "--all") {
    dedup = false;
}

var singleSource = false;
var pb_address;
if (process.argv.length >= 4 && process.argv[2] == "--addr") {
    singleSource = true;
    pb_address = process.argv[3];
    console.log("Looking for device " + pb_address);
}

var UMICH_COMPANY_ID = 0x02E0;
var POWERBLADE_SERVICE_ID = 0x11;
var OLD_COMPANY_ID = 0x4908;

// {BLE Address: Most recent sequence number} for each PowerBlade
var powerblade_sequences = {};

var encoding = 'utf8';
const fs = require('fs');
var stream = fs.createWriteStream("powerblade_data.txt", {encoding:encoding,flags:'w'});
stream.write("received_time,rms_voltage,power,apparent_power,energy,power_factor\n");
stream.end();
var stream = fs.createWriteStream("powerblade_data.txt", {encoding:encoding,flags:'a'});

noble.on('stateChange', function(state) {
    if (state === 'poweredOn') {
        console.log("Starting scan...");
        noble.startScanning([], true);
    } else {
	console.log('BLE Antenna state currently', state);
	console.log( 'Waiting for device to Power on.');
        noble.stopScanning();
    }
});

noble.on('discover', function (peripheral) {

    // Advertisement found. Check if it is a PowerBlade
    //  PowerBlade data advertisements:
    //      Have a Manufacturer Specific Data section
    //      Have a Company Identifier of 0x02E0 (assigned to the University of Michigan, first two bytes of data)
    //      Have a service id of 0x11 (assigned to PowerBlade [internally], third byte of data)
    var advertisement = peripheral.advertisement;
    var company_id = 0;
    var service_id = 0;
    const fs = require('fs');
    if (advertisement.manufacturerData !== undefined && advertisement.manufacturerData
            && advertisement.manufacturerData.length >= 3) {
        company_id = advertisement.manufacturerData.readUIntLE(0,2);
        service_id = advertisement.manufacturerData.readUInt8(2);
    }

    // also accept the old company ID of 4908 (no service ID) for compatibility
    if ((company_id == UMICH_COMPANY_ID && service_id == POWERBLADE_SERVICE_ID) ||
            company_id == OLD_COMPANY_ID) {
        // Found a PowerBlade
        var address  = peripheral.address;
        var data = advertisement.manufacturerData.slice(3);
        if (company_id == OLD_COMPANY_ID) {
            data = advertisement.manufacturerData.slice(2);
        }
        var recv_time = (new Date).getTime()/1000;

        if(singleSource == true) {
            if(address != pb_address) {
                return;
            }
        }

        // check length of data
        if (data.length < 19) {
            console.log("ERROR: Bad PowerBlade packet");
            console.log(data.length);
            console.log(data);
            console.log(advertisement);
            return;
        }

        // check software version number
        var version_num = data.readUIntBE(0,1);
        if (version_num < 1) {
            console.log("ERROR: PowerBlade version 0 discovered!");
            return;
        }

        // check for duplicate advertisements
        var sequence_num = data.readUIntBE(1,4);
        if (!(address in powerblade_sequences)) {
            powerblade_sequences[address] = -1;
        }
        if (dedup && powerblade_sequences[address] == sequence_num) {
            // duplicate advertisement. Don't display
            return;
        }
        powerblade_sequences[address] = sequence_num;

        // parse fields from advertisement
        var pscale = data.readUIntBE(5,2);
        var vscale =  data.readUIntBE(7,1);
        var whscale = data.readUIntBE(8,1);
        var v_rms = data.readUIntBE(9,1);
        var real_power = data.readUIntBE(10,2);
        var apparent_power = data.readUIntBE(12,2);
        var watt_hours = data.readUIntBE(14,4);
        var flags = data.readUIntBE(18,1);

        // calculate scaling values
        var volt_scale;
        if (version_num == 1) {
            volt_scale = vscale / 50;
        } else {
            // starting in version 2, vscale became bigger to allow for more
            //  precision in v_rms
            volt_scale = vscale / 200;
        }
        var power_scale = (pscale & 0x0FFF) * Math.pow(10,-1*((pscale & 0xF000) >> 12));
        var wh_shift = whscale;

        // scale measurements from PowerBlade
        var v_rms_disp = v_rms*volt_scale;
        var real_power_disp = real_power*power_scale;
        var app_power_disp = apparent_power*power_scale;
        if(volt_scale > 0) {
          var watt_hours_disp = watt_hours*Math.pow(2, wh_shift)*(power_scale/3600);
        } else {
          var watt_hours_disp = watt_hours;
        }

        // Exponential subtraction
        // 6.6 and 0.015 are hard coded for PB version 1
        // PB version 2 and greater will transmit device-specific values with each packet
        // real_power_disp = real_power_disp - 6.6*Math.exp(-0.015*real_power_disp)

        var pf_disp = real_power_disp / app_power_disp;

        // display data to user
        console.log('PowerBlade (' + address +')');

        if (company_id == OLD_COMPANY_ID) {
            console.log("WARNING: Old PowerBlade packet format!");
        }
        else {
            if (flags & 0x80) {
                console.log('Wireless calibrated unit');
            }
            else if (flags & 0x40) {
                console.log('Local calibrated unit');
            }
            else {
                console.log('WARNING: Uncalibrated unit');
            }
        }

        console.log('      Sequence Number: ' + sequence_num);
        console.log('          RMS Voltage: ' + v_rms_disp.toFixed(2) + ' V');
        console.log('           Real Power: ' + real_power_disp.toFixed(2) + ' W');
        console.log('       Apparent Power: ' + app_power_disp.toFixed(2) + ' VA');
        console.log('Cumulative Energy Use: ' + watt_hours_disp.toFixed(2) + ' Wh');
        console.log('         Power Factor: ' + pf_disp.toFixed(2));
        console.log('                Flags: ' + flags);
        console.log('Raw voltage: ' + v_rms.toFixed(2));
        console.log('Volt scale: ' + volt_scale.toFixed(2));
        console.log('Pscale: ' + pscale.toFixed(2));
        console.log('');

        if (config.connect_to_influx == true){
            influx.writePoints([
                {
                    measurement: config.influx.measurement,
                    tags: { device: 'Powerblade', unit:'W' },
                    fields: { 
                                Powerblade_P: parseFloat(real_power_disp.toFixed(2)),
                                Powerblade_E: parseFloat(watt_hours_disp.toFixed(2)),
                                scaling_factor:1
                            }
                }
            ]).catch(err => {
                console.error(`Error saving data to InfluxDB! ${err.stack}`)
            })    
        }
	var write_data_str = v_rms_disp.toFixed(2)+','+real_power_disp.toFixed(2)+','+app_power_disp.toFixed(2)+','+watt_hours_disp.toFixed(2)+','+pf_disp.toFixed(2);
	write_data_str = getDateTime() +','+  write_data_str + '\n';
	stream.write(write_data_str);
    }

});
