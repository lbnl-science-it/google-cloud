#!/bin/bash

# autoexit on error in this script
set -e

# OVERVIEW
# This script stops a AI notebook server once it's idle for more than 1 hour (default time)
# You can change the idle time for stop using the environment variable below.
# If you want the notebook the stop only if no browsers are open, remove the --ignore-connections flag
#

# idle time in seconds - 3600 = one hour
IDLE_TIME=3600

echo "Fetching the auto-shutdown script"
curl -O https://raw.githubusercontent.com/lbnl-science-it/google-cloud/main/auto-shutdown/auto-shutdown.py

echo "Loading the auto-shutdown script in cron to run every 5 minutes"

(crontab -l 2>/dev/null; echo "5 * * * * /usr/bin/python $PWD/auto-shutdown.py --time $IDLE_TIME --ignore-connections") | crontab -
