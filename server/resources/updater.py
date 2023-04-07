#!/bin/env python3
from tqdm import tqdm
import os
import sys
import requests
import tarfile
import yaml
import os

TEMP_DOWNLOAD_PATH = '/tmp/dvic_monitor_latest.zip'
CONFIG_FILE = './config.yml'

class Installer:

    def __init__(self) -> None:
        self.config = self.load_config()

    def load_config(self):
        with open(CONFIG_FILE, 'r') as fh:
            return yaml.safe_load(fh)

    @property
    def update_url(self):
        return self.config['latest_update_source']

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
    Installer().install()