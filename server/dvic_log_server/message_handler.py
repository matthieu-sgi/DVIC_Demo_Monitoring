'''Python module for handling messages from the client.'''

import os


def machine_hardware_state(data : dict):
    '''Handle the machine hardware state message.'''
    print(f'Machine hardware state: {data}')

def machine_log(data : dict):
    '''Handle the machine log message.'''
    print(f'Machine log: {data}')

def machine_demo_proc_state(data : dict):
    '''Handle the machine demo process state message.'''
    print(f'Machine demo process state: {data}')

def machine_demo_log(data : dict):
    '''Handle the machine demo log message.'''
    print(f'Machine demo log: {data}')