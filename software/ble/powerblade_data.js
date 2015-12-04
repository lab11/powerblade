var async = require('async');
var noble = require('noble');

// mangled version of 0x4908
var CompanyID = 18696;

var peripherals = {};

var aveTime = [10];
var timeIndex = 0;

var avePower = [10];
var aveApp = [10];
var aveIndex = 0;

var timesInThirty = [30];
var indexToThirty = 0;

var watt_hours_tot = 0;
var recv_last = 0;

var iden_count = 0;

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
  var advertisement = peripheral.advertisement;
  var manufacturer_id = 0;
  if (typeof advertisement.manufacturerData !== undefined && advertisement.manufacturerData && advertisement.manufacturerData.length >= 2) {
    manufacturer_id = advertisement.manufacturerData.readUIntLE(0,2);
  }

  // check if device is actually a PowerBlade
  if (manufacturer_id == CompanyID) {
    var peripheral_uuid = peripheral.uuid;
    if (!(peripheral_uuid in peripherals)) {
        // device doesn't exist. Add it and record a "last squence number"
        peripherals[peripheral_uuid] = -1;
    }

    // get data after the manufacturer ID
    var data = advertisement.manufacturerData.slice(2);

    // get data values from the powerblade
    var recv_time = (new Date).getTime()/1000;

    var powerblade_id = data.readUIntBE(0,1);
    var sequence_num = data.readUIntBE(1,4);
    var pscale = data.readUIntBE(5,2);
    var vscale =  data.readUIntBE(7,1);
    var whscale = data.readUIntBE(8,1);
    var v_rms = data.readUIntBE(9,1);
    var true_power = data.readUIntBE(10,2);
    var apparent_power = data.readUIntBE(12,2);
    var watt_hours = data.readUIntBE(14,4);
    var flags = data.readUIntBE(18,1);

    if (powerblade_id < 1) {
        console.log("ERROR: PowerBlade version 0 discovered!");
    }

    //var volt_scale = 2.46;
    //var power_scale = 0.0586;
    //var wh_shift = 9;
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

    // Exponential scaling
    //true_power_disp = true_power_disp - 6.6*Math.exp(-0.015*true_power_disp)

    // print unique seq's to user
    var last_seq = peripherals[peripheral_uuid];
    if (sequence_num != last_seq || sequence_num == 0) {

      // Finish last packet (by displaying count)
      // and reset iden_count
      console.log('          Num Received: ' + iden_count);
      iden_count = 0;
      console.log('');

      timesInThirty[indexToThirty++] = recv_time;
      if(indexToThirty == 30) {
        indexToThirty = 0;
      }
      var packetCount = 0;
      for (var i = timesInThirty.length - 1; i >= 0; i--) {
        if(timesInThirty[i] >= (recv_time - 30)) {
          packetCount += 1;
        }
      };

      // Average power
      avePower[aveIndex] = true_power_disp;
      var averagePower = 0;
      for (var i = avePower.length - 1; i >= 0; i--) {
        averagePower += avePower[i];
      };
      averagePower = averagePower / 10;
      // Average Apparent
      aveApp[aveIndex++] = app_power_disp;
      var appPower = 0;
      for (var i = aveApp.length - 1; i >= 0; i--) {
        appPower += aveApp[i];
      }
      appPower = appPower / 10;
      if(aveIndex == 10) {
        aveIndex = 0;
      }

      if(recv_last > 0) {
        var timeDiff = recv_time - recv_last;
      }
      else {
        var timeDiff = 1;
      }
      recv_last = recv_time;
      watt_hours_tot += (timeDiff*true_power_disp) / 3600;

      peripherals[peripheral_uuid] = sequence_num;
      last_seq = sequence_num;
      console.log('Data: ' + recv_time);
      console.log('           BLE Address: ' + peripheral_uuid);
      console.log('         PowerBlade ID: ' + '0x' + powerblade_id.toString(16));
      console.log('       Sequence Number: ' + sequence_num + ' (0x' + sequence_num.toString(16) + ')');
      console.log('           RMS Voltage: ' + v_rms_disp.toFixed(2) + ' (0x' + v_rms.toString(16) + ')');
      console.log('    Current True Power: ' + true_power_disp.toFixed(2) + ' (0x' + true_power.toString(16) + ')');
      console.log('Current Apparent Power: ' + app_power_disp.toFixed(2) + ' (0x' + apparent_power.toString(16) + ')');
      console.log(' Cumulative Watt Hours: ' + watt_hours_disp.toFixed(2) + ' (0x' + watt_hours.toString(16) + ')');
      console.log('          Power Factor: ' + pf_disp.toFixed(2));
      console.log('                 Flags: ' + '0x' + flags.toString(16));
      console.log('    Average Power (10): ' + averagePower.toFixed(2));
      console.log('   Apparent Power (10): ' + appPower.toFixed(2));
      console.log('Watt Hours Since Start: ' + watt_hours_tot.toFixed(2));
      console.log('Time Since Last Packet: ' + timeDiff.toFixed(2));
      console.log('   Packets in last 30s: ' + packetCount.toFixed(2));

    }
    else {
      iden_count += 1;
    }
  }
});

