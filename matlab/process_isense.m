Numwaves = 200;
Viewwaves = 4;

Totsize = Numwaves/60;

Rideal = 2520 * 1000;
Pideal = 1/Rideal;

Rsample = 2520;
Psample = 1/Rsample;

t = [0:Pideal:Totsize];

volt_ideal = round(255*120*sin(2*pi*60*t)) + 255;
cur_ideal = round(255*cos(2*pi*60*t)) + 255;

everyNth = Psample / Pideal;

t_samp = downsample(t, everyNth);
volt_samp = downsample(volt_ideal, everyNth);
cur_samp = downsample(cur_ideal, everyNth);

cur_int = t_samp;
cut_int(1) = 0;

for i = 2:size(cur_int, 2)
    cur_int(i) = round(cur_int(i-1) + cur_samp(i) + bitshift(cur_samp(i), -1));
    cur_int(i) = round(cur_int(i) - bitshift(cur_int(i), -5));
end

true_int = t_samp;

for i = 1:size(true_int, 2)
    true_int(i) = 0;
    for j = 1:i
        true_int(i) = true_int(i) + cur_samp(j) - 255;
    end
end

%plotyy(t, volt_ideal, t, cur_ideal)
figure
a1 = plotyy(t_samp, volt_samp, t_samp, cur_samp)
set(a1, 'XLim', [(Numwaves-Viewwaves)/60 Numwaves/60])
figure
a2 = plotyy(t_samp, volt_samp, t_samp, cur_int)
set(a2, 'XLim', [(Numwaves-Viewwaves)/60 Numwaves/60])
figure
a3 = plotyy(t_samp, volt_samp, t_samp, true_int)
set(a3, 'XLim', [(Numwaves-Viewwaves)/60 Numwaves/60])
