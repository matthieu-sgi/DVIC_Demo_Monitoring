#!/bin/env python3
import os
import argparse
import subprocess
import tarfile
import json

from tqdm import tqdm
import requests

TEMP_DOWNLOAD_PATH = '/tmp/dvic_monitor_latest.zip'
CONFIG_FILE = 'config.json'
SERVICE_NAME = 'dvic_demo_watcher.service'

class Installer:

    def __init__(self, key: str) -> None:
        self.config = self.load_config()
        self.key = key

    def load_config(self):
        with open(CONFIG_FILE, 'r') as fh:
            return json.loads(fh.read())

    @property
    def update_url(self):
        return os.path.join(self.config['latest_update_source'], self.key)
    
    # def restart_service():
    #     try :
    #         subprocess.run(['systemctl', 'restart', SERVICE_NAME])
        
    #     except OSError as e:
    #         print(e)
    #         print('Failed to restart service. Please restart manually.')
        
    #     except Exception as e:
    #         print(e)
    #         print('Failed to restart service. Please restart manually.')


    def install(self):
        print("[INSTALL] System Update Start")
        if os.path.isfile(TEMP_DOWNLOAD_PATH):
            os.unlink(TEMP_DOWNLOAD_PATH)
            print("[INSTALL] Deleted Local Download")


        with requests.get(self.update_url, headers={"Accept": "application/octet-stream"}, stream=True) as stream:
            stream.raise_for_status()
            total = int(stream.headers["Content-Length"])
            content = stream.iter_content(chunk_size=8192)

            with open(TEMP_DOWNLOAD_PATH, "wb") as fh:
                with tqdm(content, total=total, unit="B", unit_scale=True, unit_divisor=1_024) as pbar:
                    for chunk in pbar:
                        pbar.update(len(chunk))
                        fh.write(chunk)

        print("[INSTALL] Extracting Asset")
        tar = tarfile.open(TEMP_DOWNLOAD_PATH, "r:bz2")
        tar.extractall("./")
        tar.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--key', required=True)

    args = parser.parse_args()

    Installer(args.key).install()