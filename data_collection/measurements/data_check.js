#!/usr/bin/env node

var chalk = require('chalk');
var fs = require('fs');

//const pbList = ['c098e5700048', 'c098e570004a', 'c098e570004e', 'c098e5700053', 'c098e570013c'];//, 'c098e570004b', 'c098e570005d'];
const pbList = ['c098e570004f', 'c098e5700080', 'c098e5700081', 'c098e5700065'];
const configList = ['jumper', 'outlet', 'surge', 'gfci'];
const calibList = ['jumper', 'outlet', 'surge', 'gfci'];

const INCOM = -1
const CLEARED = -2

var missing_count = 0;

function printDevice(device, missing) {
	var misCount = 0;
	var printString = chalk.bold.white(device + "\t\tJumper\t\t\tOutlet\t\t\tSurge\t\t\tGFCI\n");
	//console.log(chalk.bold.white(device + "\t\tJumper\t\tOutlet\t\tSurge"));
	if(file_info[device]['actual']) {
		if(typeof file_info[device]['actual'] == "number") {
			if(missing == false) {
				printString += chalk.bold.white("Actual: ") + chalk.green(file_info[device]['actual'].toFixed(1)) + "\n";
				//console.log(chalk.bold.white("Actual: ") + chalk.green(file_info[device]['actual'].toFixed(1)));
			}
		}
		else {
			var string = chalk.bold.white("Actual:\t\t");
			var locMis = 0;
			for(var j = 0; j < configList.length; j++) {
				if(file_info[device]['actual'][configList[j]]) {
					if(file_info[device]['actual'][configList[j]] == INCOM) {
						string += chalk.yellow("Incomplete\t\t");
						locMis += 1;
					}
					else if(file_info[device]['actual'][configList[j]] == CLEARED) {
						string += chalk.grey("--\t\t\t");
					}
					else {
						string += chalk.green(file_info[device]['actual'][configList[j]].toFixed(1)) + "\t\t\t";
					}
				}
				else {
					string += chalk.bold.red("Missing") + "\t\t\t";
					locMis += 1;
				}
			}
			if(missing == false || locMis > 0) {
				printString += string + "\n";
				misCount += locMis;
				//console.log(string);
			}
			missing_count += locMis;
		}
	}
	else {
		printString += chalk.bold.white("Actual: ") + chalk.bold.red("Missing\n")
		misCount += 1;
		missing_count += 1;
		//console.log(chalk.bold.white("Actual: ") + chalk.bold.red("Missing"))
	}

	for (var i = 0; i < pbList.length; i++) {
		var pb = pbList[i];
		var string = chalk.bold.white(pb) + "\t";
		var locMis = 0;

		for (var j = 0; j < configList.length; j++) {
			config = configList[j];

			if(file_info[device][pb] && file_info[device][pb][config]) {
				if(file_info[device][pb][config]['power'] == INCOM) {
					string += chalk.yellow("Incomplete\t\t");
					locMis += 1;
				}
				else if(file_info[device][pb][config]['power'] == CLEARED) {
					string += chalk.grey("--\t\t\t");
				}
				else {
					string += chalk.green(file_info[device][pb][config]['power'].toFixed(1) + " W") + ", " + chalk.green(file_info[device][pb][config]['vrms'].toFixed(1) + " V") + "\t";
					if(file_info[device][pb][config]['power'] < 100) {
						string += "\t"
					}
				}
			}
			else {
				string += chalk.bold.red("Missing") + "\t\t\t";
				locMis += 1;
			}
		}
		if(missing == false || locMis > 0) {
			printString += string + "\n";
			misCount += locMis;
			//console.log(string);
		}
		missing_count += locMis;
	}
	if(missing == false || misCount > 0) {
		console.log(printString);
	}
}

// Get device in question
var device_save = "";
var device_clear = "";
if(process.argv.length >= 3) {
	device_save = process.argv[2];
	if(process.argv.length == 4) {
		device_clear = process.argv[3];
	}
}
    
file_info = {}

var folderName = process.env.PB_DATA + 'measurements_rig'
var filenames = fs.readdirSync(folderName);

filenames.forEach( function(file) {

	var shortname = file.split('.')[0], extension = file.split('.')[1];
	if(extension == "dat" || extension == "txt") {
		//console.log(shortname);
		filelist = shortname.split('_');

		// Read data from the file
		if(filelist.length >= 1 && filelist.length <= 3) {
			var data = fs.readFileSync(folderName + "/" + file, 'utf8');
			var avgPower = 0;
			var avgVoltage = 0;
			var count = 0;
			var readLines = data.split('\n');
			for (var i = 0; i < readLines.length; i++) {
				try {
					//console.log(readLines[i])
					//console.log(JSON.parse(readLines[i]))
					avgPower += parseFloat(JSON.parse(readLines[i])['power']);
					avgVoltage += parseFloat(JSON.parse(readLines[i])['vrms']);
					count += 1;
				} catch (e) {
					if(e != "SyntaxError: Unexpected end of input" && e != "SyntaxError: Unexpected end of JSON input") {
						console.log(e);
					}
				}
				//console.log(avgPower);
			}
		}

		if(filelist.length == 3) {			// This is a Powerblade measurement
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
				file_info[device][pb][config] = {};
				if(count == 0) {
					file_info[device][pb][config]['power'] = CLEARED;
				}
				else if(count == 50) {
					file_info[device][pb][config]['power'] = avgPower / count;
					file_info[device][pb][config]['vrms'] = avgVoltage / count;
				}
				else {
					file_info[device][pb][config]['power'] = INCOM;
				}
			}
			else {
				console.log("Error: repeat configuration: " + device + ", " + pb + ", " + config);
			process.exit();
			}
		}
		else if(filelist.length == 2) {		// This is a WattsUp measurement with multiple configs
			var device = filelist[0];
			var config = filelist[1];
			if(!file_info[device]) {
				file_info[device] = {};
			}
			if(!file_info[device]['actual']) {
				file_info[device]['actual'] = {};
			}
			else if(typeof file_info[device]['actual'] == "number") {
				console.log("Error: inconsistent ground truth: " + device);
				process.exit();
			}
			if(!file_info[device]['actual'][config]) {
				if(count == 0) {
					file_info[device]['actual'][config] = CLEARED;
				}
				else if(count == 10) {
					file_info[device]['actual'][config] = avgPower / count;
				}
				else {
					file_info[device]['actual'][config] = INCOM;
				}
			}
			else {
				console.log("Error: repeat ground truth: " + device);
				process.exit();
			}
		}
		else if(filelist.length == 1) {		// This is a WattsUp measurement with only one config
			var device = filelist[0];
			if(!file_info[device]) {
				file_info[device] = {};
			}
			if(!file_info[device]['actual']) {
				file_info[device]['actual'] = avgPower / count;
			}
			else {
				console.log("Error: repeat ground truth: " + device);	
				process.exit();
			}
		}
	}
});

console.log();
console.log("Data checkup for PowerBlade measurements");
console.log();

var missing = false;
if(device_save == "missing") {
	device_save = "";
	missing = true;
}

if(device_save == "clear") {
	for(var i = 0; i < configList.length; i++) {
		if(file_info[device_clear]['actual'] && typeof file_info[device_clear]['actual'] != "number" && !file_info[device_clear]['actual'][configList[i]]) {
			var filename = folderName + "/" + device_clear + "_" + configList[i] + ".dat";
			console.log("Creating file: " + filename);
			fs.closeSync(fs.openSync(filename, 'w')); 
		}

		for(var j = 0; j < pbList.length; j++) {
			if(!file_info[device_clear][pbList[j]] || !file_info[device_clear][pbList[j]][configList[i]]) {
				var filename = folderName + "/" + pbList[j] + "_" + device_clear + "_" + configList[i] + ".dat";
				console.log("Creating file: " + filename);
				fs.closeSync(fs.openSync(filename, 'w')); 
			}
		}
	}
	process.exit();
}

if(device_save == "") {
	for(var device in file_info) {
		printDevice(device, missing);
	}
}
else {
	printDevice(device_save, missing);
}




if(missing_count != 0) {
	console.log("Missing data, clear or collect before generating reports");
	process.exit();
}
if(device_save != "") {
	console.log("Report only generated on full dataset");
	process.exit();
}

// Data processing phase

// For each device, find the maximum difference between any two measurements
// Also sort the measurements in decreasing order
for(device in file_info) {
	var maxVal = 0;
	var minVal = 2500;
	var maxPb, maxConfig;
	var minPb, minConfig;
	var average = 0;
	var avcount = 0;
	for(pb in pbList) {
		for(config in configList) {
			if(file_info[device][pbList[pb]][configList[config]]['power'] != INCOM && file_info[device][pbList[pb]][configList[config]]['power'] != CLEARED) {
				average += file_info[device][pbList[pb]][configList[config]]['power'];
				avcount += 1;

				if(file_info[device][pbList[pb]][configList[config]]['power'] < minVal) {
					minVal = file_info[device][pbList[pb]][configList[config]]['power'];
					minPb = pbList[pb];
					minConfig = configList[config];
				}
				if(file_info[device][pbList[pb]][configList[config]]['power'] > maxVal) {
					maxVal = file_info[device][pbList[pb]][configList[config]]['power'];
					maxPb = pbList[pb];
					maxConfig = configList[config];
				}
			}
		}
	}
	//console.log(device + "\t" + maxVal + "\t" + minVal)
	// Actuall calculate maximum
	file_info[device]['maxDiff'] = maxVal - minVal;
	file_info[device]['average'] = average / avcount;	// Used to calculate percent error
}

var file_copy = JSON.parse(JSON.stringify(file_info));

var writeString_power = "";

//console.log(file_copy['vac'])

// Output the maxDiff data, sorted by maximum difference
//console.log("plot \"sorted_maxDiff_power.dat\" u :xtic(2) notitle, \\")
var count = 1
for(burner in file_info) {	// Do this for the number of devices
	var maxVal = 0;
	var maxDevice;
	for(device in file_copy) {	// For any device not yet printed
		if(file_copy[device]['maxDiff'] > maxVal) {
			maxVal = file_copy[device]['maxDiff'];
			maxDevice = device;
		}
	}

	var minVal = 2500;
	for(pb in pbList) {
		for(config in configList) {
			var this_val = file_copy[maxDevice][pbList[pb]][configList[config]]['power'];
			if(this_val < minVal && this_val > 0) {
				minVal = file_copy[maxDevice][pbList[pb]][configList[config]]['power'];
			}
		}
	}

	writeString_power += count + "\t" + maxDevice + "\t";
	// Found the device with the greatest overall difference, now sort its members
	for(var i = 0; i < (pbList.length * configList.length); i++) {
		var maxConfigVal = -3;
		var maxPB;
		var maxConfig;
		for(pb in pbList) {
			for(config in file_copy[maxDevice][pbList[pb]]) {
				if(file_copy[maxDevice][pbList[pb]][config]['power'] > maxConfigVal) {
					maxConfigVal = file_copy[maxDevice][pbList[pb]][config]['power'];
					maxPB = pbList[pb];
					maxConfig = config;
				}
			}
		}
		if(maxConfigVal >= 0) {
			writeString_power += (maxConfigVal-minVal) + "\t";
		} else {
			writeString_power += "0\t";
		}
		//console.log('\t\"\" u ($' + (i+3) + '+offset) with boxes, \\\n\t\"\" u ($' + (i+3) + ') with boxes lc \"grey\" notitle, \\')
		delete file_copy[maxDevice][maxPB][maxConfig];
	}

	//writeString_power += count + "\t" + maxDevice + "\t" + maxVal + "\t" + maxVal/file_copy[maxDevice]['average'] + "\n";
	writeString_power += maxVal/file_copy[maxDevice]['average'] + "\n";
	count += 1;
	delete file_copy[maxDevice];
}

fs.writeFileSync("sorted_maxDiff_power.dat", writeString_power);

// Get the total errors for each of the three configs for each of the three types of calibration
var avgErr = {};
var avgErrCt = {};

for(calib in calibList) {
	avgErr[calibList[calib]] = {};
	avgErrCt[calibList[calib]] = {};
	for(config in configList) {
		avgErr[calibList[calib]][configList[config]] = 0;
		avgErrCt[calibList[calib]][configList[config]] = 0;
	}
}

for(device in file_info) {
	for(calib in calibList) {
		file_info[device][calibList[calib]] = {};
	}

	for(config in configList) {
		var actual;
		if(typeof file_info[device]['actual'] == "number") {
			actual = file_info[device]['actual'];
		} else {
			actual = file_info[device]['actual'][configList[config]];
		}

		// file_info[device]['outlet'][configList[config]] = (file_info[device]['c098e5700053'][configList[config]]['power'] + file_info[device]['c098e5700048'][configList[config]]['power']) / 2;
		// file_info[device]['jumper'][configList[config]] = (file_info[device]['c098e570004a'][configList[config]]['power'] + file_info[device]['c098e570004e'][configList[config]]['power']) / 2;
		// file_info[device]['home'][configList[config]] = file_info[device]['c098e570013c'][configList[config]]['power'];
		file_info[device]['outlet'][configList[config]] = file_info[device]['c098e5700080'][configList[config]]['power'];
		file_info[device]['jumper'][configList[config]] = file_info[device]['c098e5700081'][configList[config]]['power'];
		file_info[device]['surge'][configList[config]] = file_info[device]['c098e570004f'][configList[config]]['power'];
		file_info[device]['gfci'][configList[config]] = file_info[device]['c098e5700065'][configList[config]]['power'];

		if(device != 'vac' && device != 'hairGF' && device != 'toastGF') {
			for(calib in calibList) {
				avgErr[calibList[calib]][configList[config]] += (Math.abs(actual - file_info[device][calibList[calib]][configList[config]])/actual)*100;
				avgErrCt[calibList[calib]][configList[config]] += 1;
			}
		}
	}
}

var avg_copy = JSON.parse(JSON.stringify(avgErr));
var writeString_config = "";

for(var i = 0; i < (calibList.length * configList.length); i++) {
	var maxVal = 0;
	var maxCalib;
	var maxConfig;
	for(calib in avg_copy) {
		for(config in avg_copy[calib]) {
			if(avg_copy[calib][config] > maxVal) {
				maxVal = avg_copy[calib][config];
				maxCalib = calib;
				maxConfig = config;
			}
		}
	}
	//console.log(maxCalib + "\t" + maxConfig)// + "\t" + (avgErr[maxCalib][maxConfig]/avgErrCt[maxCalib][maxConfig]));
	writeString_config += maxCalib + "." + maxConfig + "\t" + (avgErr[maxCalib][maxConfig]/avgErrCt[maxCalib][maxConfig]) + "\n";
	delete avg_copy[maxCalib][maxConfig];
}

fs.writeFileSync("sorted_configs.dat", writeString_config);




