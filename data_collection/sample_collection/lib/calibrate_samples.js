var fs = require('fs');

function SquareRoot(a_nInput){
	op = a_nInput;
	res = 0;
	one = 1 << 30;

	while(one > op) {
		one >>= 2
	}

	while(one != 0) {
		if(op >= (res + one)) {
			op = op - (res + one);
			res = res + 2 * one;
		}
		res >>= 1;
		one >>= 2;
	}

	return res;
}

module.exports = {
	calculate_constants: function (wattage, voltage, dataArr) {
		var dataLen = dataArr.length / 4;
		var dataBuf = new Buffer(dataArr);

		var voltageArr = [];
		var currentArr = [];
		var voltageIndex = 0;
		var currentIndex = 2;
		fs.writeFileSync('data/rawSamples.dat', '# Count\tVoltage\tCurrent\tInt\n');
		for(var i = 0; i < dataLen; i++) {
			voltageArr.push(dataBuf.readInt16BE(4*i + voltageIndex));
			currentArr.push(dataBuf.readInt16BE(4*i + currentIndex));
		}


		// list all of the calibrations from the powerblade here
		var voff = -6;
		var ioff = -19;
		var curoff = -3;
		var pscale = 16667;
		pscale = (pscale & 0xFFF) * Math.pow(10,-1*((pscale & 0xF000) >> 12));
		var vscale = 120;
		vscale = vscale / 200;


		//var voff = 0;
		//var ioff = 0;
		for(var i = 60; i < (dataLen-60); i++) {
			//voff += voltageArr[i];
			//ioff += currentArr[i];
		}
		//voff = Math.round(voff / (dataLen-120));
		//ioff = Math.round(ioff / (dataLen-120));

		var integrate = [];

		//var curoff = 0;
		var aggCurrent = 0;
		for(var i = 0; i < dataLen; i++) {
			var newCurrent = currentArr[i] - ioff;
			// if(i < 15) {
			// 	console.log("Current = " + currentArr[i] + ", newCurrent = " + newCurrent);
			// }
			aggCurrent += (newCurrent + (newCurrent >> 1));
			aggCurrent -= aggCurrent >> 5;
			integrate[i] = (aggCurrent >> 3);
			// if(i < 15) {
			// 	console.log("Agg current = " + aggCurrent);
			// }
			if((i > 60) && i < (dataLen - 60)) {
				//curoff += (aggCurrent >> 3);
			}

			//console.log(i + '\t' + voltageArr[i] + '\t' + currentArr[i] + '\t' + integrate[i]);
			fs.appendFileSync('data/rawSamples.dat', i + '\t' + voltageArr[i] + '\t' + currentArr[i] + '\t' + integrate[i] + '\n');
		}
		//curoff = Math.round(curoff / (dataLen-120));

		fs.writeFileSync('data/realSamples.dat', '# Count\tVoltage\tCurrent\n');
		for (var i=0; i < dataLen; i++) {
			var real_voltage = vscale*(voltageArr[i] - voff);
			var real_integrate = (pscale/vscale)*(integrate[i] - curoff);
			
			fs.appendFileSync('data/realSamples.dat', i + '\t' + real_voltage + '\t' + real_integrate + '\n');
		}
	}
}
