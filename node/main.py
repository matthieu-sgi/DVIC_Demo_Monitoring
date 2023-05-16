#!/usr/bin/env python3
import argparse
import sys
from client.dvic_client import DVICClient
import traceback
from time import sleep

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", type=str, default="./config.json", help="Config file location")

    args = parser.parse_args()

    while True:
        try:
            print(f'[STARTUP] Starting DVIC Demo Watcher Node')
            client = DVICClient(args.config)
            client.run() # will run until disconnected
            client.teardown()
        except:
            traceback.print_exc()
        print('[CONNECTION] Waiting 5 seconds before reconnection')
        sleep(5)