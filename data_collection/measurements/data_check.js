#!/usr/bin/env node

var chalk = require('chalk');
var fs = require('fs');

const pbList = ['c098e5700048', 'c098e570004a', 'c098e570004e', 'c098e5700053', 'c098e5700076', 'c098e570013c'];
const configList = ['jumper', 'outlet', 'surge'];

function printDevice(device) {
	console.log(chalk.bold.white("\n" + device + "\t\tOutlet\t\tSurge\t\tJumper"))

	for (var i = 0; i < pbList.length; i++) {
		var pb = pbList[i];
		var string = chalk.bold.white(pb) + "\t";

		for (var j = 0; j < configList.length; j++) {
			config = configList[j];

			if(file_info[device][pb] && file_info[device][pb][config]) {
				string += chalk.green(file_info[device][pb][config].toFixed(1)) + "\t\t";
			}
			else {
				string += chalk.bold.red("Missing") + "\t\t"
			}
		}

		console.log(string);
	}
}

// Get device in question
var device_save = "";
if(process.argv.length == 3) {
	device_save = process.argv[2];
}
    
file_info = {}

var filenames = fs.readdirSync(process.env.PB_DATA);

filenames.forEach(file => {
	var shortname = file.split('.')[0], extension = file.split('.')[1];
	if(extension == "dat" || extension == "txt") {
		//console.log(shortname);

		filelist = shortname.split('_');
		if(filelist.length == 3) {
			//console.log(filelist);
			var device = filelist[1];
			var pb = filelist[0];
			var config = filelist[2];

			if(!file_info[device]) {
				file_info[device] = {};
			}
			if(!file_info[device][pb]) {
				file_info[device][pb] = {};
			}
			if(!file_info[device][pb][config]) {
				var data = fs.readFileSync(process.env.PB_DATA + "/" + file, 'utf8');
				var avgPower = 0;
				var countPower = 0;
				var readLines = data.split('\n');
				for (var i = 0; i < readLines.length; i++) {
					try {
						//console.log(readLines[i])
						//console.log(JSON.parse(readLines[i]))
						avgPower += parseFloat(JSON.parse(readLines[i])['power']);
						countPower += 1;
					} catch (e) {
						if(e != "SyntaxError: Unexpected end of input") {
							console.log(e);
						}
					}
					//console.log(avgPower);
				}
				file_info[device][pb][config] = avgPower / countPower;
			}
			else {
				console.log("Error: repeat configuration: " + device + ", " + pb + ", " + config);
			}
		}
	}
});

if(device_save == "") {
	for(var device in file_info) {
		printDevice(device);		
	}
}
else {
	printDevice(device_save);
}




