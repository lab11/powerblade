var async = require('async');
var noble = require('noble');

// mangled version of 0x4908
var CompanyID = 18696;

var peripherals = {};

var prev_time = 0;

var aveValue = [10];
var aveIndex = 0;

console.log('Current Transformer Calibration');

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
    var ippk_10s = data.readUIntBE(1,4);
    var ippk_1s = data.readUIntBE(5,4);
    var flags = data.readUIntBE(18,1);

    if(true || ippk_1s != prev_time){

      // Average value
      aveValue[aveIndex++] = ippk_10s;
      if(aveIndex == 10) {
        aveIndex = 0;
      }
      var averageValue = 0;
      for (var i = aveValue.length - 1; i >= 0; i--) {
        averageValue += aveValue[i];
      };
      averageValue = averageValue / 10;

      console.log('Data: ' + recv_time);
      console.log('         BLE Address: ' + peripheral_uuid);
      console.log('       PowerBlade ID: ' + '0x' + powerblade_id.toString(16));
      console.log('I Peak-to-Peak (10s): ' + ippk_10s + ' (0x' + ippk_10s.toString(16) + ')');
      console.log('I Peak-to-Peak  (1s): ' + ippk_1s + ' (0x' + ippk_1s.toString(16) + ')');
      console.log('               Flags: ' + '0x' + flags.toString(16));
      console.log('       Average (10s): ' + averageValue.toFixed(2));

        console.log('');
    }
    prev_time = ippk_1s;

  }
});

