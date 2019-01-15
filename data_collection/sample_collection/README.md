Sample Collection
=================

Scripts for interacting with a PowerBlade, requesting its current calibration
data, downloading raw current and voltage sample values, and adjusting those
values based on the current calibration to get real voltage and current
measurements.

## Installing libraries

To install the correct libraries to run this script, you will need to run the
node package manager:

```
$ npm install
```

The script has been tested with npm version 5.6.0 and nodejs version 8.11.3,
but most likely works on newer (and some older) versions.

## Collecting samples

Call the `collect samples` script, providing it the address of the PowerBlade
you want to download samples from.

```
$ sudo ./collect_samples.js c0:98:e5:70:02:6e
```

Note that this script occasionally crashes. If you see text being repeated and
then it freezes for a long time, it has probably failed. You can kill the
script (Ctrl-C), and restart it to try again without any harm. It will most
likely work eventually after several attempts.


## Accessing data

Results are stored in the `data/` directory.

 * The `.bin` files are the raw binary data downloaded from the PowerBlade.
 * `rawSamples.dat` are the raw sample data translated into human-readable
   values and also includes the integration values for the current at each
   iteration. Note that the units of these values are in raw ADC counts and
   have not been adjusted based on the PowerBlade's calibration.
 * `realSamples.dat` are the calibrated sample data translated into a
   human-readable format. It is in units of Amps and Volts respectively.


## Visualizing data

The raw sample data can be plotted using gnuplot.

```
$ gnuplot plot_rawSamples.gnuplot
$ epstopdf plot.eps
$ open plot.pdf
```

