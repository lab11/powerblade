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
	calculate_constants: function (wattage, dataArr) {
		var dataLen = dataArr.length / 2;

		var voltageArr = [dataLen];
		var currentArr = [dataLen];
		var voltageIndex = 0;
		var currentIndex = 1;
		fs.writeFileSync('data/rawSamples.dat', '# Count\tVoltage\tCurrent\tInt\n');
		for(var i = 0; i < dataLen; i++) {
			voltageArr[i] = dataArr[2*i + voltageIndex];
			if(voltageArr[i] > 127) {
				voltageArr[i] -= 256;
			}
			currentArr[i] = dataArr[2*i + currentIndex];
			if(currentArr[i] > 127) {
				currentArr[i] -= 256;
			}

			// if((i % ((504/2)-1)) == 0) {
			// 	voltageIndex ^= 1;
			// 	currentIndex ^= 1;
			// }
		}

		var voff = 0;
		var ioff = 0;
		for(var i = 0; i < dataLen; i++) {
			voff += voltageArr[i];
			ioff += currentArr[i];
		}
		voff = Math.round(voff / dataLen);
		ioff = Math.round(ioff / dataLen);

		var integrate = [dataLen];

		var curoff = 0;
		var aggCurrent = 0;
		var tempCurrent = currentArr[0] - ioff;
		// console.log(currentArr[0])
		// console.log(aggCurrent + (tempCurrent + (tempCurrent >> 1)));
		for(var i = 0; i < dataLen; i++) {
			var newCurrent = currentArr[i] - ioff;
			// if(i < 15) {
			// 	console.log("Current = " + currentArr[i] + ", newCurrent = " + newCurrent);
			// }
			aggCurrent += (newCurrent + (newCurrent >> 1));
			aggCurrent -= aggCurrent >> 5;
			integrate[i] = aggCurrent;
			// if(i < 15) {
			// 	console.log("Agg current = " + aggCurrent);
			// }
			curoff += aggCurrent;

			//console.log(i + '\t' + voltageArr[i] + '\t' + currentArr[i] + '\t' + integrate[i]);
			fs.appendFileSync('data/rawSamples.dat', i + '\t' + voltageArr[i] + '\t' + currentArr[i] + '\t' + integrate[i] + '\n');
		}
		curoff = Math.round(curoff / dataLen);

		var sampleCount = 0;
		var acc_i_rms = 0;
		var acc_v_rms = 0;
		var acc_p_ave = 0;
		var wattHoursAve = 0;
		var voltAmpAve = 0;
		fs.writeFileSync('data/goodSamples.dat', '# Count\tVoltage\tCurrent\n');

		var vrms = 0;

		for(var i = 0; i < dataLen; i++) {
			var newVoltage = voltageArr[i] - voff;
			var newIntegrate = integrate[i] - curoff;
			acc_i_rms += newIntegrate * newIntegrate;
			acc_v_rms += newVoltage * newVoltage;
			acc_p_ave += newVoltage * newIntegrate;
			// if(i == 0) {
			// 	console.log("First Voltage: " + newVoltage);
			// 	console.log("First Current: " + newIntegrate);
			// }

			fs.appendFileSync('data/goodSamples.dat', i + '\t' + newVoltage + '\t' + newIntegrate + '\n');

			sampleCount++;
			if(sampleCount == 42) {
				sampleCount = 0;
				wattHoursAve += acc_p_ave / 42;
				//console.log(wattHoursAve);
				acc_p_ave = 0;
				voltAmpAve += SquareRoot(acc_v_rms / 42) * SquareRoot(acc_i_rms / 42);
				vrms += SquareRoot(acc_v_rms / 42);
				acc_v_rms = 0;
				acc_i_rms = 0;
			}
		}

		vrms = vrms / 60;
		var truePower = wattHoursAve / 60;
		var appPower = voltAmpAve / 60;
		var pscale_num = wattage / truePower;

		console.log();
		console.log("Prescale:");
		console.log("True Power = " + truePower);
		console.log("App Power = " + appPower);

		truePower = truePower * pscale_num;
		appPower = appPower * pscale_num;

		var pscale_val = 0x4000 + Math.floor(pscale_num*Math.pow(10,4));

		console.log();
		console.log("Voff = " + voff);
		console.log("Ioff = " + ioff);
		console.log("Curoff = " + curoff);
		console.log("Pscale = " + pscale_num);
		console.log("Pscale = " + pscale_val);
		console.log();
		console.log("Vrms = " + (2.46*vrms));
		console.log("True Power = " + truePower);
		console.log("App Power = " + appPower);
        console.log();

        // do bounds checking on numbers
        //  set numbers to their default values if they are out of bounds
        //  default numbers taken from MSP430 programming
        if (voff < -128 || voff > 127) {
            voff = -1;
        }
        if (ioff < -128 || ioff > 127) {
            ioff = -1;
        }
        if (curoff < -32768 || curoff > 32767) {
            curoff = 0;
        }
        if (pscale_val < 0 || pscale_val > 65535) {
            pscale_val = 0x428A;
        }

        // store values to properly sized buffers
        var voff_buf = new Buffer(1);
        voff_buf.writeInt8(voff);
        var ioff_buf = new Buffer(1);
        ioff_buf.writeInt8(ioff);
        var curoff_buf = new Buffer(2);
        curoff_buf.writeInt16LE(curoff);
        var pscale_buf = new Buffer(2);
        pscale_buf.writeUInt16LE(pscale_val);

	    return {'voff': voff_buf,
                'ioff': ioff_buf,
                'curoff': curoff_buf,
                'pscale': pscale_buf};
	}
}
