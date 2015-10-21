var async = require('async');
var noble = require('noble');

// mangled version of 0x4908
var CompanyID = 18696;

var peripherals = {};

console.log('Raw Calibration');

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
    var i_offset = data.readUIntBE(1,4);
    var v_offset = data.readUIntBE(5,4);
    var i_offset_min = data.readUIntBE(9,1);
    var i_offset_max = data.readUIntBE(10,2);
    var v_offset_min = data.readUIntBE(12,2);
    var v_offset_max = data.readUIntBE(14,4);
    var flags = data.readUIntBE(18,1);

    // print unique seq's to user
    console.log('Data: ' + recv_time);
    console.log('    BLE Address: ' + peripheral_uuid);
    console.log('  PowerBlade ID: ' + '0x' + powerblade_id.toString(16));
    console.log('       I Offset: ' + i_offset + ' (0x' + i_offset.toString(16) + ')');
    console.log('       V Offset: ' + v_offset + ' (0x' + v_offset.toString(16) + ')');
    console.log('   I Offset Min: ' + i_offset_min + ' (0x' + i_offset_min.toString(16) + ')');
    console.log('   I Offset Max: ' + i_offset_max + ' (0x' + i_offset_max.toString(16) + ')');
    console.log('   V Offset Min: ' + v_offset_min + ' (0x' + v_offset_min.toString(16) + ')');
    console.log('   V Offset Max: ' + v_offset_max + ' (0x' + v_offset_max.toString(16) + ')');
    console.log('          Flags: ' + '0x' + flags.toString(16));

    console.log('');

  }
});

