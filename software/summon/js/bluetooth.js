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
  translate_advertisement = function (peripheral, success) {
    var advertising = peripheral.advertising;

    // common advertisement interface is created as a new field
    //  This format follows the nodejs BLE library, noble
    //  https://github.com/sandeepmistry/noble#peripheral-discovered
    peripheral.advertisement = {
      localName: undefined,
      txPowerLevel: undefined,
      manufacturerData: undefined,
      serviceData: [],
      serviceUuids: [],
    };

    // special fields that only exist on one OS or another are listed here
    peripheral._os_dependent = {};

    // this is a hack and only has to be in place until this code gets pulled
    //  into the summon app. Since we use the same hack to decide which
    //  cordova.js to load, it seems pretty saft to use it here too
    if (navigator.platform.startsWith("iP")) {

      // we are on iOS (iPad, iPod, iPhone)
      peripheral._os_dependent.os = 'ios';
      peripheral._os_dependent.channel = advertising.kCBAdvDataChannel;
      peripheral._os_dependent.isConnectable = advertising.kCBAdvDataIsConnectable;

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

      //XXX: loook at this
      if (advertising.kCBAdvDataServiceUUIDs) {
        for(i = 0; i < advertising.kCBAdvDataServiceUUIDs.length; i++) {
          peripheral.advertisement.serviceUuids.push(advertising.kCBAdvDataServiceUUIDs[i]);
        }
      }

    } else { // Android
      //XXX: change a lot of these to slices to cut up the actual ArrayBuffer
      peripheral._os_dependent.os = 'android';
      var scanRecord = new Uint8Array(advertising);
      var index = 0;
      while (index < scanRecord.length) {
        var length = scanRecord[index++];
        if (length == 0) break; // Done once we run out of records
        var type = scanRecord[index];
        if (type == 0) break; // Done if our record isn't a valid type
        var data = scanRecord.subarray(index+1, index+length); 
        switch (type) {
          case 0x01: // Flags
            peripheral._os_dependent.flags = data[0] & 0xFF;
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
              data: data.subarray(2),
            });
            break;
          case 0xFF: // Manufacturer Specific Data
            peripheral.advertisement.manufacturerData = data;
            break;
        }
        index += length; //Advance
      }
    }
    success(peripheral);
  };

  //XXX: This needs to be tested on 32-bit and 128-bit UUIDs
  uuid = function(id) {
    if (id.length <= 4) {
      return hex(id.slice().reverse());
    } else if (id.length == 16) {
      return hex(id.subarray(0,4))+"-"+hex(id.subarray(4,6))+"-"+hex(id.subarray(6,8))+"-"+hex(id.subarray(8,10))+"-"+hex(id.subarray(10,16));
    } else {
      return "";
    }
  };

  hex = function(ab) {
    return Array.prototype.map.call(ab,function(m){return ("0"+m.toString(16)).substr(-2);}).join('').toUpperCase();
  };

});
