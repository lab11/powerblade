PowerBlade Gateway Setup
========================

Base gateway platform is the Swarm Gateway. Documentation can be found in the
[urban-heartbeat-kit](https://github.com/terraswarm/urban-heartbeat-kit) repo.
Software running on the gateway can be found in the
[lab11/gateway](https://github.com/lab11/gateway) repo.

# Push data to GATD
    `git clone https://github.com/lab11/powerblade.git`
    `cd powerblade/software/gateway/powerblade-to-gatd/`
    `cp shed/projects/powerblade/powerblade_deployment/config.js .`
    `npm install`
    `sudo cp ../systemd/powerblade-to-gatd.service /etc/systemd/system/`
    `sudo systemctl enable powerblade-to-gatd`
    `sudo systemctl start powerblade-to-gatd`

# Push data to EmonCMS
    `sudo cp shed/projects/powerblade/powerblade_deployment/emoncms.conf /etc/swarm-gateway/emoncms.conf`
    `sudo systemctl enable gateway-mqtt-emoncms`
    `sudo systemctl start gateway-mqtt-emoncms`

