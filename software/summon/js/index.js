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
var steadyscan_on = true;

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
        toggleOff.addEventListener('touchend', app.onTouchToggleOff, false);
        app.onAppReady();
    },
    onStartTimer: function(device){
        connection_toggle = false;
        timer = setTimeout(app.onLongPress, touchduration);
    },
    onLongPress: function(){
        app.log("timer expired");
        connection_toggle = true;
    },
    // App Ready Event Handler
    onAppReady: function() {
        app.log("amihere");

        // Setup update for last data time
        setInterval(app.update_time_ago, 5000);

        if (typeof window.gateway != "undefined") {                               // if UI opened through Summon,
            deviceId = window.gateway.getDeviceId();                                // get device ID from Summon
            deviceName = window.gateway.getDeviceName();                            // get device name from Summon
            app.log("Opened via Summon..");
        }
        app.log("Opened via Summon...");
        document.getElementById("title").innerHTML = String(deviceId);
        app.log("Checking if ble is enabled...");
        ble.isEnabled(app.onEnable);                                                // if BLE enabled, goto: onEnable
        app.onEnable();
    },
    // App Paused Event Handler
    onPause: function() {
        app.log("on Pause");                                                           // if user leaves app, stop BLE
        //ble.disconnect(deviceId);
        ble.stopScan();
    },
    // Bluetooth Enabled Callback
    onEnable: function() {
        //app.log("onEnable");
        app.onPause();                                                              // halt any previously running BLE processes
        ble.startScan([], app.onDiscover, app.onAppReady);                          // start BLE scan; if device discovered, goto: onDiscover
        app.log("Searching for " + deviceName + " (" + deviceId + ").");
    },
    // BLE Device Discovered Callback
    onDiscover: function(device) {
        //app.log("onDiscover");
        if (device.id == deviceId) {
            app.log("Found " + deviceName + " (" + deviceId + ")!");
            app.onParseAdvData(device);
            //app.onStartConnection(device);
        }
    },
    onStopScan: function(device) {
        //app.log("stopped scanning");
    },
    onTouchToggleOff: function(device) {
        document.getElementById('toggleOff').style.visibility = "hidden";
        document.getElementById('toggleOn').style.visibility = "visible";
        document.getElementById('connection_status').innerHTML = " Connected";
        app.log("Connecting to BLEES device!");
        ble.stopScan();
        app.onStartConnection(device);

    },
    onTouchToggleOn: function() {
        /*
        document.getElementById('toggleOff').style.visibility = "visible";
        document.getElementById('toggleOn').style.visibility = "hidden";
        app.onPause();
        app.onAppReady();
        */
    },
    onDiscoverDescriptors: function(char_Uuid) {

        bluetoothle.readDescriptor(app.readSuccess, app.onError, {
              "address": deviceId,
              "serviceUuid": serviceUuid,
              "characteristicUuid": char_Uuid,
              "descriptorUuid": essdescriptorUuid
        });

    },
    ondisconnectsuccess: function() {
        app.log("disconnected success!");
    },
    onPleaseConnect: function(){
        app.log("Please connect to use this feature");
    },
    onTouchConsoleCheck: function(){
        app.log("check");
        document.querySelector("#show_console_check").style.visibility = switch_visibility_console_check;
        document.querySelector("#console").style.visibility = switch_visibility_console_check;
        if(switch_visibility_console_check == "visible") {
            switch_visibility_console_check = "hidden";
        }
        else{
            switch_visibility_console_check = "visible";
        }
    },
    onTouchSteadyScanCheck: function(){
        app.log("check2");
        document.querySelector("#show_steadyscan_check").style.visibility = switch_visibility_steadyscan_check;
        if(switch_visibility_steadyscan_check == "visible") {
            switch_visibility_steadyscan_check = "hidden";
            steadyscan_on = true;
            app.onEnable();
        }
        else{
            switch_visibility_steadyscan_check = "visible";
            steadyscan_on = false;
        }
    },
    onParseAdvData: function(device){
        //Parse Advertised Data
        var adData = new Uint8Array(device.advertising);
	
        if ((adData[12] != 0x1A) || (adData[13] != 0x18)){
            app.log("not right");
            app.onEnable();
            return;
        }

        else{
            ble.stopScan(app.onStopScan, app.onError);
        }

        // Save when we got this.
        last_update = Date.now();
       
	/* 
	var recv_time = (new Date).getTime()/1000;
        var powerblade_id = BitArray.fromBuffer(data.slice(0,1)).toNumber();
        var sequence_num = BitArray.fromBuffer(data.slice(1,5)).toNumber();
        var pscale = BitArray.fromBuffer(data.slice(7,9)).toNumber();
        var vscale = BitArray.fromBuffer(data.slice(6,7)).toNumber();
        var whscale = BitArray.fromBuffer(data.slice(5,6)).toNumber();
        var v_rms = BitArray.fromBuffer(data.slice(9,10)).toNumber();
        var true_power = BitArray.fromBuffer(data.slice(10,12)).toNumber();
        var apparent_power = BitArray.fromBuffer(data.slice(12,14)).toNumber();
        var watt_hours = BitArray.fromBuffer(data.slice(14,18)).toNumber();
        var flags = BitArray.fromBuffer(data.slice(18,19)).toNumber();
        var num_connections = BitArray.fromBuffer(data.slice(19,20)).toNumber();
        var volt_scale = vscale / 50;
        var power_scale = (pscale & 0x0FFF) * Math.pow(10,-1*((pscale & 0xF000) >> 12));
        var wh_shift = whscale;
        var v_rms_disp = v_rms*volt_scale;
        var true_power_disp = true_power*power_scale;
        var app_power_disp = apparent_power*power_scale;
        if(volt_scale > 0) {
          var watt_hours_disp = (watt_hours << wh_shift)*(power_scale/3600);
        }
        else {
          var watt_hours_disp = watt_hours;
        }
        var pf_disp = true_power_disp / app_power_disp;
	
	document.getElementById("timeLastRecievedVal").innerHTML = String(last_update);
        document.getElementById("rmsVoltageVal").innerHTML = String(v_rms_disp);
        document.getElementById("truePowerVal").innerHTML = String(true_power_disp);
        document.getElementById("apparentPowerVal").innerHTML = String(app_power_disp);
        document.getElementById("wattHoursVal").innerHTML = String(watt_hours_disp);
        document.getElementById("powerFactorVal").innerHTML = String(pf_disp);
	*/

        if (intAcc) {
            document.getElementById('accLastIntCell').style.color = "#ED97B9";
            document.getElementById('accLastIntCell2').style.color = "#ED97B9";
            document.getElementById('accSpinnerInt').style.visibility = "visible";
            document.getElementById('accNotSpinnerInt').style.visibility = "hidden";

        }
        else {
            document.getElementById('accLastIntCell').style.color = "black";
            document.getElementById('accLastIntCell2').style.color = "black";
            document.getElementById('accSpinnerInt').style.visibility = "hidden";
            document.getElementById('accNotSpinnerInt').style.visibility = "visible";
        }

        app.update_time_ago();

        if(steadyscan_on){
            app.onEnable();
        }

    },
    // BLE Characteristic Write Callback
    onWrite : function() {
        app.log("Characeristic Written: " + writeValue);                            // display write success
    },
    // BLE Characteristic Read/Write Error Callback
    onError: function() {                                                           // on error, try restarting BLE
        app.log("Read/Write Error.")
        ble.isEnabled(deviceId,function(){},app.onAppReady);
        ble.isConnected(deviceId,function(){},app.onAppReady);
    },
    // Function to Convert String to Bytes (to Write Characteristics)
    stringToBytes: function(string) {
        array = new Uint8Array(string.length);
        for (i = 0, l = string.length; i < l; i++) array[i] = string.charCodeAt(i);
        return array.buffer;
    },
    buffToUInt32Decimal: function(buffer) {
        var uint32View = new Uint32Array(buffer);
        return uint32View[0];
    },
    buffToUInt16Decimal: function(buffer) {
        var uint16View = new Uint16Array(buffer);
        return uint16View[0];
    },
    buffToInt16Decimal: function(buffer) {
        var int16View = new Int16Array(buffer);
        return int16View[0];
    },
    buffToUInt8Decimal: function(buffer) {
        var uint8View = new Uint8Array(buffer);
        return uint8View[0];
    },
    bytesToString: function(buffer) {
        return String.fromCharCode.apply(null, new Uint8Array(buffer));
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

app.initialize();
