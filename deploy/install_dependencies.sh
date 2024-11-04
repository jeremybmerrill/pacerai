#!/bin/bash

set -e

source /home/ubuntu/tow-pacer/deploy/install_root_dependencies.sh

sudo chmod 777 -R /home/ubuntu/tow-pacer/deploy/
cd /home/ubuntu/tow-pacer/deploy/

# setup services
ls /home/ubuntu/tow-pacer/deploy/services | xargs -i sudo install -m u+rw,ugo-x,go-w,go+r services/"{}" "/lib/systemd/system/{}"
sudo systemctl daemon-reload
sudo systemctl enable courtlistener_search_warrant_alerter.timer # timers need both enable and start
sudo systemctl start courtlistener_search_warrant_alerter.timer # timers need both enable and start
sudo systemctl start courtlistener_search_warrant_alerter.service # run the service just once
sudo systemctl enable rss_search_warrant_alerter.timer # timers need both enable and start
sudo systemctl start rss_search_warrant_alerter.timer # timers need both enable and start
sudo systemctl start rss_search_warrant_alerter.service # run the service just once
sudo systemctl enable pacer_rss_scraper.timer # timers need both enable and start
sudo systemctl start pacer_rss_scraper.timer # timers need both enable and start
sudo systemctl start pacer_rss_scraper.service # run the service just once


# setup server
cd /home/ubuntu/tow-pacer/deploy/

# pull secrets
export $(grep -e '^[^#]' /home/ubuntu/.env | xargs)

sudo chmod 777 -R /home/ubuntu/tow-pacer/deploy/
pip3 install -U --user pip # default pip causes some problems
pip3 install --user  --no-cache-dir -r /home/ubuntu/tow-pacer/search_warrant_alerter/requirements.txt # no-cache-dir causes some problems
rm -rf /tmp/pacerporcupine/
