#! /usr/bin/env node

// Collect MQTT powerblade packets
//  De-duplicate packets based on sequence number
//  Push to GATD for storage

var debug = require('debug')('powerblade-to-gatd');
var watchout = require('watchout');
var request = require('request');

// discover the local MQTT broker
var MQTTDiscover = require('mqtt-discover');
MQTTDiscover.start();

try {
    var config = require('./config');
} catch (e) {
    console.log(e);
    console.log("\nCannot find configuration file");
    console.log("\t`ln -s shed/projects/powerblade/powerblade_deployment/config.js .`");
    process.exit(1);
}

// mapping of {
//  'ble_addr': <squence_number>
// }
powerblades = {};

// add a watchdog for mqtt packets
mqtt_down = false;
var mqtt_watchdog = new watchout(1*60*1000, function(didCancelWatchdog) {
    if (didCancelWatchdog) {
        // benign
    } else {
        console.log("MQTT watchdog tripped");
        mqtt_down = true;
    }
});

// add a watchdog for gatd posts
gatd_down = false;
var gatd_watchdog = new watchout(5*60*1000, function(didCancelWatchdog) {
    if (didCancelWatchdog) {
        // benign
    } else {
        console.log("GATD watchdog tripped");
        gatd_down = true;
    }
});

// connect to MQTT broker
MQTTDiscover.on('mqttBroker', function (mqtt_client) {
    console.log("Connected to MQTT broker: " + mqtt_client.options.host);

    // subscribe to powerblade data
    mqtt_client.subscribe(config.mqtt.topic);
    mqtt_client.on('message', function (topic, message) {
        var adv = JSON.parse(message.toString());

        // got a packet, reset watchdog
        mqtt_watchdog.reset();
        if (mqtt_down) {
            console.log("Getting packets again");
            mqtt_down = false;
        }

        // keep track of each powerblade seen
        if (!(adv.id in powerblades)) {
            powerblades[adv.id] = -1;
        }

        // de-duplicate powerblade packets
        if (adv.sequence_number != powerblades[adv.id]) {
            powerblades[adv.id] = adv.sequence_number;

            // post packet to GATD
            post_to_gatd(adv);
        }
    });
});

// post JSON advertisements to GATD
function post_to_gatd (adv) {
    var req = {
        url: config.gatd.url,
        method: "POST",
        json: JSON.stringify(adv),
    };

    request(req, function (error, response, body) {
        if (!(error || response.statusCode != 200)) {
            // post successful, reset watchdog
            gatd_watchdog.reset();
            if (gatd_down) {
                console.log("Getting packets again");
                gatd_down = false;
            }
        }
    });
}

