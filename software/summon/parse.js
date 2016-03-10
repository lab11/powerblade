
// {BLE Address: Most recent sequence number} for each PowerBlade
var powerblade_sequences = {};
var powerblade_last_seens = {};
var cleanup_timer = null;
var CLEANUP_INTERVAL = 12*60*60*1000;

var OLD_COMPANY_ID = 0x4908;

var parse_advertisement = function (advertisement, cb) {

    // add an interval timer for cleanup of old powerblades
    if (cleanup_timer == null) {
        cleanup_timer = setInterval(cleanup_powerblades, CLEANUP_INTERVAL);
    }

    // check for a valid advertisement packet
    if (advertisement.manufacturerData) {
        if (advertisement.manufacturerData.length >= 19) {

            var company_id = advertisement.manufacturerData.readUIntLE(0,2);
            var data = advertisement.manufacturerData.slice(3);
            if (company_id == OLD_COMPANY_ID) {
                // allow backwards compatibility with old powerblade format
                data = advertisement.manufacturerData.slice(2);
            }
            var recv_time = (new Date).getTime()/1000;

            // check software version number
            var version_num = data.readUIntBE(0,1);
            if (version_num >= 1) {

                // check for duplicate advertisements
                var address = advertisement.address;
                var sequence_num = data.readUIntBE(1,4);
                if (!(address in powerblade_sequences)) {
                    powerblade_sequences[address] = -1;
                    powerblade_last_seens[address] = -1;
                }
                if (powerblade_sequences[address] == sequence_num) {
                    // duplicate advertisement. Don't display
                    cb(null);
                    return;
                }
                powerblade_sequences[address] = sequence_num;
                powerblade_last_seens[address] = recv_time;

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
                var volt_scale;
                if (version_num == 1) {
                    volt_scale = vscale / 50;
                } else {
                    // starting in version 2, vscale became bigger to allow for more
                    //  precision in v_rms
                    volt_scale = vscale / 200;
                }
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

                cb(out);
                return;
            }
        }
    }

    cb(null);
}

var cleanup_powerblades = function () {
    var curr_time = (new Date).getTime()/1000;

    // search for devices that are old and remove them
    for (powerblade in powerblade_last_seens) {
        if ((curr_time - powerblade_last_seens) > 10) {
            delete powerblade_sequences[powerblade];
            delete powerblade_last_seens[powerblade];
        }
    }
}

module.exports = {
    parseAdvertisement: parse_advertisement
};
