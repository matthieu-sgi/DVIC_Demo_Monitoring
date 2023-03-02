'''This module is used to log data to a file'''

import os
import platform


base_path = f'/tmp/dvic_demo_log_fifo'
ISLINUX = (platform.system() == 'Linux')

def create_fifo():
    path = f'{base_path}_{os.getpid()}'
    if ISLINUX:
        if not os.path.exists(path):
            os.mkfifo(path)
        return path
    else:
        print('Your are not running on Linux, so the log will be printed to the console')

path = create_fifo()

def log(data : str):
    if ISLINUX:
        with open(path, 'a') as log_file:
            log_file.write('Log : ' + data)
    else:
        print('Log : ', data)

def error(data : str):
    if ISLINUX:
        with open(path, 'a') as log_file:
            log_file.write('Error : ' + data)
    else:
        print('Error : ', data)
    
def warning(data : str):
    if ISLINUX:
        with open(path, 'a') as log_file:
            log_file.write('Warning : ' + data)
    else:
        print('Warning : ', data)

