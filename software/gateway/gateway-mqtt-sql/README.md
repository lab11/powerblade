Gateway to GATD
===============

[GATD](gatd.io) is a data collection, storage, and distribution service. This
service HTTP POSTs data collected by the gateway to GATD for storage.

Configuration
-------------

You must tell this tool the URL for the HTTP POST Receiver of the desired GATD
profile. To do this, create `/etc/swarm-gateway/emoncms.conf` and add:

    post_url = <url of GATD HTTP POST receiver>

Example:

    # /etc/swarm-gateway/gatd.conf
    post_url = http://post.gatd.io/<UUID>

