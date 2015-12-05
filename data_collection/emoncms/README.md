Using Emoncms with PowerBlade
=================================================

[Emoncms](http://emoncms.org/site/home) is an energy meter data backend.


Emoncms Installation
--------------------

1. Install [docker](http://docs.docker.com/engine/installation/)

2. Build the Docker image using [docker-emoncms](https://github.com/mdef/docker-emoncms).

        git clone https://github.com/mdef/docker-emoncms
        cd docker-emoncms
        docker build -t yourname/emoncms .
        
    This step will take a minute to create all the required dependencies.

3. Setup the host machine so that we can save persistent data.

        mkdir -p /opt/emoncms
        docker run --rm -v /opt/emoncms:/host yourname/emoncms cp -rp {/var/www/emoncms,/var/lib/mysql,/var/lib/phpfina,/var/lib/phpfiwa,/var/lib/phptimeseries} /host/

4. Run the Docker image of emoncms.

    Run for testing
    ```bash
    docker run -it -p 80:80 \
    -v /home/core/git/emoncms/emoncms:/var/www/emoncms \ 
    -v /home/core/git/emoncms/mysql:/var/lib/mysql \
    -v /home/core/git/emoncms/phpfiwa:/var/lib/phpfiwa \
    -v /home/core/git/emoncms/phpfina:/var/lib/phpfina \
    -v /home/core/git/emoncms/phptimeseries:/var/lib/phptimeseries \
    -v /home/core/git/emoncms/sessions:/var/lib/php5/sessions \
    -v /home/core/git/emoncms/supervisor:/etc/supervisor/conf.d \
    yourname/emoncms /bin/bash 
    ```

    Run in production
    ```bash
    /usr/bin/docker run -p 80:80 -v /home/core/git/emoncms/emoncms:/var/www/emoncms -v /home/core/git/emoncms/mysql:/var/lib/mysql -v /home/core/git/emoncms/phpfiwa:/var/lib/phpfiwa -v /home/core/git/emoncms/phpfina:/var/lib/phpfina -v /home/core/git/emoncms/phptimeseries:/var/lib/phptimeseries -v /home/core/git/emoncms/sessions:/var/lib/php5/sessions -v /home/core/git/emoncms/supervisor:/etc/supervisor/conf.d yourname/emoncms /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
    ```

