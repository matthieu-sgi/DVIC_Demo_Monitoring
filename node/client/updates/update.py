#!/bin/python3

import subprocess
import requests
import zipfile

# Download the version file from the server and compare it to the local version file
# If the server version is newer, download the new version and run it

VERSION_FILE_URL = 'http://localhost:8000/version'
UPDATE_FILE_URL = 'http://localhost:8000/update'
PATH = '/opt/dvic_log_server'
SERVICE_NAME = 'dvic_log_server'



def get_version():
    r = requests.get(VERSION_FILE_URL)
    return r.text


def get_local_version():
    with open('version', 'r') as f:
        return f.read()
    
# Methods to download the update zip archive and extract it to the current directory

def download_update():
    r = requests.get(UPDATE_FILE_URL)
    with open('update.zip', 'wb') as f:
        f.write(r.content)
    
def extract_update():
    with zipfile.ZipFile('update.zip', 'r') as zip_ref:
        zip_ref.extractall('.')

def restart_service():
    try :
        subprocess.run(['systemctl', 'restart', SERVICE_NAME])
    
    except OSError as e:
        print(e)
        print('Failed to restart service. Please restart manually.')
    
    except Exception as e:
        print(e)
        print('Failed to restart service. Please restart manually.')
        # TODO : push error to server. Through log ? 


# Main method to check for updates and download them if necessary

def check_for_updates():
    server_version = get_version()
    local_version = get_local_version()
    if server_version != local_version:
        print('New version available. Downloading...')
        download_update()
        print('Extracting...')
        extract_update()
        print('Restarting service...')
        restart_service()
        print('Done.')
    else:
        print('No updates available.')

    

if __name__ == '__main__':
    check_for_updates()
