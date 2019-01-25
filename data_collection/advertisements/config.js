var config = {};

config.connect_to_influx = true;
config.influx = {};
config.influx.host = '127.0.0.1';
config.influx.port = 9003;
config.influx.db = 'powerblade_demo'
config.influx.measurement = 'test_table';
config.influx.username = '';
config.influx.password = '';

module.exports = config;