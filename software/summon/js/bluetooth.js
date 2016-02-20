/* vim: set sw=2 expandtab tw=80: */
var bluetooth = {};

document.addEventListener("deviceready", function () {

  bluetooth = Object.assign({}, ble);

  bluetooth.scan = function(services, seconds, success, failure) {
    ble.scan(services, seconds, function (peripheral) {
      translate_advertisement(peripheral, success);
    }, failure);
  };

  bluetooth.startScan = function(services, success, failure) {
    ble.startScan(services, function (peripheral) {
      translate_advertisement(peripheral, success);
    }, failure);
  };

  // create a common advertisement interface between iOS and android
  //  This format follows the nodejs BLE library, noble
  //  https://github.com/sandeepmistry/noble#peripheral-discovered
  translate_advertisement = function (peripheral, success) {
    var advertising = peripheral.advertising;

    // common advertisement interface is created as a new field
    //  This format follows the nodejs BLE library, noble
    //  https://github.com/sandeepmistry/noble#peripheral-discovered
    peripheral.advertisement = {
      localName: undefined,
      txPowerLevel: undefined,
      manufacturerData: undefined,
      channel: undefined,   // ios only
      flags: undefined,     // android only
      serviceData: [],
      serviceUuids: [],
    };

    // this is a hack and only has to be in place until this code gets pulled
    //  into the summon app. Since we use the same hack to decide which
    //  cordova.js to load, it seems pretty saft to use it here too
    if (navigator.platform.startsWith("iP")) {

      // we are on iOS (iPad, iPod, iPhone)
      peripheral.advertisement.channel = advertising.kCBAdvDataChannel;
      peripheral.isConnectable = advertising.kCBAdvDataIsConnectable;

      // directly copy fields as long as they exist
      if (advertising.kCBAdvDataLocalName) {
        peripheral.advertisement.localName = advertising.kCBAdvDataLocalName;
      }
      if (advertising.kCBAdvDataTxPowerLevel) {
        peripheral.advertisement.txPowerLevel = advertising.kCBAdvDataTxPowerLevel;
      }
      if (advertising.kCBAdvDataManufacturerData) {
        peripheral.advertisement.manufacturerData = new Uint8Array(advertising.kCBAdvDataManufacturerData);
      }
      if (advertising.kCBAdvDataServiceUUIDs) {
        peripheral.advertisement.serviceUuids = advertising.kCBAdvDataServiceUUIDs;
      }

      // format for service data is different
      var serviceData = advertising.kCBAdvDataServiceData;
      if (serviceData) {
        for (var serviceDataUuid in serviceData) {
          peripheral.advertisement.serviceData.push({
            uuid: serviceDataUuid,
            data: new Uint8Array(serviceData[serviceDataUuid]),
          });
        }
      }

    } else {
      // we are on android
      //XXX: can we determine `connectable` on android?
      var scanRecord = new Uint8Array(advertising);
      var index = 0;
      while (index < scanRecord.length) {
        // first is length of the field, length of zero indicates advertisement
        //  is complete
        var length = scanRecord[index++];
        if (length == 0) {
          break;
        }

        // next is type of field and then field data (if any)
        var type = scanRecord[index];
        var data = scanRecord.subarray(index+1, index+length);

        // determine data based on field type
        switch (type) {
          case 0x01: // Flags
            peripheral.advertisement.flags = data[0] & 0xFF;
            break;

          case 0x02: // Incomplete List of 16-Bit Service UUIDs
          case 0x03: // Complete List of 16-Bit Service UUIDs
            for (var n=0; n<data.length; n+=2) {
              peripheral.advertisement.serviceUuids.push(uuid(data.subarray(n,n+2)));
            }
            break;

          case 0x04: // Incomplete List of 32-Bit Service UUIDs
          case 0x05: // Complete List of 32-Bit Service UUIDs
            for (var n=0; n<data.length; n+=4) {
              peripheral.advertisement.serviceUuids.push(uuid(data.subarray(n,n+4)));
            }
            break;

          case 0x06: // Incomplete List of 128-Bit Service UUIDs
          case 0x07: // Complete List of 128-Bit Service UUIDs
            for (var n=0; n<data.length; n+=16) {
              peripheral.advertisement.serviceUuids.push(uuid(data.subarray(n,n+16)));
            }
            break;

          case 0x08: // Short Local Name
          case 0x09: // Complete Local Name
            peripheral.advertisement.localName = String.fromCharCode.apply(null,data);
            break;

          case 0x0A: // TX Power Level
            peripheral.advertisement.txPowerLevel = data[0] & 0xFF;
            break;

          case 0x16: // Service Data
            peripheral.advertisement.serviceData.push({
              uuid: uuid(data.subarray(0,2)),
              data: new Uint8Array(data.subarray(2)),
            });
            break;

          case 0xFF: // Manufacturer Specific Data
            peripheral.advertisement.manufacturerData = new Uint8Array(data);
            break;
        }

        // move to next advertisement field
        index += length;
      }
    }

    // finished parsing, call originally intended callback
    success(peripheral);
  };

  //XXX: This needs to be tested!!
  // convert an array of bytes representing a UUID into a hex string
  //    Note that all arrays need to be reversed before presenting to the user
  uuid = function (id) {
    if (id.length == 2) {
      return hex(id[1]) + hex(id[0]);

    } else if (id.length <= 4) {
      return hex(id[3]) + hex(id[2]) + hex(id[1]) + hex(id[0]);

    } else if (id.length == 16) {
      return hex(id[15]) + hex(id[14]) + hex(id[13]) + hex(id[12]) + '-' +
             hex(id[11]) + hex(id[10]) + '-' +
             hex(id[9])  + hex(id[8])  + '-' +
             hex(id[7])  + hex(id[6])  + '-' +
             hex(id[5])  + hex(id[4])  + hex(id[3])  + hex(id[2])  + hex(id[1])  + hex(id[0]);

    } else {
      // invalid number of bytes
      return "";
    }
  };

  // convert an array of bytes into hex data
  hex = function (ab) {
    return Array.prototype.map.call(ab, function (m) {
      return ("0"+m.toString(16)).substr(-2);
    }).join('').toUpperCase();
  };

});
