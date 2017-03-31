#!/usr/bin/env node

var noble = require('noble');
var fs = require('fs');
var dateFormat = require('dateformat');
var readlineSync = require('readline-sync');
var childProcess = require('child_process');

var mqtt = require('mqtt');

var debug = false;
var dedup = true;
var pb_address = 0;
var pb_tag = "";
var device = "";
var count = 50;
var rx_count = 0;
var host = 'mqtt://localhost';
for(var i = 0; i < process.argv.length; i++) {
    var val = process.argv[i];
    if(val == "-v" || val == "--verbose") {
        console.log("Running with verbose output (printing PowerBlade advertisements)");
        debug = true;
    }
    else if(val == "-a" || val == "--all") {
        console.log("Dedup disabled");
        dedup = false;
    }
    else if(val == "-m") {
        pb_address = "c0:98:e5:70:" + process.argv[++i];  // Additional increment of i
    }
    else if(val == "--mac") {
        pb_address = process.argv[++i];   // Additional increment of i
    }
    else if(val == "-t" || val == "--tag") {
        pb_tag = "_" + process.argv[++i];          // Additional increment of i
        //console.log("Tagging file with additional tag: " + pb_tag);
    }
    else if(val == "-c" || val == "--count") {
        count = parseInt(process.argv[++i]); // Additional increment of i
        if(count > 0) {
            console.log("Collecting " + count + " advertisements");
        }
    }
    else if(val == "-s" || val == "--server") {
        host = 'mqtt://' + process.argv[++i];
        console.log("Connecting to " + host);
    }
    else if(val == "-d" || val == "--device") {
        device = "_" + process.argv[++i];
    }
}

// Check for the required parameter
if(pb_address == 0) {
    console.log("Error: Must run with a certain PowerBlade");
    console.log("Use \"-m xx:xx\" or \"--mac c0:98:e5:70:xx:xx\" to specify");
    process.exit();
}

if(device == "") {
    console.log("Error: Must run with a certain device");
    console.log("Use \"-d [device]\" or \"--device [device]\" to specify");
    process.exit();
}

var addr_list = pb_address.split(":");
if(!(addr_list.length == 6 && addr_list[0] == "c0" && addr_list[1] == "98" && addr_list[2] == "e5" && addr_list[3] == "70" && !isNaN(parseInt(addr_list[4], 16)) && !isNaN(parseInt(addr_list[5], 16)))) {
    console.log("Error: Invalid PowerBlade address");
    console.log("Use \"-m c0:98:e5:70:xx:xx\" or \"--mac c0:98:e5:70:xx:xx\" to specify");
    process.exit();
}

console.log("Looking for PowerBlade " + pb_address);

var g_time_start = new Date();

//filename = dateFormat(g_time_start, "yyyy-mm-dd_h-MM-ss") + "_" + addr_list[0] + addr_list[1] + addr_list[2] + addr_list[3] + addr_list[4] + addr_list[5] + pb_tag + ".txt";
filename = process.env.PB_DATA + "measurements_rig/" + addr_list[0] + addr_list[1] + addr_list[2] + addr_list[3] + addr_list[4] + addr_list[5] + device + pb_tag + ".dat";

if(fs.existsSync(filename)) {
    var replace = readlineSync.question("File exists: overwrite, rename, or exit? (o/r/e): ");
    if(replace == 'r') {
        var newfileNum = 0
        var newfile = filename.split('.')[0] + '.bak'
        while(fs.existsSync(newfile)) {
            newfileNum += 1
            newfile = filename.split('.')[0] + '_' + newfileNum + '.bak'
        }
        console.log("Copying existing log to " + newfile);
        fs.renameSync(filename, newfile);
    } 
    else if(replace != 'o') {
        process.exit()
    }
}

fs.closeSync(fs.openSync(filename, 'w'));

console.log("Logging to " + filename);

var UMICH_COMPANY_ID = 0x02E0;
var POWERBLADE_SERVICE_ID = 0x11;
var OLD_COMPANY_ID = 0x4908;

// {BLE Address: Most recent sequence number} for each PowerBlade
var powerblade_sequences = {};

var total = 0;

var mqtt_client = mqtt.connect(host);
mqtt_client.on('connect', function () {
    console.log("Connected to MQTT");
    mqtt_client.subscribe('gateway-data');

    mqtt_client.on('message', function (topic, message) {
        var adv = JSON.parse(message.toString());

        //console.log(adv);

        if(adv['_meta'] && adv['_meta']['device_id'] == pb_address.replace(new RegExp(':', 'g'), '')) {

            var writeObject = {
                seq: adv['sequence_number'], 
                vrms: parseFloat(adv['rms_voltage']).toFixed(2),
                power: parseFloat(adv['power']).toFixed(2),
                app: parseFloat(adv['apparent_power']).toFixed(2),
                wh: parseFloat(adv['energy']).toFixed(2),
                pf: parseFloat(adv['power_factor']).toFixed(2),
                fg: adv['flags']
            }

            fs.appendFileSync(filename, JSON.stringify(writeObject) + "\n", 'utf-8');

            rx_count = rx_count + 1;
            process.stdout.write(rx_count + "/50 (" + adv['sequence_number'] + "): " + adv['power'] + "\n");
            total = total + parseFloat(adv['power']);
            if(rx_count == count) {
                process.stdout.write("\n");
                console.log("Average power: " + (total/count))

                runScript('./data_check.js', device.substr(1), function (err) {
				    if (err) throw err;
				    console.log('finished running data_check.js');
				    process.exit();
				});
            }
        }
	});
});

function runScript(scriptPath, arg, callback) {

    // keep track of whether callback has been invoked to prevent multiple invocations
    var invoked = false;

	var opts = [arg];
    var cprocess = childProcess.fork(scriptPath, opts);

    // listen for errors as they may prevent the exit event from firing
    cprocess.on('error', function (err) {
        if (invoked) return;
        invoked = true;
        callback(err);
    });

    // execute the callback once the process has finished running
    cprocess.on('exit', function (code) {
        if (invoked) return;
        invoked = true;
        var err = code === 0 ? null : new Error('exit code ' + code);
        callback(err);
    });
}

/*noble.on('stateChange', function(state) {
    if (state === 'poweredOn') {
        console.log("Starting scan...");
        noble.startScanning([], true);
    } else {
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

        if(address != pb_address) {
            return;
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
        var watt_hours_disp = watt_hours*Math.pow(2, wh_shift)*(power_scale/3600);
        var pf_disp = real_power_disp / app_power_disp;

        // display data to user
        if (debug) {
            console.log('PowerBlade (' + address +')');
        }

        if (company_id == OLD_COMPANY_ID) {
            console.log("WARNING: Old PowerBlade packet format!");
        }
        else if (debug) {
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

        if (debug) {
            console.log('      Sequence Number: ' + sequence_num);
            console.log('          RMS Voltage: ' + v_rms_disp.toFixed(2) + ' V');
            console.log('           Real Power: ' + real_power_disp.toFixed(2) + ' W');
            console.log('       Apparent Power: ' + app_power_disp.toFixed(2) + ' VA');
            console.log('Cumulative Energy Use: ' + watt_hours_disp.toFixed(2) + ' Wh');
            console.log('         Power Factor: ' + pf_disp.toFixed(2));
            console.log('                Flags: ' + flags);
            // console.log('Raw voltage: ' + v_rms.toFixed(2));
            // console.log('Volt scale: ' + volt_scale.toFixed(2));
            // console.log('Pscale: ' + pscale.toFixed(2));
            console.log('');
        }

        var writeObject = {
            seq: sequence_num, 
            vrms: v_rms_disp.toFixed(2),
            power: real_power_disp.toFixed(2),
            app: app_power_disp.toFixed(2),
            wh: watt_hours_disp.toFixed(2),
            pf: pf_disp.toFixed(2),
            fg: flags
        }

        fs.appendFileSync(filename, JSON.stringify(writeObject) + "\n", 'utf-8');

        rx_count = rx_count + 1;
        process.stdout.write(rx_count + "/50: " + real_power_disp + "\n");
        total = total + real_power_disp;
        if(rx_count == count) {
        	process.stdout.write("\n");
        	console.log("Average power: " + (total/count))

        	process.exit();
        }
    }
});*/



