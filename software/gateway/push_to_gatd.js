#! /usr/bin/env node

// Collect MQTT packets
//  Check format and possibly append keys
//  Push to GATD for storage

var mqtt = require('mqtt');
var request = require('request');
var moment = require('moment');
var watchout = require('watchout');
try {
    var config = require('./config');
} catch (e) {
    console.log(e);
    console.log("\nCannot find configuration file");
    console.log("\t`ln -s shed/projects/powerblade/<deployment name>/config.js .`");
    process.exit(1);
}

// add a watchdog to notify when no MQTT packets have been received in a while
var watchdog = new watchout(5*60*1000, function(didCancelWatchdog) {
    if (didCancelWatchdog) {
        // benign
    } else {
        console.log(now_str() + "MQTT watchdog tripped");
    }
});

// connect and subscribe to MQTT topic from gateway
var client = mqtt.connect('mqtt://' + config.mqtt.host);
client.on('connect', function () {
    client.subscribe(config.mqtt.topic);
    console.log("Connected and running...");
});

// receive messages and append keys
client.on('message', function (topic, message) {
    // got a packet, reset watchdog
    watchdog.reset();

    // parse into a JSON object
    var adv_obj = JSON.parse(message.toString());

    if (!('meta' in adv_obj)) {
        adv_obj['meta'] = {};
        adv_obj.meta['receiver'] = config.mqtt.host;
        adv_obj.meta['time'] = new Date().toISOString();

        post_to_gatd(adv_obj);
    }
});

// post JSON advertisements to GATD
function post_to_gatd (adv) {
    var req = {
        url: config.gatd.url,
        method: "POST",
        json: JSON.stringify(adv),
    };

    request(req, function (error, response, body) {
        if (error || response.statusCode != 200) {
            console.log(now_str() + "Error posting to GATD");
            console.log(error);
            console.log(response);
            console.log();
        }
    });
}

function now_str () {
    return moment().format('MMMM Do YYYY, h:mm:ss a ');
}

