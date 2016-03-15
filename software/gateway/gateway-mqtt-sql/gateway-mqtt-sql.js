#! /usr/bin/env node

// Collect BLE packets over MQTT
//  Push to SQL for storage

var debug = require('debug')('gateway-mqtt-sql');
var watchout = require('watchout');
var request = require('request');
var fs = require('fs');
var ini = require('ini');
var mysql = require('mysql');

// discover the local MQTT broker
var MQTTDiscover = require('mqtt-discover');
MQTTDiscover.start();
var MQTT_DATA_TOPIC = 'gateway-data';

// configuration
try {
    var config_file = fs.readFileSync('/etc/swarm-gateway/powerblade-sql.conf', 'utf-8');
    var config = ini.parse(config_file);
    // if (config.post_url == undefined || config.post_url == '') {
    //     throw new Exception("No GATD HTTP POST Receiver URL");
    // }
} catch (e) {
    console.log(e);
    console.log("\nCannot find /etc/swarm-gateway/powerblade-sql.conf or configuration invalid.");
    process.exit(1);
}

// This is used for re-directing the flow during an upload
var pb_csv_current = config.pb_csv0;
var bl_csv_current = config.bl_csv0;

// Erase the temporary files
fs.writeFile(config.pb_csv0, '', function (err) {
    if (err) throw err;
});
fs.writeFile(config.pb_csv1, '', function (err) {
    if (err) throw err;
});
fs.writeFile(config.bl_csv0, '', function (err) {
    if (err) throw err;
});
fs.writeFile(config.bl_csv1, '', function (err) {
    if (err) throw err;
});

var connection = mysql.createConnection({
  host     : config.sql_ip,
  user     : config.sql_usr,
  password : config.sql_pw,
  database : config.sql_db
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
var powerblade_count = 0;
var blees_count = 0;
var UPLOAD_COUNT = 1000;
var file_start_time = 0;
var FILE_TIMEOUT = 30;
MQTTDiscover.on('mqttBroker', function (mqtt_client) {
    console.log("Connected to MQTT broker: " + mqtt_client.options.host);

    // subscribe to powerblade data
    mqtt_client.subscribe(MQTT_DATA_TOPIC);
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
        if(powerblade_count == 0 && blees_count == 0) {      // Mark the start time of the first packet in this file
            file_start_time = curr_time;
        }
        log_to_sql(adv);
		
		// if enough packets have been logged, push to SQL
        if((powerblade_count + blees_count) >= UPLOAD_COUNT || (curr_time - file_start_time) >= FILE_TIMEOUT) {
            post_to_sql();
        }
    });
});

// Log csv-formatted advertisements to a temp file
function log_to_sql (adv) {

    var timestamp = adv['_meta']['received_time'].split('T');
    timestamp[1] = timestamp[1].slice(0,-1);
    datetime = timestamp[0] + ' ' + timestamp[1];

    var gatewayID = adv['_meta']['gateway_id'].replace(new RegExp(':', 'g'), '');

    //console.log(adv['device']);
    if(adv['device'] == "PowerBlade") {
        powerblade_count += 1;
        fs.appendFile(pb_csv_current, 
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
        blees_count += 1;
        fs.appendFile(bl_csv_current, 
            gatewayID + ',' +
            adv['id'] + ',' +
            adv['temperature_celcius'] + ',' +
            adv['light_lux'] + ',' +
            adv['pressure_pascals'] + ',' +
            adv['humidity_percent'] + ',' +
            adv['acceleration_advertisement'] + ',' +
            adv['acceleration_interval'] + ',' +
            datetime + '\n', 
            encoding='utf8', 
            function (err) {
            if (err) throw err;
        });
    }
}

function post_to_sql () {
    if(powerblade_count > 0) {
        powerblade_count = 0;

        // Switch log files (save current log)
        var pb_csv = pb_csv_current;
        if(pb_csv_current == config.pb_csv0) {
            pb_csv_current = config.pb_csv1;
        }
        else {
            pb_csv_current = config.pb_csv0;   
        }

        // Batch upload to SQL
        var loadQuery = 'LOAD DATA LOCAL INFILE \'' + pb_csv + '\' INTO TABLE powerblade_test FIELDS TERMINATED BY \',\';';
        console.log(loadQuery)

        connection.query(loadQuery, function(err, rows, fields) {
            if (err) throw err;
            console.log('Done writing to PowerBlade');

            // Erase the PowerBlade temp file
            console.log('Erasing PowerBlade');
            fs.writeFile(pb_csv, '', function (err) {
                if (err) throw err;
                console.log('Done erasing PowerBlade');
            });
        });
    }

    if(blees_count > 0) {
        blees_count = 0;

        var bl_csv = bl_csv_current;
        if(bl_csv_current == config.bl_csv0) {
            bl_csv_current = config.bl_csv1;
        }
        else {
            bl_csv_current = config.bl_csv0;   
        }

        var loadQuery = 'LOAD DATA LOCAL INFILE \'' + bl_csv + '\' INTO TABLE blees_test FIELDS TERMINATED BY \',\';';
        console.log(loadQuery)
        
        connection.query(loadQuery, function(err, rows, fields) {
            if (err) throw err;
            console.log('Done writing to BLEES');

            // Erase the BLEES temp file
            console.log('Erasing BLEES');
            fs.writeFile(bl_csv, '', function (err) {
                if (err) throw err;
                console.log('Done erasing BLEES');
            });
        });
    }
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

