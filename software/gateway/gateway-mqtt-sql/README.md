Gateway to GATD
===============

[GATD](gatd.io) is a data collection, storage, and distribution service. This
service HTTP POSTs data collected by the gateway to GATD for storage.

Setup
-----
If running standalone:

    npm install

or if running as part of a gateway:

    npm install mysql

Then

    sudo scp <user@computer>:~/shed/projects/powerblade/powerblade_deployment/powerblade-sql.conf /etc/swarm-gateway/powerblade-sql.conf
    sudo scp <user@computer>:~/shed/projects/powerblade/powerblade_deployment/powerblade-aws.conf /etc/swarm-gateway/powerblade-aws.conf
    sudo cp gateway-mqtt-sql.service /etc/systemd/system/
    sudo systemctl enable gateway-mqtt-sql
    sudo systemctl start gateway-mqtt-sql


Configuration
-------------

You must tell this tool the URL for the HTTP POST Receiver of the desired GATD
profile. To do this, create `/etc/swarm-gateway/emoncms.conf` and add:

    post_url = <url of GATD HTTP POST receiver>

Example:

    # /etc/swarm-gateway/gatd.conf
    post_url = http://post.gatd.io/<UUID>

