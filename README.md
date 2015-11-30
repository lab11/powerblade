PowerBlade
==========

PowerBlade is a miniature plug load power meter - it is small enough to fit
between the plug and the outlet while performing its metering operation.
Achieving this form factor requires targeting every aspect of traditional power
meters, including contact method (PowerBlade uses flexible tabs in the PCB
itself), power supply, voltage and current sensing, and data communication
(Bluetooth Low Energy, in this case).

There have been multiple iterations of PowerBlade, starting with a backscatter-
based variant and eventually transitioning to the BLE version. Along the way
there have been several iterations of flexible PCBs to determine the optimum
construction for the tabs to ensure strength and elasticity.

Future work on this system will include improvements to the accuracy of the unit
(PowerBlade readings currently have 5% to 10% error but we believe this can be
significantly lower), as well as safety.

[
![pb](https://raw.github.com/lab11/powerblade/master/images/powerblade.png)
](https://raw.github.com/lab11/powerblade/master/images/powerblade.png)


Applications
------------
Example applications to collect PowerBlade data are located in https://github.com/lab11/powerblade/tree/master/software/ble
To run:
```
sudo node powerblade_data.js
```

Installation
------------
### Pre-reqs for Noble

Install [Node.js](https://nodejs.org/en/download/package-manager/)

#### OS X
 * install [Xcode](https://itunes.apple.com/ca/app/xcode/id497799835?mt=12)

#### Linux
 * Kernel version 3.6 or above
 * ```libbluetooth-dev```

##### Ubuntu/Debian/Raspbian
```sh
sudo apt-get install bluetooth bluez libbluetooth-dev libudev-dev
```

##### Fedora / Other-RPM based
```sh
sudo yum install bluez bluez-libs bluez-libs-devel
```

##### Intel Edison
See [Configure Intel Edison for Bluetooth LE (Smart) Development](http://rexstjohn.com/configure-intel-edison-for-bluetooth-le-smart-development/)


### Pre-reqs for Node applications
Requirements are already listed in package.json.
```
npm install
```

