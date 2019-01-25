# BLE Data Gathering
Gathers data from a powerblade over advertisements

This script can be used to display PowerBlade advertisements

At first run:
```
npm install
sudo node powerblade_adv.js
```

Subsequent runs:
```
sudo node powerblade_adv.js
```

# Saving to InfluxDB

`powerblade_adv_influx.js` is provided to save the data to an InfluxDB and also to a file called `powerblade_data.txt`. A basic config file for the InfluxDB settings is included at `config.js`.

`powerblade_data.txt` will be overwritten if it exists. 
