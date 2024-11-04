#!/bin/bash

set -e

cd /home/ubuntu

sudo apt-get update -y

sudo apt-get install -y autoconf bison
sudo apt-get install -y libssl-dev
sudo apt-get install -y python3-pip
sudo apt-get install postgresql postgresql-contrib
