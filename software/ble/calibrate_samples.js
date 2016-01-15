
function calculate_constants(wattage, dataArr) {
	var voltageArr = [2520];
	var currentArr = [2520];
	for(var i = 0; i < 2520; i++) {
		voltageArr[i] = dataArr[2*i];
		currentArr[i] = dataArr[2*i + 1];
	}

	var voff = 0;
	var ioff = 0;
	for(var i = 0; i < 2520; i++) {
		voff += voltageArr[i];
		ioff += currentArr[i];
	}
	voff = Math.floor(voff / 2520);
	ioff = Math.floor(ioff / 2520);

	var integrate = [2520];

	var curoff = 0;
	for(var i = 0; i < 2520; i++) {
		var newCurrent = currentArr[i] - ioff;
		aggCurrent += (newCurrent + (newCurrent >> 1));
		aggCurrent -= aggCurrent >> 5;
		integrate[i] = aggCurrent;
		curoff += aggCurrent;
	}
	curoff = curoff / 2520;

	var sampleCount = 0;
	var aggCurrent = 0;
	var acc_i_rms = 0;
	var acc_v_rms = 0;
	var acc_p_ave = 0;
	var wattHoursAve = 0;
	var voltAmpAve = 0;
	for(var i = 0; i < 2520; i++) {
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

	var pscale_val = 0x4000 + *Math.floor(pscale_num*Math.pow(10,4));

    return {voff, ioff, curoff, pscale_val};
}