Using Emoncms with PowerBlade
=================================================

[Emoncms](http://emoncms.org/site/home) is an energy meter data backend.


Emoncms Installation
--------------------

1. Install [docker](http://docs.docker.com/engine/installation/)

2. Build the Docker image using [docker-emoncms](https://github.com/mdef/docker-emoncms).

        cd /opt
        sudo git clone https://github.com/mdef/docker-emoncms emoncms
        sudo chown -R username:username emoncms
        cd emoncms
        docker build -t yourname/emoncms .
        
    This step will take a minute to create all the required dependencies.

3. Setup the host machine so that we can save persistent data.

        docker run --rm -v /opt/emoncms:/host yourname/emoncms cp -rp {/var/www/emoncms,/var/lib/mysql,/var/lib/phpfina,/var/lib/phpfiwa,/var/lib/phptimeseries} /host/

4. Run the Docker image of emoncms.

    Run for testing
    ```bash
    docker run -it -p 80:80 \
    -v /opt/emoncms/emoncms:/var/www/emoncms \ 
    -v /opt/emoncms/mysql:/var/lib/mysql \
    -v /opt/emoncms/phpfiwa:/var/lib/phpfiwa \
    -v /opt/emoncms/phpfina:/var/lib/phpfina \
    -v /opt/emoncms/phptimeseries:/var/lib/phptimeseries \
    -v /opt/emoncms/sessions:/var/lib/php5/sessions \
    -v /opt/emoncms/supervisor:/etc/supervisor/conf.d \
    yourname/emoncms /bin/bash 
    ```

    Run in production
    ```bash
    /usr/bin/docker run -p 80:80 -v /opt/emoncms/emoncms:/var/www/emoncms -v /opt/emoncms/mysql:/var/lib/mysql -v /opt/emoncms/phpfiwa:/var/lib/phpfiwa -v /opt/emoncms/phpfina:/var/lib/phpfina -v /opt/emoncms/phptimeseries:/var/lib/phptimeseries -v /opt/emoncms/sessions:/var/lib/php5/sessions -v /opt/emoncms/supervisor:/etc/supervisor/conf.d yourname/emoncms /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
    ```

