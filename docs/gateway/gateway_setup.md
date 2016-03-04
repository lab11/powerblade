PowerBlade Gateway Setup
========================

Base gateway platform is the Swarm Gateway. Documentation can be found in the
[urban-heartbeat-kit](https://github.com/terraswarm/urban-heartbeat-kit) repo.
Software running on the gateway can be found in the
[lab11/gateway](https://github.com/lab11/gateway) repo.

# Push data to GATD

`git clone https://github.com/lab11/powerblade.git`
`cp shed/projects/powerblade/powerblade_deployment/config.js .`
`sudo cp powerblade/software/gateway/systemd/powerblade-to-gatd.service /etc/systemd/system/`
`sudo systemctl powerblade-to-gatd`

# Push data to EmonCMS

