PowerBlade Gateway Setup
========================

Base gateway platform is the Swarm Gateway. Documentation can be found in the
[urban-heartbeat-kit](https://github.com/terraswarm/urban-heartbeat-kit) repo.
Software running on the gateway can be found in the
[lab11/gateway](https://github.com/lab11/gateway) repo.

# Disable unnecessary services
    sudo systemctl stop ble-nearby
    sudo systemctl disable ble-nearby
    sudo systemctl stop node-red
    sudo systemctl disable node-red

# Push data to GATD
*XXX* For now, this step should be skipped. It requires too much uplink bandwidth to be acceptable in a home deployment.

    sudo scp <user@comptuer>:~/shed/projects/powerblade/powerblade_deployment/gatd.conf /etc/swarm-gateway/gatd.conf
    sudo systemctl enable gateway-mqtt-gatd
    sudo systemctl start gateway-mqtt-gatd

# Push data to EmonCMS

    sudo scp <user@computer>:~/shed/projects/powerblade/powerblade_deployment/emoncms.conf /etc/swarm-gateway/emoncms.conf
    sudo systemctl enable gateway-mqtt-emoncms
    sudo systemctl start gateway-mqtt-emoncms

# Mount an SD Card
First Install a FAT32-formatted micro SD Card in the gateway. Then find the
sdcard with `fdisk -l` it's probably `/dev/mmcblk1p1`

    sudo mkdir /media/sdcard
    sudo mount -v /dev/mmcblk1p1 /media/sdcard
    
NOTE: This does NOT automatically re-mount the SD card at boot. We are still
working on a solution for that.

# Log data locally
As a default, the log.conf in shed attempts to save data to `/media/sdcard/`.
This will log to sdcard if it is mounted or locally if it is not.

    sudo scp <user@computer>:~/shed/projects/powerblade/powerblade_deployment/log.conf /etc/swarm-gateway/log.conf
    sudo systemctl enable gateway-mqtt-log
    sudo systemctl start gateway-mqtt-log

# Collect 802.15.4 packets from Monjolos

    sudo systemctl enable ieee802154-monjolo-gateway
    sudo systemctl start ieee802154-monjolo-gateway

# Collect 802.15.4 packets from Triumvis
You must be using an Edison gateway in order to receive Triumvi data. First,
you need to flash the cc2538 on the gateway.

    Clone [lab11/IntelEdisonGateway](https://github.com/lab11/IntelEdisonGateway)
    Clone [JelmerT/cc2538-bsl](https://github.com/JelmerT/cc2538-bsl)
    cd IntelEdisonGateway/Triumvi/cc2538/bin/
    Edit `flash.sh` to point at your copy of cc2538-bsl/cc2538-bsl.py
    Connect pogo pin program to the gateway with `Epic Multi Prog` board
    ./flash.sh

# Connect to WiFi
Edit /etc/network/interfaces. (Already set up for MWireless)

# Set up Sensu
Make sure you have a unique MAC address first!

    sudo scp <user@computer>:~/shed/projects/powerblade/powerblade_deployment/sensu.json /etc/sensu/conf.d/client.json
    cd gateway-tools/gateway/
    sudo ./sensu-configure-client.js
    sudo systemctl enable sensu-client
    sudo systemctl start sensu-client

# Common problems
To test that a service is working run `sudo systemctl status -l <SERVICE_NAME>`

If a service has failed, check that `npm install` has been run in its directory
within `gateway/software/`

