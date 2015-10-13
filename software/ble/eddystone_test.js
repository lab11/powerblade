var async = require('async');
var noble = require('noble');
var BitArray = require('node-bitarray');

// mangled version of 0x4908
var CompanyID = 37392;

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
  var uuid = peripheral.uuid;
  if (uuid == 'da1bbb1acf38') {
      var recv_time = (new Date).getTime()/1000;
      if (typeof advertisement.serviceData !== undefined && advertisement.serviceData && advertisement.serviceData.length != 0) {
        console.log(recv_time + '\t' + 'eddystone' + '\t' + uuid);
      } else {
        console.log(recv_time + '\t' + 'powerblade' + '\t' + uuid);
      }
  }
});

