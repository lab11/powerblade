#! /usr/bin/env node

// Display status of deployed powerblades

var WebSocketClient = require('websocket').client;
var client = new WebSocketClient();

var fs = require('fs');
var ini = require('ini');

try {
    var config_file = fs.readFileSync('gatd.conf', 'utf-8');
    var config = ini.parse(config_file);
    if (config.streamer_url == undefined || config.streamer_url == '') {
        throw new Exception("No GATD streamer URL");
    }
} catch (e) {
    console.log(e);
    console.log("\nBad configuration file");
    console.log("\t`ln -s shed/projects/powerblade/powerblade_deployment/gatd.conf .`");
    process.exit(1);
}

// connect to GATD stream via a websocket
client.on('connectFailed', function (error) {
    console.log('Client error: ' + error);
});

client.on('connect', function(connection) {
    console.log("Connected!");

    var query = {
        //'time_utc_timestamp': {'$gt': 1457070299796870},
        //'_gatd': {'time_utc_timestamp': 1457070299796870},
        'device': "BLEES",
    };

    //query = {};

    connection.sendUTF(JSON.stringify(query));

    connection.on('error', function (error) {
        console.log("Connection error: " + error);
    });

    connection.on('close', function () {
        console.log("Connection closed");
    });

    connection.on('message', function (message) {
        console.log(message);
    });
});

console.log("Connecting to " + config.streamer_url);
client.connect(config.streamer_url, null);

