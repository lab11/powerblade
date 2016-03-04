Runs on a gateway. Connects to the local MQTT broker, collects PowerBlade BLE
data, de-duplicates the data, and posts it to GATD.

Requires a configuration script from shed:
    `ln -s shed/projects/powerblade/powerblade_deployment/config.js .`

