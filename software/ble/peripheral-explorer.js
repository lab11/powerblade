var async = require('async');
var noble = require('../index');

//XXX: Replace COLONS!
//var peripheralUuid = process.argv[2];
//peripheralUuid = peripheralUuid.replace(':', '');
//peripheralUuid = peripheralUuid.toLowerCase();
var peripheralUuid = 'e12b8ee3b640';


noble.on('stateChange', function(state) {
  if (state === 'poweredOn') {
    console.log("Starting scan...");
    noble.startScanning([], true);
  } else {
    noble.stopScanning();
  }
});

noble.on('discover', function(peripheral) {
  //console.log("Peripheral found: UUID " + peripheral.uuid);
  if (peripheral.uuid === peripheralUuid) {

    //console.log('Found peripheral: UUID ' + peripheralUuid + ' found');
    var advertisement = peripheral.advertisement;
    //console.log('  Advertising Data = ' + JSON.stringify(advertisement, null, 0));

    // get data after the manufacturer ID
    var data = advertisement.manufacturerData.slice(2);

    // get data values from the powerblade
    var sequence_num = data.slice(0,4);
    var time = data.slice(4,8);
    var v_rms = data.slice(8,9);
    var true_power = data.slice(9,11);
    var apparent_power = data.slice(11,13);
    var watt_hours = data.slice(13,17);

    // print to user
    console.log('Data:');
    console.log('       Sequence Number: ' + sequence_num +   ' (0x' + sequence_num.toString('hex') = ')');
    console.log('                  Time: ' + time +           ' (0x' + time.toString('hex') = ')');
    console.log('           RMS Voltage: ' + v_rms +          ' (0x' + v_rms.toString('hex') = ')');
    console.log('    Current True Power: ' + true_power +     ' (0x' + true_power.toString('hex') = ')');
    console.log('Current Apparent Power: ' + apparent_power + ' (0x' + apparent_power.toString('hex') = ')');
    console.log(' Cumulative Watt Hours: ' + watt_hours +     ' (0x' + watt_hours.toString('hex') = ')');

    console.log('');
  }
});

// lists all services, characteristics, and values when connected
function explore(peripheral) {
  console.log('services and characteristics:');

  peripheral.on('disconnect', function() {
    process.exit(0);
  });

  peripheral.connect(function(error) {
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
          console.log(serviceInfo);

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

