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

def handle_interactive_session_packet(pck: InteractiveSessionPacket):
    #TODO:
    # if interactive session does not exist
    #  if this is initial packet with target machine and executable
    #   create interactive session, this sends the initial packet
    #   subscribe sender
    #   return
    # if this is ret_value (final) packet
    #   kill session, remove session, return
    # push data normally
    pass




# Merged with machine_log into log
# def machine_demo_log(data : dict):
#     '''Handle the machine demo log message.'''
#     print(f'Machine demo log: {data}')