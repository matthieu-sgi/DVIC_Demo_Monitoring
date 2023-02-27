'''This module is used to log data to a file'''

import os

path = f'/tmp/dvic_demo_log_fifo'


def create_fifo():
    try: 
        os.mkfifo(path)
    except OSError as oe:
        print(f'FIFO already exists: {oe}')


def log(data : str):
    with open(path, 'a') as log_file:
        log_file.write('Log : ' + data)

def error(data : str):
    with open(path, 'a') as log_file:
        log_file.write('Error : ' + data)
    
def warning(data : str):
    with open(path, 'a') as log_file:
        log_file.write('Warning : ' + data)


