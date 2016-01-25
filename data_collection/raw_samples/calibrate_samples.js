
module.exports = {
	calculate_constants: function (wattage, dataArr) {
		var dataLen = dataArr.length / 2;

		var voltageArr = [dataLen];
		var currentArr = [dataLen];
		for(var i = 0; i < dataLen; i++) {
			voltageArr[i] = dataArr[2*i];
			currentArr[i] = dataArr[2*i + 1];
		}

		var voff = 0;
		var ioff = 0;
		for(var i = 0; i < dataLen; i++) {
			voff += voltageArr[i];
			ioff += currentArr[i];
		}
		voff = Math.floor(voff / dataLen);
		ioff = Math.floor(ioff / dataLen);

		var integrate = [dataLen];

		var curoff = 0;
		for(var i = 0; i < dataLen; i++) {
			var newCurrent = currentArr[i] - ioff;
			aggCurrent += (newCurrent + (newCurrent >> 1));
			aggCurrent -= aggCurrent >> 5;
			integrate[i] = aggCurrent;
			curoff += aggCurrent;
		}
		curoff = curoff / dataLen;

		var sampleCount = 0;
		var aggCurrent = 0;
		var acc_i_rms = 0;
		var acc_v_rms = 0;
		var acc_p_ave = 0;
		var wattHoursAve = 0;
		var voltAmpAve = 0;
		for(var i = 0; i < dataLen; i++) {
			var newVoltage = voltageArr[i] - voff;
			var newIntegrate = integrate[i] - curoff;
			acc_i_rms = newIntegrate * newIntegrate;
			acc_v_rms = newVoltage * newVoltage;
			acc_p_ave = newVoltage * newIntegrate;

			sampleCount++;
			if(sampleCount == 42) {
				sampleCount = 0;
				wattHoursAve += acc_p_ave / 42;
				acc_p_ave = 0;
				voltAmpAve += Math.sqrt(acc_v_rms / 42) * Math.sqrt(acc_i_rms / 42);
				acc_v_rms = 0;
				acc_i_rms = 0;
			}
		}

		var truePower = wattHoursAve / 60;
		var pscale_num = wattage / truePower;

		var pscale_val = 0x4000 + Math.floor(pscale_num*Math.pow(10,4));

		console.log("Ioff = " + ioff);
		console.log("Voff = " + voff);
		console.log("Curoff = " + curoff);
		console.log("Pscale = " + pscale_val);

	    return {voff, ioff, curoff, pscale_val};
	}
}