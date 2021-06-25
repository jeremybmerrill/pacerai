#!/bin/bash

set -e

source /home/ubuntu/tow-pacer/infra/deploy/install_root_dependencies.sh

sudo chmod 777 -R /home/ubuntu/tow-pacer/infra/deploy/
cd /home/ubuntu/tow-pacer/infra/deploy/

# setup services
ls /home/ubuntu/tow-pacer/infra/deploy/services | xargs -i sudo install -m u+rw,ugo-x,go-w,go+r services/"{}" "/lib/systemd/system/{}"
sudo systemctl daemon-reload
sudo systemctl enable courtlistener_search_warrant_alerter.service
sudo systemctl start courtlistener_search_warrant_alerter.service
sudo systemctl enable rss_search_warrant_alerter.timer
sudo systemctl start rss_search_warrant_alerter.timer


# setup server
cd /home/ubuntu/tow-pacer/infra/deploy/

# pull secrets
export $(cat /home/ubuntu/.env | xargs)

sudo chmod 777 -R /home/ubuntu/tow-pacer/infra/deploy/
pip3 install -U --user pip # default pip causes some problems
pip3 install --user  --no-cache-dir -r /home/ubuntu/tow-pacer/search_warrant_alerter/requirements.txt # no-cache-dir causes some problems
rm -rf /tmp/pacerporcupine/
