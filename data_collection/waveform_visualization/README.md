Waveform Visualization
======================

Connects to a PowerBlade and continuously collects waveform data. Expects the
PowerBlade to be continuously providing the waveforms, rather than only
providing unique data. Waveforms are visualized with matplotlib.

## Installing libraries

To install the correct libraries to run this script, you will need to run the
node package manager:

```
$ npm install
```

The script has been tested with npm version 5.6.0 and nodejs version 8.11.3,
but most likely works on newer (and some older) versions.

To plot things, we're using a python3 process running matplotlib.

```
$ pip3 install matplotlib
```

## Waveform visualization

Call the `visualize waveforms` script, providing it the address of the PowerBlade
you want to download samples from.

```
$ sudo ./visualize_waveforms.js c0:98:e5:70:02:6a
```

Note that this script occasionally crashes. If you see text being repeated and
then it freezes for a long time, it has probably failed. You can kill the
script (Ctrl-C), and restart it to try again without any harm. It will most
likely work eventually after several attempts.


## Data collection

Data is not typically saved by this script, but can be saved with the `--save`
flag. Results are stored in the `data/` directory and are named sequentially.

## Unique Waveforms

Instead of collecting continuous waveforms, this script can be configured to
only collect 'unique' waveforms with the `--unique` flag.

