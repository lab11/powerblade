// app state
var paused = false;
var switch_visibility_console_check = "visible";
var switch_visibility_steadyscan_check = "visible";
var steadyscan_on = true;

// device state
var deviceId = "C0:98:E5:70:00:2D"; // set to value for testing, overwritten by summon
var last_update = 0;

// Load the swipe pane
$(document).on('pageinit',function(){
    $("#main_view").on("swipeleft",function(){
        $("#logPanel").panel( "open");
    });
});

var UMICH_COMPANY_ID = 0x02E0;
var POWERBLADE_SERVICE_ID = 0x11;
var OLD_COMPANY_ID = 0x4908;

function parse_powerblade(adv) {
    // parse company id and service byte
    var company_id = 0;
    var service_id = 0;
    if (adv.manufacturerData !== undefined && adv.manufacturerData
            && adv.manufacturerData.length >= 3) {
        company_id = (adv.manufacturerData[1]<<8) | adv.manufacturerData[0];
        service_id = adv.manufacturerData[2];
    }

    // check that this is a powerblade data packet
    //  Eddystone packets are silently ignored
    if ((company_id == UMICH_COMPANY_ID && service_id == POWERBLADE_SERVICE_ID) ||
            company_id == OLD_COMPANY_ID) {

        // values to be displayed
        var v_rms_disp = 0;
        var real_power_disp = 0;
        var app_power_disp = 0;
        var watt_hours_disp = 0;
        var pf_disp = 0;

        // parse values from advertisement
        var data = new DataView(adv.manufacturerData.slice(3).buffer);
        if (company_id == OLD_COMPANY_ID) {
            // support old packet format
            data = new DataView(adv.manufacturerData.slice(2).buffer);
            app.log("WARNING: Old PowerBlade packet format");
		}

        var powerblade_id  = data.getUint8(0);
        app.log("PowerBlade version " + powerblade_id);
        switch (powerblade_id) {
            case 0x01:
                var sequence_num   = data.getUint32(1);
                var pscale         = data.getUint16(5);
                var vscale         = data.getUint8(7);
                var whscale        = data.getUint8(8);
                var v_rms          = data.getUint8(9);
                var real_power     = data.getUint16(10);
                var apparent_power = data.getUint16(12);
                var watt_hours     = data.getUint32(14);
                var flags          = data.getUint8(18);

                // do maths
                var volt_scale = vscale / 50;
                var power_scale = (pscale & 0x0FFF) * Math.pow(10,-1*((pscale & 0xF000) >> 12));
                var wh_shift = whscale;
                var v_rms_disp = v_rms*volt_scale;
                var real_power_disp = real_power*power_scale;
                var app_power_disp = apparent_power*power_scale;
                if(volt_scale > 0) {
                  var watt_hours_disp = (watt_hours << wh_shift)*(power_scale/3600);
                }
                else {
                  var watt_hours_disp = watt_hours;
                }
                var pf_disp = real_power_disp / app_power_disp;
                break;

            case 0x02:
                // version 2 has a vscale value that needs to be divided by 200
                //  instead of 50. Sending a larger vscale allows the resulting
                //  voltage displayed to the user to be more precise
                var sequence_num   = data.getUint32(1);
                var pscale         = data.getUint16(5);
                var vscale         = data.getUint8(7);
                var whscale        = data.getUint8(8);
                var v_rms          = data.getUint8(9);
                var real_power     = data.getUint16(10);
                var apparent_power = data.getUint16(12);
                var watt_hours     = data.getUint32(14);
                var flags          = data.getUint8(18);

                // do maths
                var volt_scale = vscale / 200;
                var power_scale = (pscale & 0x0FFF) * Math.pow(10,-1*((pscale & 0xF000) >> 12));
                var wh_shift = whscale;
                var v_rms_disp = v_rms*volt_scale;
                var real_power_disp = real_power*power_scale;
                var app_power_disp = apparent_power*power_scale;
                if(volt_scale > 0) {
                  var watt_hours_disp = (watt_hours << wh_shift)*(power_scale/3600);
                }
                else {
                  var watt_hours_disp = watt_hours;
                }
                var pf_disp = real_power_disp / app_power_disp;
                break;

            default:
                app.log("Error: Can't handle version " + powerblade_id);
        }

        // write to user interface
        document.getElementById("timeLastRecievedVal").innerHTML = (new Date()).toLocaleTimeString();
        document.getElementById("rmsVoltageVal").innerHTML       = v_rms_disp.toFixed(2) + " V";
        document.getElementById("truePowerVal").innerHTML        = real_power_disp.toFixed(2) + " W";
        document.getElementById("apparentPowerVal").innerHTML    = app_power_disp.toFixed(2) + " W";
        document.getElementById("wattHoursVal").innerHTML        = watt_hours_disp.toFixed(2) + " Wh";
        document.getElementById("powerFactorVal").innerHTML      = pf_disp.toFixed(2);

        // Update data reception timestamp
        last_update = Date.now();
    }
}

function parse_advertisement(adv_buffer) {
    //Parse Advertised Data
    var scanRecord = new Uint8Array(adv_buffer);

    // double-check that this is the right device
    if (scanRecord.length > 11 && 
		((scanRecord[4] == 0xFF && scanRecord[5] == 0x08 && scanRecord[6] == 0x49) 			|| 
		(scanRecord[5] == 0xE0 && scanRecord[6] == 0x02 && scanRecord[7] == 0x11) 
		 ||
       	(scanRecord[8] == 0xFF && scanRecord[9] == 0xE0 && 
		scanRecord[10] == 0x02 && scanRecord[11] == 0x11))) {

        // values to be displayed
        var v_rms_disp = 0;
        var real_power_disp = 0;
        var app_power_disp = 0;
        var watt_hours_disp = 0;
        var pf_disp = 0;

        // parse values from advertisement
        var data = new DataView(adv_buffer, 12);
        if (scanRecord[5] == 0x08) {
            // support old packet format
            data = new DataView(adv_buffer, 7);
            app.log("WARNING: Oldest PowerBlade packet format");
        } else if(scanRecord[5] == 0xE0) {
            data = new DataView(adv_buffer, 8);
            app.log("WARNING: Older PowerBlade packet format");
		}

        var powerblade_id  = data.getUint8(0);
        app.log("PowerBlade version " + powerblade_id);
        switch (powerblade_id) {
            case 0x01:
                var sequence_num   = data.getUint32(1);
                var pscale         = data.getUint16(5);
                var vscale         = data.getUint8(7);
                var whscale        = data.getUint8(8);
                var v_rms          = data.getUint8(9);
                var real_power     = data.getUint16(10);
                var apparent_power = data.getUint16(12);
                var watt_hours     = data.getUint32(14);
                var flags          = data.getUint8(18);

                // do maths
                var volt_scale = vscale / 50;
                var power_scale = (pscale & 0x0FFF) * Math.pow(10,-1*((pscale & 0xF000) >> 12));
                var wh_shift = whscale;
                var v_rms_disp = v_rms*volt_scale;
                var real_power_disp = real_power*power_scale;
                var app_power_disp = apparent_power*power_scale;
                if(volt_scale > 0) {
                  var watt_hours_disp = (watt_hours << wh_shift)*(power_scale/3600);
                }
                else {
                  var watt_hours_disp = watt_hours;
                }
                var pf_disp = real_power_disp / app_power_disp;
                break;

            case 0x02:
                // version 2 has a vscale value that needs to be divided by 200
                //  instead of 50. Sending a larger vscale allows the resulting
                //  voltage displayed to the user to be more precise
                var sequence_num   = data.getUint32(1);
                var pscale         = data.getUint16(5);
                var vscale         = data.getUint8(7);
                var whscale        = data.getUint8(8);
                var v_rms          = data.getUint8(9);
                var real_power     = data.getUint16(10);
                var apparent_power = data.getUint16(12);
                var watt_hours     = data.getUint32(14);
                var flags          = data.getUint8(18);

                // do maths
                var volt_scale = vscale / 200;
                var power_scale = (pscale & 0x0FFF) * Math.pow(10,-1*((pscale & 0xF000) >> 12));
                var wh_shift = whscale;
                var v_rms_disp = v_rms*volt_scale;
                var real_power_disp = real_power*power_scale;
                var app_power_disp = apparent_power*power_scale;
                if(volt_scale > 0) {
                  var watt_hours_disp = (watt_hours << wh_shift)*(power_scale/3600);
                }
                else {
                  var watt_hours_disp = watt_hours;
                }
                var pf_disp = real_power_disp / app_power_disp;
                break;

            default:
                app.log("Error: Can't handle version " + powerblade_id);
        }

        // write to user interface
        document.getElementById("timeLastRecievedVal").innerHTML = (new Date()).toLocaleTimeString();
        document.getElementById("rmsVoltageVal").innerHTML       = v_rms_disp.toFixed(2) + " V";
        document.getElementById("truePowerVal").innerHTML        = real_power_disp.toFixed(2) + " W";
        document.getElementById("apparentPowerVal").innerHTML    = app_power_disp.toFixed(2) + " W";
        document.getElementById("wattHoursVal").innerHTML        = watt_hours_disp.toFixed(2) + " Wh";
        document.getElementById("powerFactorVal").innerHTML      = pf_disp.toFixed(2);

        // Update data reception timestamp
        last_update = Date.now();

    } else {
        app.log("Unexpected advertisement structure - logging scan record");
		app.log(scanRecord);
    }
}

// translates advertisement into a platform-agnostic format
//  The original `.advertising` field is maintained, but a new `.advertisement`
//  field is created that mimics the Noble (nodejs library) structure and is
//  automatically populated regardless of OS
//  Format: https://github.com/sandeepmistry/noble#peripheral-discovered
function translate_advertisement(device) {
    device.advertisement = {
        localName: undefined,
        txPowerLevel: undefined,
        manufacturerData: undefined,
        serviceData: [],
        serviceUuids: [],
    };

    // determine if we know how to parse the .advertising field
    if (Object.prototype.toString.call(device.advertising) === '[object ArrayBuffer]') {
        // raw ArrayBuffer of bytes (android format)
        android_advertisement(device);

    } else if ('kCBAdvDataChannel' in device.advertising) {
        // dict of already-parsed fields (iOS format)
        ios_advertisement(device);

    } else {
        // don't know how to parse this data
        app.log("Can't translate advertisement data");
    }
}

// code adapted from https://github.com/sandeepmistry/noble/blob/master/lib/hci-socket/gap.js
function android_advertisement (device) {
    var eir = new Buffer(device.advertising);
    var advertisement = device.advertisement;

    // parse each advertisement field
    var i = 0;
    while ((i + 1) < eir.length) {
        var length = eir.readUInt8(i);

        // length of 0 signifies end of advertisement data
        if (length < 1) {
            break;
        }

        var eirType = eir.readUInt8(i + 1);

        if ((i + length + 1) > eir.length) {
            app.log('invalid EIR data, out of range of buffer length');
            break;
        }

        var bytes = eir.slice(i + 2).slice(0, length - 1);

        // switch on advertisement field type
        //  https://www.bluetooth.org/en-us/specification/assigned-numbers/generic-access-profile
        //  the structure of each field is defined in the BLE Core
        //  Specification Supplement (see CSSv6)
        switch(eirType) {
            case 0x02: // Incomplete List of 16-bit Service Class UUID
            case 0x03: // Complete List of 16-bit Service Class UUIDs
                for (var j = 0; j < bytes.length; j += 2) {
                    var serviceUuid = bytes.readUInt16LE(j).toString(16);
                    if (advertisement.serviceUuids.indexOf(serviceUuid) === -1) {
                        advertisement.serviceUuids.push(serviceUuid);
                    }
                }
                break;

            case 0x06: // Incomplete List of 128-bit Service Class UUIDs
            case 0x07: // Complete List of 128-bit Service Class UUIDs
                for (var j = 0; j < bytes.length; j += 16) {
                    var serviceUuid = bytes.slice(j, j + 16).toString('hex').match(/.{1,2}/g).reverse().join('');
                    if (advertisement.serviceUuids.indexOf(serviceUuid) === -1) {
                        advertisement.serviceUuids.push(serviceUuid);
                    }
                }
                break;

            case 0x08: // Shortened Local Name
            case 0x09: // Complete Local Name»
                advertisement.localName = bytes.toString('utf8');
                break;

            case 0x0a: // Tx Power Level
                advertisement.txPowerLevel = bytes.readInt8(0);
                break;

            case 0x16: // Service Data, there can be multiple occurences
                var serviceDataUuid = bytes.slice(0, 2).toString('hex').match(/.{1,2}/g).reverse().join('');
                var serviceData = bytes.slice(2, bytes.length);

                advertisement.serviceData.push({
                    uuid: serviceDataUuid,
                    data: serviceData
                });
                break;

            case 0xff: // Manufacturer Specific Data
                advertisement.manufacturerData = bytes;
                break;
        }

        i += (length + 1);
    }
}

// code adapted from https://github.com/sandeepmistry/noble/blob/master/lib/mac/mavericks.js
function ios_advertisement (device) {
    var args = {'kCBMsgArgAdvertisementData': device.advertising};
    var advertisement = device.advertisement;

    advertisement.localName = args.kCBMsgArgAdvertisementData.kCBAdvDataLocalName || device.name;
    advertisement.txPowerLevel = args.kCBMsgArgAdvertisementData.kCBAdvDataTxPowerLevel;
    advertisement.manufacturerData = args.kCBMsgArgAdvertisementData.kCBAdvDataManufacturerData;

    var serviceData = args.kCBMsgArgAdvertisementData.kCBAdvDataServiceData;
    if (serviceData) {
        for (i = 0; i < serviceData.length; i += 2) {
            var serviceDataUuid = serviceData[i].toString('hex');
            var data = serviceData[i + 1];

            advertisement.serviceData.push({
                uuid: serviceDataUuid,
                data: data
            });
        }
    }

    if (args.kCBMsgArgAdvertisementData.kCBAdvDataServiceUUIDs) {
        for(i = 0; i < args.kCBMsgArgAdvertisementData.kCBAdvDataServiceUUIDs.length; i++) {
            advertisement.serviceUuids.push(args.kCBMsgArgAdvertisementData.kCBAdvDataServiceUUIDs[i].toString('hex'));
        }
    }
}

var app = {
    // Application Constructor
    initialize: function() {
        document.addEventListener("deviceready", app.onAppReady, false);
        document.addEventListener("resume", app.onAppReady, false);
        document.addEventListener("pause", app.onPause, false);
    },
    // App Ready Event Handler
    onAppReady: function() {
        // Setup update for last data time
        // setInterval(app.update_time_ago, 5000);

        if (typeof window.gateway != "undefined") {                               // if UI opened through Summon,
            deviceId = window.gateway.getDeviceId();                                // get device ID from Summon
            deviceName = window.gateway.getDeviceName();                            // get device name from Summon
            app.log("Opened via Summon..");
            //parse_advertisement(window.gateway.getDeviceAdvertisement());
            //app.log("Updated with initial advertisement");
        }
        document.getElementById("title").innerHTML = String(deviceId);
        app.log("Checking if ble is enabled...");
        paused=false;
        bluetooth.isEnabled(app.onEnable);                                                // if BLE enabled, goto: onEnable
    },
    // App Paused Event Handler
    onPause: function() {
        app.log("on Pause");                                                           // if user leaves app, stop BLE
        bluetooth.stopScan();
        paused=true;
    },
    // Bluetooth Enabled Callback
    onEnable: function() {
        bluetooth.stopScan(function(){
            bluetooth.startScan([],app.onDiscover,function(e){console.log(e)});
            setTimeout(function(){if (!paused) app.onEnable()},1000);
        },app.onAppReady);
        app.log("Searching for (" + deviceId + ").");
    },
    // BLE Device Discovered Callback
    onDiscover: function(device) {
        //app.log("onDiscover");
        if (device.id == deviceId) {
            app.log("Found (" + deviceId + ")!");

            // convert to os-agnostic advertisement data
            //translate_advertisement(device);

            // actually use the advertisement data
            //parse_advertisement(device.advertising);
            parse_powerblade(device.advertisement);
        }

        // update time notion
        app.update_time_ago();
    },
    update_time_ago: function () {
        // Default output
        var out = 'Waiting for data...';

        var now = Date.now();
        var diff = now - last_update;
        if (diff < 60000) {
            // less than a minute
            var seconds = Math.round(diff/1000);
            out = 'Last updated ' + seconds + ' second';
            if (seconds != 1) {
                out += 's';
            }
            out += ' ago';

        } else if (diff < 120000) {
            out = 'Last updated about a minute ago';
        }

        document.querySelector("#data_update").innerHTML = out;
    },
    // Function to Log Text to Screen
    log: function(string) {
        document.querySelector("#console").innerHTML += (new Date()).toLocaleTimeString() + " : " + string + "<br />";
        document.querySelector("#console").scrollTop = document.querySelector("#console").scrollHeight;
    }
};

app.initialize();

