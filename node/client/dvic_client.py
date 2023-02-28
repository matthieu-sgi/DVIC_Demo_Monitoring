'''Client for the DVIC log server. Run as system service on the DVIC node.'''

import json
from multiprocessing import Queue
import os
import subprocess
import traceback
from typing import NoReturn
from client.network.packets import Packet, decode as decode_packet, PacketInteractiveSession
from threading import Thread

from websocket import create_connection, WebSocketApp
import logging
from client.interactive_session import InteractiveSession

DEFAULT_UID = "1d1f0545-2b60-488e-9419-d54b23bda47d" #fixed for testing
DEFAULT_ENDPOINT = 'wss://dvic.devinci.fr/demo_control/ws/'

class DVICClient:
    '''Client for the DVIC log server. Run as system service on the DVIC node.'''
    def __init__(self):        
        self.send_queue = Queue()
        self.interactive_sessions: dict[str, InteractiveSession] = {}
        self.ws = WebSocketApp(self.url, on_open=self.on_open, on_message=self.on_message, on_close=self.on_close, on_error=self.on_error)

    def _send_thread_target(self):
        try:
            while True:
                pck: Packet = self.send_queue.get()
                self.ws.send(pck.encode())
        except:
            traceback.print_exc()
            try: self.ws.close()
            except: pass

    @property
    def url(self) -> str:
        base = os.environ.get('WEBSOCKET_URL') or DEFAULT_ENDPOINT
        if not base.endswith('/'): base = f'{base}/'
        uid  = os.environ.get('DVIC_MACHINE_UID') or DEFAULT_UID
        return f'{base}{uid}'

    def send_packet(self, pck: Packet):
        self.send_queue.put(pck)

    def receive_packet(self, pck: Packet):
        getattr(self, f'_handle_{pck.identifier}')(pck)

    def run(self) -> NoReturn:
        self.ws.run_forever()

    def on_open(self, ws: WebSocketApp):
        logging.info(f"[CONNECTION] Connected to {self.url}")
        Thread(target=self._send_thread_target).run()

    def on_message(self, ws: WebSocketApp, data: str):
        self.receive_packet(decode_packet(data))

    def on_close(self, ws: WebSocketApp, sts, msg):
        logging.error(f'[CONNECTION] Ws closed with message: {msg}. Status is {sts} ')


    # / / / / / handlers

    def _handle_interactive_session(self, pck: PacketInteractiveSession):
        uid = pck.uuid
        if uid in self.interactive_sessions:
            iss: InteractiveSession = self.interactive_sessions[uid]
            iss.push(pck.value)
        else:
            self.interactive_sessions[uid] = InteractiveSession(pck.executable, uid, self)
            self.interactive_sessions[uid].launch()
    
    def _unregister_interactive_session(self, session: InteractiveSession):
        if session.uid in self.interactive_sessions:
            del self.interactive_sessions[session.uid]

    #TODO @Matthieu implement the rest of the handlers
   
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
    logging.info(f'[PRGM] Starting DVIC Demo Watcher Node')
    client = DVICClient()
    client.run()

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
    # print(client.get_machine_software_info())

