var serviceUuid = "181A";                                                           // ESS UUID
var writeValue = "Written Name";                                                    // value to write to characteristic
var essdescriptorUuid = "290D";

var ess_service = "181A";

var device_connected = false;
var timer;
var touchduration = 3000; //length of time we want the user to touch before we do something
var connection_toggle = false;
var is_init = false;

var last_update = 0;

var switch_visibility_console_check = "visible";
var switch_visibility_steadyscan_check = "visible";
var deviceId = "C0:98:E5:70:00:02";
var adata;
var paused = false;
// Load the swipe pane
$(document).on('pageinit',function(){
    $("#main_view").on("swipeleft",function(){
        $("#logPanel").panel( "open");
    });
});

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
    },
    onParseAdvData: function(device){
        //Parse Advertised Data
        scanRecord = new Uint8Array(device.advertising);
        index = 0;
        data = null;
        while (index < scanRecord.length) {
            length = scanRecord[index++];
            if (length == 0) break; //Done once we run out of records
            type = scanRecord[index];
            if (type == 0) break; //Done if our record isn't a valid type
            adData = scanRecord.subarray(index + 1, index + length);
            if (type==0xFF && length>4 && adData[1]==0x49 && adData[0]==0x08) data=adData.slice(2);
            index += length; //Advance
        }
        if (data==null) return;

        adata = data;

        console.log( Array.prototype.map.call(new Uint8Array(data),function(m){return ("0"+m.toString(16)).substr(-2);}).join(' ') );

        console.log( data[7].toString(2) + " " + data[8].toString(2) );

        pscale          = app.r((new Uint16Array(data.slice( 7, 9).buffer))[0],2);
        vscale          = app.r((new Uint8Array (data.slice( 6, 7).buffer))[0],1);
        whscale         = app.r((new Uint8Array (data.slice( 5, 6).buffer))[0],1);
        v_rms           = app.r((new Uint8Array (data.slice( 9,10).buffer))[0],1);
        true_power      = app.r((new Uint16Array(data.slice(10,12).buffer))[0],2);
        apparent_power  = app.r((new Uint16Array(data.slice(12,14).buffer))[0],2);
        watt_hours      = app.r((new Uint32Array(data.slice(14,18).buffer))[0],4);

        volt_scale      = vscale / 50;
        power_scale     = ((new Uint16Array([pscale]))[0] & 0x0FFF) * Math.pow(10, -1 * (((new Uint16Array([pscale]))[0] & 0xF000) >> 12));
    
        v_rms_disp      = v_rms * volt_scale;
        true_power_disp = true_power * power_scale;
        app_power_disp  = apparent_power * power_scale;
        watt_hours_disp = (volt_scale > 0) ? (watt_hours << whscale) * (power_scale / 3600) : watt_hours;
        pf_disp         = true_power_disp / app_power_disp;

        console.log("pscale: " + pscale.toString(2) + ", vscale: " + vscale.toString(16) + ", whscale: " + whscale.toString(16) + ", v_rms: " + v_rms.toString(16) + ", true_power: " + true_power.toString(16) + ", apparent_power: " + apparent_power.toString(16) + ", watt_hours: " + watt_hours.toString(16));

        document.getElementById("timeLastRecievedVal").innerHTML = (new Date()).toLocaleTimeString();
        document.getElementById("rmsVoltageVal").innerHTML       = v_rms_disp.toFixed(2) + " V";
        document.getElementById("truePowerVal").innerHTML        = true_power_disp.toFixed(2) + " W";
        document.getElementById("apparentPowerVal").innerHTML    = app_power_disp.toFixed(2) + " W";
        document.getElementById("wattHoursVal").innerHTML        = watt_hours_disp.toFixed(2) + " Wh";
        document.getElementById("powerFactorVal").innerHTML      = pf_disp.toFixed(2);

        // app.update_time_ago();

        // app.onEnable();

    },
    r: function(x,c) {
        y = x.toString(2).split("").reverse().join("");
        return parseInt("00000000000000000000000000000000".substr(y.length)+y,2);
    },
    update_time_ago: function () {
        if (last_update > 0) {
            // Only do something after we've gotten a packet
            // Default output
            var out = 'Haven\'t gotten a packet in a while...';

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
        }
    },
    // Function to Log Text to Screen
    log: function(string) {
        document.querySelector("#console").innerHTML += (new Date()).toLocaleTimeString() + " : " + string + "<br />";
        document.querySelector("#console").scrollTop = document.querySelector("#console").scrollHeight;
    }
};

    // fromBuffer: function(buf) {
    //   var bits = []
    //   for (var i = 0; i < buf.length; i++) bits = bits.concat(BitArray.from32Integer(buf[i]).toJSON())
    //   return bits;
    // }

app.initialize();
