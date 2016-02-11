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

		var voff = 0;
		var ioff = 0;
		for(var i = 60; i < (dataLen-60); i++) {
			voff += voltageArr[i];
			ioff += currentArr[i];
		}
		voff = Math.round(voff / (dataLen-120));
		ioff = Math.round(ioff / (dataLen-120));

		var integrate = [];

		var curoff = 0;
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
			curoff += (aggCurrent >> 3);

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
		var throwOutFirst = true;
		var divCount = 0;

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
				if(throwOutFirst == false) {
					wattHoursAve += acc_p_ave / 42;
					//console.log(wattHoursAve);
					voltAmpAve += SquareRoot(acc_v_rms / 42) * SquareRoot(acc_i_rms / 42);
					vrms += SquareRoot(acc_v_rms / 42);
					divCount = divCount + 1;
				}
				throwOutFirst = false;
				acc_p_ave = 0;
				acc_v_rms = 0;
				acc_i_rms = 0;
			}
		}

		console.log("Div len: " + divCount);

		
		vrms = vrms / divCount;
		var truePower = wattHoursAve / divCount;
		var appPower = voltAmpAve / divCount;

		var vscale_num = voltage / vrms;
		var vscale = Math.round(vscale_num * 200);

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
		console.log("Vscale = " + vscale_num);
		console.log("Vscale = " + vscale);
		console.log();
		console.log("Vrms = " + (vscale_num*vrms));
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
        //var vscale = 0x1F;
        var whscale = 0x09;

        // store values to properly sized buffers
        var voff_buf = new Buffer(1);
        voff_buf.writeInt8(voff);
        var ioff_buf = new Buffer(1);
        ioff_buf.writeInt8(ioff);
        var curoff_buf = new Buffer(2);
        curoff_buf.writeInt16LE(curoff);
        var pscale_buf = new Buffer(2);
        pscale_buf.writeUInt16LE(pscale_val);

        // also set default values for the scaling factors (which are not
        //  device dependent)
        var vscale_buf = new Buffer(1);
        vscale_buf.writeUInt8(vscale);
        var whscale_buf = new Buffer(1);
        whscale_buf.writeUInt8(whscale);

	    return {'voff': voff_buf,
                'ioff': ioff_buf,
                'curoff': curoff_buf,
                'pscale': pscale_buf,
                'vscale': vscale_buf,
                'whscale': whscale_buf};
	}
}
