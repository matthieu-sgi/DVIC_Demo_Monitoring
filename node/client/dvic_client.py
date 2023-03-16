'''Client for the DVIC log server. Run as system service on the DVIC node.'''

import json
from multiprocessing import Queue
import os
import subprocess
import traceback
import atexit
from typing import NoReturn
from client.network.packets import Packet, decode as decode_packet, PacketInteractiveSession
from threading import Thread

from websocket import create_connection, WebSocket
import logging
from client.interactive_session import InteractiveSession
from client.meta import AbstractDVICNode

DEFAULT_UID = "1d1f0545-2b60-488e-9419-d54b23bda47d" #fixed for testing TODO: read from config.
DEFAULT_ENDPOINT = 'wss://dvic.devinci.fr/demo_control/ws/'

class DVICClient(AbstractDVICNode):
    '''Client for the DVIC log server. Run as system service on the DVIC node.'''
    def __init__(self):        
        super().__init__()
        self.send_queue = Queue()
        self.interactive_sessions: dict[str, InteractiveSession] = {}
        print(f'[STARTUP] Connection to {self.url}')
        self.ws: WebSocket = create_connection(self.url)
        print(f'[STARTUP] Connected')
        
    def _send_thread_target(self):
        try:
            print("Starting send thread") #FIXME remove
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
        try: getattr(self, f'_handle_{pck.identifier}')(pck)
        except: traceback.print_exc()

    def exit_handler(self):
        self.ws.close()

    def run(self) -> NoReturn:
        atexit.register(self.exit_handler)
        Thread(target=self._send_thread_target,  daemon=True).start()
        Thread(target=self._recpt_thread_target, daemon=True).start()
        input() #TODO local console?

    # def on_open(self, ws: WebSocketApp):
    #     logging.info(f"[CONNECTION] Connected to {self.url}")

    def _recpt_thread_target(self):
        print('Receiving...') #FIXME remove
        while True:
            try:
                data = self.ws.recv()
                if data is None: return #EOF 
                self.receive_packet(decode_packet(data))
            except:
                traceback.print_exc()
                if not self.ws.connected: return

    # def on_data(self, ws: WebSocketApp, data: str, data_type, more):
    #     if more == 0:
    #         print("Expect trouble")
    #     print(data)
    #     self.receive_packet(decode_packet(data))

    # def on_close(self, ws: WebSocketApp, sts, msg):
    #     logging.error(f'[CONNECTION] Ws closed with message: {msg}. Status is {sts} ')

    # / / / / / handlers

    def _handle_interactive_session(self, pck: PacketInteractiveSession):
        uid = pck.uuid
        if uid in self.interactive_sessions:
            iss: InteractiveSession = self.interactive_sessions[uid]
            iss.push(pck.value)
        else:
            #TODO refuse if more than xx sessions
            self.interactive_sessions[uid] = InteractiveSession(pck.executable, uid, self)
            print(f'[SESSION] Launching interactive session {uid}')
            self.interactive_sessions[uid].launch()
    
    def _unregister_interactive_session(self, uid: str):
        if uid in self.interactive_sessions:
            del self.interactive_sessions[uid]

    #TODO @Matthieu implement the rest of the handlers
   

    
    def execute_shell_command(self, command: str) -> None:
        '''Execute a shell command on the DVIC node.'''
        print(f'Executing shell command: {command}') 
        stdout, stderr = None, None
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            stdout, stderr = process.communicate()
        self.create_json_message('shell_command_response', {'stdout': stdout.decode('utf-8'), 'stderr': stderr.decode('utf-8')}) # send packet directly with return uid 



if __name__ == '__main__':
    print(f'[STARTUP] Starting DVIC Demo Watcher Node')
    client = DVICClient()
    client.run()
