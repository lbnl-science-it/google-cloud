import requests
from datetime import datetime
import getopt, sys
import urllib3
import os
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Read in command-line parameters
parser = argparse.ArgumentParser(
    description='This scripts checks if all the notebooks running are idle for more than X seconds and, if they are, it''ll shutdown the server',
    allow_abbrev=False)

parser.add_argument('-t', '--time', type=int, default=3600, 
	help='Time in seconds when determining max idle time to cause shutdown (3600 is the default)')
parser.add_argument('-p', '--port', type=int, default=8080,
	help='Jupyter port (8080 is the default)')
parser.add_argument('-c', '--ignore-connections', action='store_true', 
	help='Ignore connected users when testing for idle')
args = parser.parse_args()

# default settings and parameters via command line
idle = True
datetime_format = "%Y-%m-%dT%H:%M:%S.%fz"
time = args.time
port = args.port
ignore_connections = args.ignore_connections

def get_settings_filepath():
    dirpath, filename = os.path.split(__file__)
    filename = '.' + filename.split('.')[0]
    filepath = os.path.join(dirpath, filename)
    
    return filepath

def store_last_activity(last_activity):
    file = get_settings_filepath()
    
    # if file doesn't exist, create and load with now
    with open(file, 'w') as f:
        f.write(last_activity.strftime(datetime_format))
    
def get_last_activity():
    # if there's no activity file at all, save one that's marked as now.
    # figuring if you install this, then you're going to get going ASAP, but well within the timeout window
    file = get_settings_filepath()
    
    # if file doesn't exist, create and load it with now so we have some time on a reboot
    # to launch the notebook
    if not os.path.isfile(file):
        store_last_activity(datetime.now())

    with open(file, 'r') as f:
        last_activity = f.read().strip()

    # return converted to UTC datetime
    return datetime.strptime(last_activity, datetime_format)

def is_idle(last_activity):
    if (datetime.now() - last_activity).total_seconds() > time:
        print('Notebook is idle. Last activity time = ', last_activity)
        return True
    else:
        print('Notebook is not idle. Last activity time = ', last_activity)
        return False

most_recent_activity = get_last_activity()

# This is hitting Jupyter's sessions API: https://github.com/jupyter/jupyter/wiki/Jupyter-Notebook-Server-API#Sessions-API
url = 'http://localhost:{}/api/sessions'.format(port)
response = requests.get(url, verify=False)
data = response.json()
if len(data) > 0:
    for notebook in data:
        # Idleness is defined by Jupyter
        # https://github.com/jupyter/notebook/issues/4634
        if notebook['kernel']['execution_state'] == 'idle':
            last_activity = datetime.strptime(notebook['kernel']['last_activity'], datetime_format)
                
            if ignore_connections:
                if not is_idle(last_activity):
                    idle = False
            else:
                if notebook['kernel']['connections'] == 0:
                    if not is_idle(last_activity):
                        idle = False
                else:
                    idle = False

            # track most recent activity
            if last_activity > most_recent_activity:
                most_recent_activity = last_activity
            
        else:
            print('Notebook is not idle:', notebook['kernel']['execution_state'])
            idle = False
else:
    # no kernels running, but we still need to check when the last time one was run
    if not is_idle(get_last_activity()):
        idle = False

if idle:
    # kill activity tracking file due to shutdown, so that it doesn't just shutdown again on restart
    print('Closing idle notebooks and shutting down server')
    os.remove(get_settings_filepath())
    os.system("sudo shutdown -hP now")
else:
    print('Notebook not idle. Pass.')
    # save most recent activity, if different
    if most_recent_activity > get_last_activity():
        store_last_activity(most_recent_activity)

