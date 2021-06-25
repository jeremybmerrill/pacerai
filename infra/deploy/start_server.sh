#!/bin/bash

set -e

service courtlistener_search_warrant_alerter restart
service rss_search_warrant_alerter restart
