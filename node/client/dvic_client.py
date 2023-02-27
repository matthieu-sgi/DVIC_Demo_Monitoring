'''Client for the DVIC log server. Run as system service on the DVIC node.'''

import json
import os
import subprocess
from typing import NoReturn

from websocket import create_connection, WebSocketApp

path = f'/tmp/dvic_demo_log_fifo'

class DVICClient:
    '''Client for the DVIC log server. Run as system service on the DVIC node.'''
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ws = WebSocketApp(self.url, on_open=self.on_open, on_message=self.on_message, on_close=self.on_close)

    def run(self) ->  NoReturn:
        self.ws.run_forever()


    def on_open(self, ws: WebSocketApp):
        pass

    def on_message(self, ws: WebSocketApp, data: str):
        pass

    def on_close(self, ws: WebSocketApp):
        pass


   
    # def handle_server_message(self):
    #     message = self.receive_json()
    #     print(f'Message received: {message}')
    #     if message['type'] in self.MESSAGE_TYPES_CLIENT:
    #         if self.MESSAGE_TYPES_CLIENT[message['type']] is not None:
    #             self.send_json(self.MESSAGE_TYPES_CLIENT[message['type']](message['data']))
    #         else:
    #             print(f'No callback function for message type {message["type"]}')
    #     else:
    #         print(f'Unknown message type {message["type"]}')



    
    def execute_shell_command(self, data : dict):
        '''Execute a shell command on the DVIC node.'''
        command = data['command']
        print(f'Executing shell command: {command}')
        stdout, stderr = None, None
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            stdout, stderr = process.communicate()
        return self.create_json_message('shell_command_response', {'stdout': stdout.decode('utf-8'), 'stderr': stderr.decode('utf-8')})



if __name__ == '__main__':  
   with DVICClient('0.0.0.0', 9240) as client:

        # print('Connected to DVIC log server.')
        # input('Press enter to send json...')
        # print('Sending data...')
        # # message = client.create_json_message('machine_hardware_state', {'test': 'test'})
        # # client.send_json(message)
        # print(client.get_machine_hardware_info())
        # input('Press enter to send json...')
        # client.send_json(client.get_machine_hardware_info())
        # print('Message sent.')
        # client.handle_server_message()
        # input('Press enter to close connection...')
        # print('Closing connection...')
        print(client.get_machine_software_info())

    