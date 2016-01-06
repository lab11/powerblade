
// {BLE Address: Most recent sequence number} for each PowerBlade
var powerblade_sequences = {};

var parse_advertisement = function (advertisement, cb) {

    var data = advertisement.manufacturerData.slice(2);
    var recv_time = (new Date).getTime()/1000;

    // check length of data
    if (data.length < 19) {
        // console.log("ERROR: Bad PowerBlade packet");
        cb(null);
    }

    // check software version number
    var version_num = data.readUIntBE(0,1);
    if (version_num < 1) {
        // console.log("ERROR: PowerBlade version 0 discovered!");
        cb(null);
    }

    // check for duplicate advertisements
    var sequence_num = data.readUIntBE(1,4);
    // if (!(address in powerblade_sequences)) {
    //     powerblade_sequences[address] = -1;
    // }
    // if (powerblade_sequences[address] == sequence_num) {
    //     // duplicate advertisement. Don't display
    //     cb(null);
    // }
    // powerblade_sequences[address] = sequence_num;

    // parse fields from advertisement
    var pscale = data.readUIntBE(5,2);
    var vscale =  data.readUIntBE(7,1);
    var whscale = data.readUIntBE(8,1);
    var v_rms = data.readUIntBE(9,1);
    var real_power = data.readUIntBE(10,2);
    var apparent_power = data.readUIntBE(12,2);
    var watt_hours = data.readUIntBE(14,4);
    var flags = data.readUIntBE(18,1);

    // calculate scaling values
    var volt_scale = vscale / 50;
    var power_scale = (pscale & 0x0FFF) * Math.pow(10,-1*((pscale & 0xF000) >> 12));
    var wh_shift = whscale;

    // scale measurements from PowerBlade
    var v_rms_disp = v_rms*volt_scale;
    var real_power_disp = real_power*power_scale;
    var app_power_disp = apparent_power*power_scale;
    if(volt_scale > 0) {
      var watt_hours_disp = (watt_hours << wh_shift)*(power_scale/3600);
    } else {
      var watt_hours_disp = watt_hours;
    }

    // Exponential subtraction
    // 6.6 and 0.015 are hard coded for PB version 1
    // PB version 2 and greater will transmit device-specific values with each packet
    // real_power_disp = real_power_disp - 6.6*Math.exp(-0.015*real_power_disp)

    var pf_disp = real_power_disp / app_power_disp;

    var out = {
        device: 'PowerBlade',
        sequence_number: sequence_num,
        rms_voltage: v_rms_disp.toFixed(2),
        power: real_power_disp.toFixed(2),
        apparent_power: app_power_disp.toFixed(2),
        energy: watt_hours_disp.toFixed(2),
        power_factor: pf_disp.toFixed(2)
    }

    // // display data to user
    // console.log('PowerBlade (' + address +')');
    // console.log('      Sequence Number: ' + sequence_num);
    // console.log('          RMS Voltage: ' + v_rms_disp.toFixed(2) + ' V');
    // console.log('           Real Power: ' + real_power_disp.toFixed(2) + ' W');
    // console.log('       Apparent Power: ' + app_power_disp.toFixed(2) + ' VA');
    // console.log('Cumulative Energy Use: ' + watt_hours_disp.toFixed(2) + ' Wh');
    // console.log('         Power Factor: ' + pf_disp.toFixed(2));
    // console.log('');

    cb(out);
}


module.exports = {
    parseAdvertisement: parse_advertisement
};
