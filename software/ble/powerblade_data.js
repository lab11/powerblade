var async = require('async');
var noble = require('noble');
var BitArray = require('node-bitarray');

// mangled version of 0x4908
var CompanyID = 37392;

var peripherals = {};

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
  if (typeof advertisement.manufacturerData !== undefined && advertisement.manufacturerData) {
    manufacturer_id = BitArray.fromBuffer(advertisement.manufacturerData.slice(0,2)).toNumber();
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
    var powerblade_id = BitArray.fromBuffer(data.slice(0,1)).toNumber();
    var sequence_num = BitArray.fromBuffer(data.slice(1,5)).toNumber();
    var time = BitArray.fromBuffer(data.slice(5,9)).toNumber();
    var v_rms = BitArray.fromBuffer(data.slice(9,10)).toNumber();
    var true_power = BitArray.fromBuffer(data.slice(10,12)).toNumber();
    var apparent_power = BitArray.fromBuffer(data.slice(12,14)).toNumber();
    var watt_hours = BitArray.fromBuffer(data.slice(14,18)).toNumber();
    var flags = BitArray.fromBuffer(data.slice(18,19)).toNumber();
    var num_connections = BitArray.fromBuffer(data.slice(19,20)).toNumber();

    var v_rms_disp = v_rms*2.46;
    var true_power_disp = true_power*0.015;
    var app_power_disp = apparent_power*0.015;
    var watt_hours_disp = watt_hours*0.0000057;
    var pf_disp = true_power_disp / app_power_disp;

    // print unique seq's to user
    var last_seq = peripherals[peripheral_uuid];
    if (sequence_num != last_seq || sequence_num == 0) {
      peripherals[peripheral_uuid] = sequence_num;
      last_seq = sequence_num;
      console.log('Data: ' + recv_time);
      console.log('           BLE Address: ' + peripheral_uuid);
      console.log('         PowerBlade ID: ' + '0x' + powerblade_id.toString(16));
      console.log('       Sequence Number: ' + sequence_num + ' (0x' + sequence_num.toString(16) + ')');
      console.log('                  Time: ' + time + ' (0x' + time.toString(16) + ')');
      console.log('           RMS Voltage: ' + v_rms_disp.toFixed(2) + ' (0x' + v_rms.toString(16) + ')');
      console.log('    Current True Power: ' + true_power_disp.toFixed(2) + ' (0x' + true_power.toString(16) + ')');
      console.log('Current Apparent Power: ' + app_power_disp.toFixed(2) + ' (0x' + apparent_power.toString(16) + ')');
      console.log(' Cumulative Watt Hours: ' + watt_hours_disp.toFixed(2) + ' (0x' + watt_hours.toString(16) + ')');
      console.log('          Power Factor: ' + pf_disp.toFixed(2));
      console.log('                 Flags: ' + '0x' + flags.toString(16));
      //console.log(' Number of Connections: ' + num_connections);

      console.log('');
    }

    //explore(peripheral);
    //connect(peripheral);
  }
});

function connect(peripheral) {
    peripheral.on('disconnect', function() {
        //process.exit(0);
        noble.startScanning([], true);
    });

    peripheral.connect(function(error) {
        var conn_time = (new Date).getTime()/1000;
        console.log("Connected! " + conn_time);

        peripheral.disconnect();
    });
}

// lists all services, characteristics, and values when connected
function explore(peripheral) {
  console.log('services and characteristics:');

  peripheral.on('disconnect', function() {
    process.exit(0);
  });

  peripheral.connect(function(error) {
    var conn_time = (new Date).getTime()/1000;
    console.log("Connected! " + conn_time);

    peripheral.discoverServices([], function(error, services) {
      var serviceIndex = 0;

      async.whilst(
        function () {
          return (serviceIndex < services.length);
        },
        function(callback) {
          var service = services[serviceIndex];
          var serviceInfo = service.uuid;

          if (service.name) {
            serviceInfo += ' (' + service.name + ')';
          }
          console.log(serviceInfo + ((new Date).getTime()/1000));

          service.discoverCharacteristics([], function(error, characteristics) {
            var characteristicIndex = 0;

            async.whilst(
              function () {
                return (characteristicIndex < characteristics.length);
              },
              function(callback) {
                var characteristic = characteristics[characteristicIndex];
                var characteristicInfo = '  ' + characteristic.uuid;

                if (characteristic.name) {
                  characteristicInfo += ' (' + characteristic.name + ')';
                }

                async.series([
                  function(callback) {
                    characteristic.discoverDescriptors(function(error, descriptors) {
                      async.detect(
                        descriptors,
                        function(descriptor, callback) {
                          return callback(descriptor.uuid === '2901');
                        },
                        function(userDescriptionDescriptor){
                          if (userDescriptionDescriptor) {
                            userDescriptionDescriptor.readValue(function(error, data) {
                              if (data) {
                                characteristicInfo += ' (' + data.toString() + ')';
                              }
                              callback();
                            });
                          } else {
                            callback();
                          }
                        }
                      );
                    });
                  },
                  function(callback) {
                        characteristicInfo += '\n    properties  ' + characteristic.properties.join(', ');

                    if (characteristic.properties.indexOf('read') !== -1) {
                      characteristic.read(function(error, data) {
                        if (data) {
                          var string = data.toString('ascii');

                          characteristicInfo += '\n    value       ' + data.toString('hex') + ' | \'' + string + '\'';
                        }
                        callback();
                      });
                    } else {
                      callback();
                    }
                  },
                  function() {
                    console.log(characteristicInfo);
                    characteristicIndex++;
                    callback();
                  }
                ]);
              },
              function(error) {
                serviceIndex++;
                callback();
              }
            );
          });
        },
        function (err) {
          peripheral.disconnect();
        }
      );
    });
  });
}

