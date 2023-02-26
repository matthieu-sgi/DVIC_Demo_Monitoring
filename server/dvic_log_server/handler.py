'''Python module for handling messages from the client.'''
from server.dvic_log_server.network.packets import HardwareState, ShellCommandResponse, LogEntry, DemoProcState, InteractiveSession as InteractiveSessionPacket
import os


def hardware_state(data: HardwareState):
    '''Handle the machine hardware state message.'''
    print(f'Machine hardware state: {data}')

def log(data : LogEntry):
    '''Handle the machine log message.'''
    print(f'Machine log: {data}')

def demo_proc_state(data : DemoProcState):
    '''Handle the machine demo process state message.'''
    print(f'Machine demo process state: {data}')

def shell_command_response(data : ShellCommandResponse):
    '''Handle the machine shell command response message.'''
    print(f'Machine shell command response: {data}')



# Merged with machine_log into log
# def machine_demo_log(data : dict):
#     '''Handle the machine demo log message.'''
#     print(f'Machine demo log: {data}')