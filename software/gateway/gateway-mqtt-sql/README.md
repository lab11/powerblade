Gateway to SQL
===============

This service sends data from a swarm gateway to a remote SQL server for storage.

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

