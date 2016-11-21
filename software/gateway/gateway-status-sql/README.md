Gateway to SQL
===============

Once per day, this service sends a gateway status message to the SQL server

Setup
-----
If running standalone:

    npm install

or if running as part of a gateway:

    npm install mysql

Then

    sudo scp <user@computer>:~/shed/projects/powerblade/powerblade_deployment/powerblade-aws.conf /etc/swarm-gateway/powerblade-aws.conf
    sudo cp gateway-status-sql.service /etc/systemd/system/
    sudo systemctl enable gateway-status-sql
    sudo systemctl start gateway-status-sql

