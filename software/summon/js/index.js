
// app state
var paused = false;
var switch_visibility_console_check = "visible";
var switch_visibility_steadyscan_check = "visible";
var steadyscan_on = true;

// device state
var deviceId = "C0:98:E5:70:00:02"; // set to value for testing, overwritten by summon
var last_update = 0;

// Load the swipe pane
$(document).on('pageinit',function(){
    $("#main_view").on("swipeleft",function(){
        $("#logPanel").panel( "open");
    });
});

function parse_advertisement(adv_buffer) {
    //Parse Advertised Data
    var scanRecord = new Uint8Array(adv_buffer);

    // double-check that this is the right device
    if (scanRecord.length > 7 &&
            scanRecord[0] == 0x02 && scanRecord[1] == 0x01 && scanRecord[2] == 0x06 &&
            scanRecord[4] == 0xFF &&
            scanRecord[5] == 0x08 && scanRecord[6] == 0x49) {

        // values to be displayed
        var v_rms_disp = 0;
        var real_power_disp = 0;
        var app_power_disp = 0;
        var watt_hours_disp = 0;
        var pf_disp = 0;

        // parse values from advertisement
        var data = new DataView(adv_buffer, 7);
        var powerblade_id  = data.getUint8(0);
        switch (powerblade_id) {
            case 0x01:
                app.log("PowerBlade version " + powerblade_id);
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
        app.log("Device had incorrect adv structure");
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
            parse_advertisement(window.gateway.getDeviceAdvertisement());
            app.log("Updated with initial advertisement");
        }
        document.getElementById("title").innerHTML = String(deviceId);
        app.log("Checking if ble is enabled...");
        paused=false;
        ble.isEnabled(app.onEnable);                                                // if BLE enabled, goto: onEnable
    },
    // App Paused Event Handler
    onPause: function() {
        app.log("on Pause");                                                           // if user leaves app, stop BLE
        ble.stopScan();
        paused=true;
    },
    // Bluetooth Enabled Callback
    onEnable: function() {
        ble.stopScan(function(){
            ble.startScan([],app.onDiscover,function(e){console.log(e)});
            setTimeout(function(){if (!paused) app.onEnable()},1000);
        },app.onAppReady);
        app.log("Searching for (" + deviceId + ").");
    },
    // BLE Device Discovered Callback
    onDiscover: function(device) {
        //app.log("onDiscover");
        if (device.id == deviceId) {
            app.log("Found (" + deviceId + ")!");
            app.onParseAdvData(device);
        }

        // update time notion
        app.update_time_ago();
    },
    onParseAdvData: function(device){
        parse_advertisement(device.advertising);
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

