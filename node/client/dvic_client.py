'''Client for the DVIC log server. Run as system service on the DVIC node.'''
from __future__ import annotations

import asyncio
import json
import subprocess

from websocket import create_connection




class DVICClient:
    '''Client for the DVIC log server. Run as system service on the DVIC node.'''
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ws = None
    
    def send_str(self, message : str):
        self.ws.send(message)

    def send_json(self, message : dict):
        self.ws.send(message)
        response = self.ws.recv()
        while response != message:
            print(f'Error: Message received: {response}')
            self.ws.send(message)
            response = self.ws.recv()

        print(f'Message received: {response}')


    def create_json_message(self, message_type : str, data_dict : dict) -> json:
        return json.dumps({
            'type': message_type,
            'data': data_dict
        })
    
    def receive(self):
        return self.ws.recv()
    
    def receive_json(self):
        return json.loads(self.ws.recv(), object_hook=dict)

    
    def handle_server_message(self):
        message = self.receive_json()
        print(f'Message received: {message}')
        print(type(message) )
        if message['type'] in MESSAGE_TYPES_CLIENT:
            if MESSAGE_TYPES_CLIENT[message['type']] is not None:
                MESSAGE_TYPES_CLIENT[message['type']](message['data'])
            else:
                print(f'No callback function for message type {message["type"]}')
        else:
            print(f'Unknown message type {message["type"]}')

    @staticmethod
    def execute_shell_command(data : dict):
        '''Execute a shell command on the DVIC node.'''
        command = data['command']
        print(f'Executing shell command: {command}')
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            for line in process.stdout:
                print(line)
            for line in process.stderr:
                print(line)

    
    def close(self):
        self.ws.close(status=1000, reason='Client closed connection.')
    
    def __enter__(self):
        self.ws = create_connection(f'ws://{self.host}:{self.port}/ws')
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

MESSAGE_TYPES_CLIENT = { # Put future callbacks handle functions here
    # For the client, the message types are likely to change
    'machine_hardware_state': None ,
    'machine_ log': None,
    'machine_demo_proc_sate': None,
    'machine_demo_log': None,
    'shell_command': DVICClient.execute_shell_command
}


if __name__ == '__main__':  
   with DVICClient('0.0.0.0', 9240) as client:

        print('Connected to DVIC log server.')
        input('Press enter to send json...')
        print('Sending data...')
        message = client.create_json_message('machine_hardware_state', {'test': 'test'})
        client.send_json(message)
        client.handle_server_message()
        print('Message sent.')
        input('Press enter to close connection...')
        print('Closing connection...')

    