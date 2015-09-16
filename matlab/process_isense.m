Totsize = 2/60;

Rideal = 2520 * 1000;
Pideal = 1/Rideal;

Rsample = 2520;
Psample = 1/Rsample;

t = [0:Pideal:Totsize];

volt_ideal = 120*sin(2*pi*60*t);
cur_ideal = cos(2*pi*60*t);

everyNth = Psample / Pideal;

t_samp = downsample(t, everyNth);
volt_samp = downsample(volt_ideal, everyNth);
cur_samp = downsample(cur_ideal, everyNth);

%plotyy(t, volt_ideal, t, cur_ideal)
plotyy(t_samp, volt_samp, t_samp, cur_samp)