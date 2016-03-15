#! /usr/bin/env node

// Collect BLE packets over MQTT
//  Push to SQL for storage

var debug = require('debug')('gateway-mqtt-sql');
var watchout = require('watchout');
var request = require('request');
var fs = require('fs');
var ini = require('ini');

// discover the local MQTT broker
var MQTTDiscover = require('mqtt-discover');
MQTTDiscover.start();
var MQTT_DATA_TOPIC = 'gateway-data';

// configuration
try {
    var config_file = fs.readFileSync('/etc/swarm-gateway/powerblade-sql.conf', 'utf-8');
    var config = ini.parse(config_file);
    if (config.post_url == undefined || config.post_url == '') {
        throw new Exception("No GATD HTTP POST Receiver URL");
    }
} catch (e) {
    console.log(e);
    console.log("\nCannot find /etc/swarm-gateway/gatd.conf or configuration invalid.");
    process.exit(1);
}

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
var post_count = 0;
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
        log_to_sql(adv);
        if(post_count == 0) {      // Mark the start time of the first packet in this file
            file_start_time = curr_time;
        }
        post_count += 1;
		
		// if enough packets have been logged, push to SQL
        if(post_count >= UPLOAD_COUNT || (curr_time - file_start_time) >= FILE_TIMEOUT) {
		  post_to_sql();
        }
    });
});

// Log csv-formatted advertisements to a temp file
var powerblade_count = 0;
function log_to_sql (adv) {


    console.log(adv['device']);
}

function post_to_sql () {
    console.log("Post");
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

