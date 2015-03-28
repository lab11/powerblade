var async = require('async');
var noble = require('noble');
var BitArray = require('node-bitarray');

// mangled version of 0x4908
var CompanyID = 37392;

var peripherals = {};

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
    var ippk_10s = BitArray.fromBuffer(data.slice(1,5)).toNumber();
    var ippk_1s  = BitArray.fromBuffer(data.slice(5,9)).toNumber();
    var flags = BitArray.fromBuffer(data.slice(18,19)).toNumber();
    var num_connections = BitArray.fromBuffer(data.slice(19,20)).toNumber();

    console.log('Data: ' + recv_time);
    console.log('         BLE Address: ' + peripheral_uuid);
    console.log('       PowerBlade ID: ' + '0x' + powerblade_id.toString(16));
    console.log('I Peak-to-Peak (10s): ' + ippk_10s + ' (0x' + ippk_10s.toString(16) + ')');
    console.log('I Peak-to-Peak  (1s): ' + ippk_1s + ' (0x' + ippk_1s.toString(16) + ')');
    console.log('               Flags: ' + '0x' + flags.toString(16));
    //console.log(' Number of Connections: ' + num_connections);

      console.log('');

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

