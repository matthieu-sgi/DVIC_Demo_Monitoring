'''Client for the DVIC log server. Run as system service on the DVIC node.'''

import json
from multiprocessing import Queue
import os
from queue import Empty
import subprocess
import traceback
import atexit
from dataclasses import dataclass
from typing import NoReturn
from client.network.packets import Packet, decode as decode_packet, PacketInteractiveSession
from threading import Thread

from websocket import create_connection, WebSocket
import logging
from pathlib import Path
import requests
from client.interactive_session import InteractiveSession
from client.meta import AbstractDVICNode
from client.utils.crypto import CryptPhonebook, CryptClient

DEFAULT_UID = "1d1f0545-2b60-488e-9419-d54b23bda47d" #fixed for testing TODO: read from config.
DEFAULT_ENDPOINT = 'wss://dvic.devinci.fr/demo_control/ws/'

@dataclass
class ClientConfig():
    uid: str
    private_key_path: str
    server_root_path: str
    latest_install_source: str
    preauth_source: str

    def __str__(self):
        p = Path(self.private_key_path)
        return f'uid={self.uid}\nserver_root={self.server_root_path}\nprivate_key={self.private_key_path} exists={p.exists()}\npreauth_source={self.preauth_source}'

class DVICClient(AbstractDVICNode, CryptPhonebook):
    '''Client for the DVIC log server. Run as system service on the DVIC node.'''
    def __init__(self, config_file: str):        
        super().__init__()
        self.send_queue = Queue()
        self.config: ClientConfig = None
        self.interactive_sessions: dict[str, InteractiveSession] = {}
        self.read_config(config_file)


    def read_config(self, config_file: str):
        """
            uid: {{ NODE_UID }}
            private_key_path: /opt/dvic-demo-watcher/private.key
            server_root_path: {{ SERVER_ROOT_PATH }}
            preauth_source: {{ PREAUTH_SOURCE }}
            latest_install_source: {{ UPDATE_SOURCE }}
        """ 
        try:
            cfg = Path(config_file)
            if not cfg.exists(): raise RuntimeError(f'Config file {config_file} does not exist')
            self.config = ClientConfig(**json.loads(cfg.read_bytes()))
            print("[STARTUP] Config loaded")
            print(f"[STARTUP] Config:\n{self.config}")

        except: 
            traceback.print_exc()
            print("[STARTUP] Config not loaded")

    def get_public_key(self,  uid: str) -> str: return None # client only needs private key
    def get_client_salt(self, _: str) -> str: return None
    def set_client_salt(self, uid: str, salt: str) -> None: return

    def _craft_auth_token(self): 
        if not self.is_secure_auth_enabled():
            print(f'[AUTH] Bypassing auth')
            return self.uid
        
        cc = CryptClient(private_key=self.config.private_key_path)
        p_answer = requests.get(f'{self.config.preauth_source}{self.uid}').json()
        if not 'preauth_key' in p_answer:
            print(f"[CONNECTION] Pre-auth failed: {p_answer}")
            return None
        token = cc.craft_initial_token(self.uid, p_answer['preauth_key'])
        print(f'[CONNECTION] Attempting login with token {token}')
        return token

    def _send_thread_target(self):
        try:
            while True:
                pck: Packet = self.send_queue.get(True)
                self.ws.send(pck.encode())
        except:
            traceback.print_exc()
            try: self.ws.close()
            except: pass

    @property
    def uid(self) -> str:
        return self.config.uid if self.config else os.environ.get('DVIC_MACHINE_UID') or DEFAULT_UID

    @property
    def url(self) -> str:
        base = self.config.server_root_path or os.environ.get('WEBSOCKET_URL') or DEFAULT_ENDPOINT
        if not base.endswith('/'): base = f'{base}/'
        return f'{base}'

    def send_packet(self, pck: Packet):
        self.send_queue.put(pck)

    def receive_packet(self, pck: Packet):
        try: getattr(self, f'_handle_{pck.identifier}')(pck)
        except: traceback.print_exc()

    def teardown(self):
        self.ws.close()


    def run(self) -> None:
        auth_token = self._craft_auth_token()
        url = self.url + auth_token
        print(f'[STARTUP] Connection to {url}')
        self.ws: WebSocket = create_connection(url)
        print(f'[STARTUP] Connected')
        
        # TODO moveatexit.register(self.exit_handler)
        self.send_thread = Thread(target=self._send_thread_target,  daemon=True)
        self.recp_thread = Thread(target=self._recpt_thread_target, daemon=True)
        
        self.send_thread.start()
        self.recp_thread.start()

        from time import sleep
        while True:
            sleep(1)
            if not self.ws.connected:
                print("[CONNECTION] Disconnected")
                break



    def _recpt_thread_target(self):
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

    def execute_shell_command(self, command: str) -> None:
        '''Execute a shell command on the DVIC node.'''
        print(f'Executing shell command: {command}') 
        stdout, stderr = None, None
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            stdout, stderr = process.communicate()
        self.create_json_message('shell_command_response', {'stdout': stdout.decode('utf-8'), 'stderr': stderr.decode('utf-8')}) # send packet directly with return uid 
