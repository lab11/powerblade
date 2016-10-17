MSP 430 Images
==============

Used for flashing new MSP430 devices. See [PowerBlade
versions](../../docs/powerblade_specs/msp_versions.md) for more details.

First install [MSP Flasher](http://www.ti.com/tool/msp430-flasher).
You also need to export it and it's library files. Add the following to your `.bashrc`

    PATH=$PATH:<PATH>/MSPFlasher_1.3.9/bin/
    LD_LIBRARY_PATH=$LD_LIBRARY_PATH:<PATH>/MSPFlasher_1.3.9/

You also need a [MSP430 USB JTAG
Interface](http://www.ti.com/tool/msp-fet430uif) and a
[10-pin Tag Connect Cable](http://www.tag-connect.com/TC2050-IDC-430).

After connecting to the MSP430, run `./flash_powerblade` to flash a unit.

### Naming Format

[software name]\_[PD_ID]v[MSP Version]v[Minor Version].hex

