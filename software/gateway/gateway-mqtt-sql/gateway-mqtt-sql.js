#! /usr/bin/env node

// Collect BLE packets over MQTT
//  Push to SQL for storage

var debug = require('debug')('gateway-mqtt-sql');
var watchout = require('watchout');
var request = require('request');
var fs = require('fs');
var ini = require('ini');
var mysql = require('mysql');
var getmac = require('getmac');

// connect to the local MQTT broker
var mqtt = require('mqtt');
// TODO this should be in a config - this list determines which data streams are subscribed to
var topic_list = [
['device/PowerBlade/+', 'dat_powerblade'],
['device/BLEES/+', 'dat_blees'],
['device/Coilcube/+', 'dat_coilcube'],
['device/Solar Monjolo/+', 'dat_monjolo'],
['device/Triumvi/+', 'dat_triumvi'],
['device/Blink/+', 'dat_blink']//,
//['ble-advertisements', 'dat_rssi']
];
//var MQTT_DATA_TOPIC = 'gateway-data';
//var MQTT_RSSI_TOPIC = 'ble-advertisements'

var field_list = {
'PowerBlade': '(gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, timestamp)',
'BLEES': '(gatewayMAC, deviceMAC, temp, lux, pascals, humid, accel_ad, accel_int, timestamp)',
'Coilcube': '(gatewayMAC, deviceMAC, seq, count, timestamp)',
'Solar Monjolo': '(gatewayMAC, deviceMAC, seq, count, timestamp)',
'Triumvi': '(gatewayMAC, deviceMAC, power, timestamp)',
'Blink': '(gatewayMAC, deviceMAC, curMot, advMot, minMot, timestamp)',
'ble-advertisements': '(gatewayMAC, deviceMAC, rssi, timestamp)'
}

var debug = 0;
var test = 0;
process.argv.forEach(function (val, index, array) {
    if(val == "-d" || val == "--debug") {
        debug = 1;
        console.log("Running with verbose output");
    }
    else if(val == "-t" || val == "--test") {
        test = 1;
        console.log("Running with testbed database");
    }
});

function sumTopicList() {
    var sum = 0;
    for(var key in topic_data) {
        sum += topic_data[key][3];
    }
    return sum;
}

// configuration
try {
    // var config_file = fs.readFileSync('/etc/swarm-gateway/powerblade-sql.conf', 'utf-8');
    // var config = ini.parse(config_file);
    var aws_config_file = fs.readFileSync('/etc/swarm-gateway/powerblade-aws.conf', 'utf-8');
    var aws_config = ini.parse(aws_config_file);
    // if (config.post_url == undefined || config.post_url == '') {
    //     throw new Exception("No GATD HTTP POST Receiver URL");
    // }
} catch (e) {
    console.log(e);
    console.log("\nCannot find /etc/swarm-gateway/powerblade-aws.conf or configuration invalid.");
    process.exit(1);
}

// Process topic list, create temp files, zero counts
var topic_data = {};
var topic_counts = [];
topic_list.forEach(function(value) {
    // Get device name, if available
    var dev_list = value[0].split('/');
    if(dev_list.length > 1) {
        var dev_name = dev_list[1];
    }
    else {
        var dev_name = dev_list;
    }

    // Set up two temporary files
    temp_files = [];
    for(var i = 0; i <= 1; i++) {
        var filename = '/tmp/' + dev_name + i + '.csv';
        // Erase existing data
        fs.writeFile(filename, '', function (err) {
            if (err) throw err;
        });
        temp_files.push(filename);
    }

    // Add table name and initialize count to zero
    temp_files.push(value[1]);
    temp_files.push(0);

    // Save to topic_data
    topic_data[dev_name] = temp_files;
});

var file_current = 0;

// This is used for re-directing the flow during an upload
// var pb_csv_current = config.pb_csv0;
// var bl_csv_current = config.bl_csv0;
// var cc_csv_current = config.cc_csv0;
// var rssi_csv_current = config.rssi_csv0;
// var tv_csv_current = config.tv_csv0;
// var pir_csv_current = config.pir_csv0;

// Erase the temporary files
// fs.writeFile(config.pb_csv0, '', function (err) {
//     if (err) throw err;
// });
// fs.writeFile(config.pb_csv1, '', function (err) {
//     if (err) throw err;
// });
// fs.writeFile(config.bl_csv0, '', function (err) {
//     if (err) throw err;
// });
// fs.writeFile(config.bl_csv1, '', function (err) {
//     if (err) throw err;
// });
// fs.writeFile(config.cc_csv0, '', function (err) {
//     if (err) throw err;
// });
// fs.writeFile(config.cc_csv1, '', function (err) {
//     if (err) throw err;
// });
// fs.writeFile(config.rssi_csv0, '', function (err) {
//     if (err) throw err;
// });
// fs.writeFile(config.rssi_csv1, '', function (err) {
//     if (err) throw err;
// });
// fs.writeFile(config.tv_csv0, '', function (err) {
//     if (err) throw err;
// });
// fs.writeFile(config.tv_csv1, '', function (err) {
//     if (err) throw err;
// });
// fs.writeFile(config.pir_csv0, '', function (err) {
//     if (err) throw err;
// });
// fs.writeFile(config.pir_csv1, '', function (err) {
//     if (err) throw err;
// });

/*
var connection = mysql.createConnection({
  host     : config.sql_ip,
  user     : config.sql_usr,
  password : config.sql_pw,
  database : config.sql_db
});
*/
if(test == 0) {
    console.log("Connecting to " + aws_config.sql_ip);
    var db_connection = mysql.createConnection({
      host     : aws_config.sql_ip,
      user     : aws_config.sql_usr,
      password : aws_config.sql_pw,
      database : aws_config.sql_db
    });
}
else {
    console.log("Connecting to " + aws_config.test_ip);
    var db_connection = mysql.createConnection({
      host     : aws_config.test_ip,
      user     : aws_config.test_usr,
      password : aws_config.test_pw,
      database : aws_config.test_db
    }); 
}

var gateway_mac;
getmac.getMac(function(err,macAddress) {
    if (err) throw err;
    gateway_mac = macAddress.replace(new RegExp(':', 'g'), '');
});

// settings
var POST_BUFFER_LEN = 4; // group N packets into a single post
var POST_TIMEOUT = 30; // after 30 seconds, just post anyway

// add a watchdog for mqtt packets
mqtt_down = false;
var mqtt_watchdog = new watchout(1*60*1000, function(didCancelWatchdog) {
    if (didCancelWatchdog) {
        // benign
    } else {
        console.log("MQTT watchdog tripped");
        mqtt_down = true;
        process.exit(1);
    }
});

// connect to MQTT broker
// var powerblade_count = 0;
// var blees_count = 0;
// var coilcube_count = 0;
// var rssi_count = 0;
// var triumvi_count = 0;
// var blink_count = 0;

var UPLOAD_COUNT = 5000;
var file_start_time = 0;
var FILE_TIMEOUT = 30;

var mqtt_client = mqtt.connect('mqtt://localhost');

mqtt_client.on('connect', function () {
    console.log("Connected to MQTT");

    // subscribe to powerblade data
    topic_list.forEach(function(value) {
        mqtt_client.subscribe(value[0]);
    });
    // mqtt_client.subscribe(MQTT_DATA_TOPIC);
    // mqtt_client.subscribe(MQTT_RSSI_TOPIC);
    mqtt_client.on('message', function (topic, message) {
        var adv = JSON.parse(message.toString());

        // got a packet, reset watchdog
        mqtt_watchdog.reset();
        if (mqtt_down) {
            console.log("Getting packets again");
            mqtt_down = false;
        }

        // log packets in SQL format
        var curr_time = Date.now()/1000;

        //var topic_sum = topic_counts.reduce(function(total, num) {return total + num}, 0);
        var topic_sum = sumTopicList();
        if(topic_sum == 0) {// Mark the start time of the first packet in this file
        //if(powerblade_count == 0 && blees_count == 0 && coilcube_count == 0 && rssi_count == 0 && triumvi_count == 0 && blink_count == 0) {      // Mark the start time of the first packet in this file
            file_start_time = curr_time;
        }
        log_to_sql(topic, adv);
		
		// if enough packets have been logged, push to SQL
        if(topic_sum >= UPLOAD_COUNT || (curr_time - file_start_time) >= FILE_TIMEOUT) {
        //if((powerblade_count + blees_count + coilcube_count + rssi_count + triumvi_count + blink_count) >= UPLOAD_COUNT || (curr_time - file_start_time) >= FILE_TIMEOUT) {
            post_to_sql();
        }
    });
});

// Log csv-formatted advertisements to a temp file
// TODO this function is hard coded and clunky
// It might make sense to try to the the parse.js files
function log_to_sql (topic, adv) {

    if(topic == 'ble-advertisements') {
        var timestamp = adv['receivedTime'].split('T');
        timestamp[1] = timestamp[1].slice(0,-1);
        datetime = timestamp[0] + ' ' + timestamp[1];

        //rssi_count += 1;
        topic_data['ble-advertisements'][3] += 1;
        //fs.appendFile(rssi_csv_current,
        fs.appendFile(topic_data['ble-advertisements'][file_current],
            gateway_mac + ',' + 
            adv['address'] + ',' + 
            adv['rssi'] + ',' + 
            datetime + '\n',
            encoding='utf8',
            function (err) {
            if (err) throw err;
        });
    }
    else {
    //if(topic == MQTT_DATA_TOPIC) {
        var timestamp = adv['_meta']['received_time'].split('T');
        timestamp[1] = timestamp[1].slice(0,-1);
        datetime = timestamp[0] + ' ' + timestamp[1];

        var gatewayID = adv['_meta']['gateway_id'].replace(new RegExp(':', 'g'), '');

        //console.log(adv['device']);
        if(adv['device'] == "PowerBlade") {
            //powerblade_count += 1;
            topic_data['PowerBlade'][3] += 1;
            //fs.appendFile(pb_csv_current, 
            fs.appendFile(topic_data['PowerBlade'][file_current],
                gatewayID + ',' +
                adv['id'] + ',' +
                adv['sequence_number'] + ',' +
                adv['rms_voltage'] + ',' + 
                adv['power'] + ',' +
                adv['energy'] + ',' +
                adv['power_factor'] + ',' +
                datetime + '\n',
                encoding='utf8', 
                function (err) {
                if (err) throw err;
            });
        }
        else if(adv['device'] == "BLEES"){
            //blees_count += 1;
            topic_data['BLEES'][3] += 1;
            //fs.appendFile(bl_csv_current, 
            fs.appendFile(topic_data['BLEES'][file_current],
                gatewayID + ',' +
                adv['id'] + ',' +
                adv['temperature_celcius'] + ',' +
                adv['light_lux'] + ',' +
                adv['pressure_pascals'] + ',' +
                adv['humidity_percent'] + ',' +
                (adv['acceleration_advertisement']+0) + ',' +
                (adv['acceleration_interval']+0) + ',' +
                datetime + '\n', 
                encoding='utf8', 
                function (err) {
                if (err) throw err;
            });
        }
        else if(adv['device'].slice(0,8) == "Coilcube" || adv['device'] == "Solar Monjolo") {
            //coilcube_count += 1;
            topic_data['Coilcube'][3] += 1;
            //fs.appendFile(cc_csv_current,
            fs.appendFile(topic_data['Coilcube'][file_current],
                gatewayID + ',' +
                adv['_meta']['device_id'] + ',' + 
                adv['seq_no'] + ',' + 
                adv['counter'] + ',' +
                datetime + '\n',
                encoding='utf8',
                function (err) {
                if (err) throw err;
            });
        }
        else if(adv['device'] == "Triumvi") {
            //triumvi_count += 1;
            topic_data['Triumvi'][3] += 1;
            //fs.appendFile(tv_csv_current,
            fs.appendFile(topic_data['Triumvi'][file_current],
                gatewayID + ',' +
                adv['_meta']['device_id'] + ',' +
                adv['Power'] + ',' + 
                datetime + '\n',
                encoding='utf8',
                function (err) {
                if (err) throw err;
            });
        }
        else if(adv['device'] == "Blink") {
            //blink_count += 1;
            topic_data['Blink'][3] += 1;
            //fs.appendFile(pir_csv_current,
            fs.appendFile(topic_data['Blink'][file_current],
                gatewayID + ',' +
                adv['_meta']['device_id'] + ',' +
                (adv['current_motion']+0) + ',' +
                (adv['motion_since_last_adv']+0) + ',' +
                (adv['motion_last_minute']+0) + ',' +
                datetime + '\n',
                encoding='utf8',
                function (err) {
                if (err) throw err;
            });
        }
    }
}

function post_to_sql () {
    var count_save = {};
    for(var key in topic_data) {
        count_save[key]= topic_data[key][3];
        topic_data[key][3] = 0;
    }

    // Switch log files
    var file_last = file_current;
    file_current = 1 - file_current;

    // var powerblade_count_save = powerblade_count;
    // powerblade_count = 0;

    // var blees_count_save = blees_count;
    // blees_count = 0;

    // var coilcube_count_save = coilcube_count;
    // coilcube_count = 0;

    // var rssi_count_save = rssi_count;
    // rssi_count = 0;

    // var triumvi_count_save = triumvi_count
    // triumvi_count = 0;

    // var blink_count_save = blink_count;
    // blink_count = 0;

    if(test == 0) {
        var db_name = 'AWS';
    }
    else {
        var db_name = 'Test DB (Girard)';
    }

    var dat_csv = {}
    var dat_table = {}
    for(var key in count_save) {
        if(count_save[key] > 0) {
            dat_csv[key] = topic_data[key][file_last];
            dat_table[key] = topic_data[key][2];
            var loadQuery = 'LOAD DATA LOCAL INFILE \'' + dat_csv[key] + '\' INTO TABLE ' + dat_table[key] + ' FIELDS TERMINATED BY \',\' ' + field_list[key] + ';';
            //console.log(loadQuery);

            console.log('Writing ' + count_save[key] + ' packets to ' + dat_table[key] + ' at ' + db_name)
            db_connection.query(loadQuery, function(err, rows, fields) {
                if (err) throw err;

                // Erase temp file
                console.log('Done writing to ' + dat_table[key] + ' at ' + db_name + ', erasing temp data');
                fs.writeFile(dat_csv[key], '', function (err) {
                    if (err) throw err;
                    console.log('Done erasing ' + dat_table[key] + ' at ' + db_name);
                });
            });
        }
    }

    // if(powerblade_count_save > 0) {
    //     // Switch log files (save current log)
    //     var pb_csv = pb_csv_current;
    //     if(pb_csv_current == config.pb_csv0) {
    //         pb_csv_current = config.pb_csv1;
    //     }
    //     else {
    //         pb_csv_current = config.pb_csv0;   
    //     }

    //     /*
    //     // Batch upload to SQL
    //     var loadQuery = 'LOAD DATA LOCAL INFILE \'' + pb_csv + '\' INTO TABLE powerblade_test FIELDS TERMINATED BY \',\' (gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, timestamp);';
    //     console.log(loadQuery)

    //     connection.query(loadQuery, function(err, rows, fields) {
    //         if (err) throw err;
    //         console.log('Done writing ' + powerblade_count_save + ' packets to PowerBlade in Umich');
    //     });
    //     */

    //     // Batch upload to AWS
    //     var loadQuery = 'LOAD DATA LOCAL INFILE \'' + pb_csv + '\' INTO TABLE dat_powerblade FIELDS TERMINATED BY \',\' (gatewayMAC, deviceMAC, seq, voltage, power, energy, pf, timestamp);';
    //     console.log(loadQuery)

    //     db_connection.query(loadQuery, function(err, rows, fields) {
    //         if (err) throw err;
    //         console.log('Done writing ' + powerblade_count_save + ' packets to PowerBlade in AWS');

    //         // Erase the PowerBlade temp file
    //         console.log('Erasing PowerBlade');
    //         fs.writeFile(pb_csv, '', function (err) {
    //             if (err) throw err;
    //             console.log('Done erasing PowerBlade');
    //         });
    //     });
    // }

    // if(blees_count_save > 0) {
    //     var bl_csv = bl_csv_current;
    //     if(bl_csv_current == config.bl_csv0) {
    //         bl_csv_current = config.bl_csv1;
    //     }
    //     else {
    //         bl_csv_current = config.bl_csv0;   
    //     }

    //     /*
    //     var loadQuery = 'LOAD DATA LOCAL INFILE \'' + bl_csv + '\' INTO TABLE blees_test FIELDS TERMINATED BY \',\' (gatewayMAC, deviceMAC, temp, lux, pascals, humid, accel_ad, accel_int, timestamp);';
    //     console.log(loadQuery)
        
    //     connection.query(loadQuery, function(err, rows, fields) {
    //         if (err) throw err;
    //         console.log('Done writing ' + blees_count_save + ' packets to BLEES in Umich');
    //     });
    //     */

    //     var loadQuery = 'LOAD DATA LOCAL INFILE \'' + bl_csv + '\' INTO TABLE dat_blees FIELDS TERMINATED BY \',\' (gatewayMAC, deviceMAC, temp, lux, pascals, humid, accel_ad, accel_int, timestamp);';
    //     console.log(loadQuery)

    //     db_connection.query(loadQuery, function(err, rows, fields) {
    //         if (err) throw err;
    //         console.log('Done writing ' + blees_count_save + ' packets to BLEES in AWS');

    //         // Erase the BLEES temp file
    //         console.log('Erasing BLEES');
    //         fs.writeFile(bl_csv, '', function (err) {
    //             if (err) throw err;
    //             console.log('Done erasing BLEES');
    //         });
    //     });
    // }

    // if(coilcube_count_save > 0) {
    //     var cc_csv = cc_csv_current;
    //     if(cc_csv_current == config.cc_csv0) {
    //         cc_csv_current = config.cc_csv1;
    //     }
    //     else {
    //         cc_csv_current = config.cc_csv0;
    //     }

    //     /*
    //     var loadQuery = 'LOAD DATA LOCAL INFILE \'' + cc_csv + '\' INTO TABLE coilcube_test FIELDS TERMINATED BY \',\' (gatewayMAC, deviceMAC, seq, count, timestamp);';
    //     console.log(loadQuery);

    //     connection.query(loadQuery, function(err, rows, fields) {
    //         if (err) throw err;
    //         console.log('Done writing ' + coilcube_count_save + ' packets to Coilcube in Umich');
    //     });
    //     */

    //     var loadQuery = 'LOAD DATA LOCAL INFILE \'' + cc_csv + '\' INTO TABLE dat_coilcube FIELDS TERMINATED BY \',\' (gatewayMAC, deviceMAC, seq, count, timestamp);';
    //     console.log(loadQuery);

    //     db_connection.query(loadQuery, function(err, rows, fields) {
    //         if (err) throw err;
    //         console.log('Done writing ' + coilcube_count_save + ' packets to Coilcube in AWS');

    //         // Erase the Coilcube temp file
    //         console.log('Erasing Coilcube');
    //         fs.writeFile(cc_csv, '', function (err) {
    //             if (err) throw err;
    //             console.log('Done erasing Coilcube');
    //         });
    //     });
    // }

    // if(triumvi_count_save > 0) {
    //     var tv_csv = tv_csv_current;
    //     if(tv_csv_current == config.tv_csv0) {
    //         tv_csv_current = config.tv_csv1;
    //     }
    //     else {
    //         tv_csv_current = config.tv_csv0;
    //     }

    //     var loadQuery = 'LOAD DATA LOCAL INFILE \'' + tv_csv + '\' INTO TABLE dat_triumvi FIELDS TERMINATED BY \',\' (gatewayMAC, deviceMAC, power, timestamp);';
    //     console.log(loadQuery);

    //     db_connection.query(loadQuery, function(err, rows, fields) {
    //         if (err) throw err;
    //         console.log('Done writing ' + triumvi_count_save + ' packets to Triumvi in AWS');

    //         // Erase the Triumvi temp file
    //         console.log('Erasing Triumvi');
    //         fs.writeFile(tv_csv, '', function (err) {
    //             if (err) throw err;
    //             console.log('Done erasing Triumvi');
    //         });
    //     });
    // }

    // if(blink_count_save > 0) {
    //     var pir_csv = pir_csv_current;
    //     if(pir_csv_current == config.pir_csv0) {
    //         pir_csv_current = config.pir_csv1;
    //     }
    //     else {
    //         pir_csv_current = config.pir_csv0;
    //     }

    //     var loadQuery = 'LOAD DATA LOCAL INFILE \'' + pir_csv + '\' INTO TABLE dat_blink FIELDS TERMINATED BY \',\' (gatewayMAC, deviceMAC, curMot, advMot, minMot, timestamp);';
    //     console.log(loadQuery);

    //     db_connection.query(loadQuery, function(err, rows, fields) {
    //         if (err) throw err;
    //         console.log('Done writing ' + blink_count_save + ' packets to Blink in AWS');

    //         // Erase the Blink temp file
    //         console.log('Erasing Blink');
    //         fs.writeFile(pir_csv, '', function (err) {
    //             if (err) throw err;
    //             console.log('Done erasing Blink');
    //         });
    //     });
    // }

    // if(rssi_count_save > 0) {
    //     var rssi_csv = rssi_csv_current;
    //     if(rssi_csv_current == config.rssi_csv0) {
    //         rssi_csv_current = config.rssi_csv1;
    //     }
    //     else {
    //         rssi_csv_current = config.rssi_csv0;
    //     }

    //     /*
    //     var loadQuery = 'LOAD DATA LOCAL INFILE \'' + rssi_csv + '\' INTO TABLE rssi_test FIELDS TERMINATED BY \',\' (gatewayMAC, deviceMAC, rssi, timestamp);';
    //     console.log(loadQuery);

    //     connection.query(loadQuery, function(err, rows, fields) {
    //         if (err) throw err;
    //         console.log('Done writing ' + rssi_count_save + ' packets to RSSI in Umich');
    //     });
    //     */

    //     var loadQuery = 'LOAD DATA LOCAL INFILE \'' + rssi_csv + '\' INTO TABLE dat_rssi FIELDS TERMINATED BY \',\' (gatewayMAC, deviceMAC, rssi, timestamp);';
    //     console.log(loadQuery);

    //     db_connection.query(loadQuery, function(err, rows, fields) {
    //         if (err) throw err;
    //         console.log('Done writing ' + rssi_count_save + ' packets to RSSI in AWS');

    //         // Erase RSSI file
    //         console.log('Erasing RSSI');
    //         fs.writeFile(rssi_csv, '', function (err) {
    //             if (err) throw err;
    //             console.log('Done erasing RSSI');
    //         });
    //     });
    // }
}

// post JSON advertisements to GATD
// var post_buffer = [];
// var last_post_time = 0;
// function post_to_gatd (adv) {
//     var curr_time = Date.now()/1000;




    // buffer several advertisements and post the entire list to GATD
    // post_buffer.push(adv);
    // if (post_buffer.length > POST_BUFFER_LEN || (curr_time-last_post_time) > POST_TIMEOUT) {
    //     last_post_time = curr_time;
    //     var buf = post_buffer;
    //     post_buffer = [];

    //     // time to send array
    //     var req = {
    //         url: config.post_url,
    //         method: "POST",
    //         json: buf,
    //     };
    //     request(req, function (error, response, body) {
    //         if (!(error || response.statusCode != 200)) {
    //             // post successful, reset watchdog
    //             gatd_watchdog.reset();
    //             if (gatd_down) {
    //                 console.log("Getting packets again");
    //                 gatd_down = false;
    //             }
    //         }
    //     });
    // }
//}

