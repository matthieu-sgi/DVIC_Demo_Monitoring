'''API module for the DVIC log and monitor server.'''

import traceback
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import asyncio
import os
import json
from pathlib import Path
from dataclasses import dataclass

from dvic_log_server.meta import AConnection
from dvic_log_server.network.packets import Packet, PacketNodeAdditionRequest, decode as decode_packet
from dvic_log_server.utils.wrappers import singleton
from dvic_log_server.utils.crypto import CryptClient, CryptPhonebook
from dvic_log_server.interactive_sessions import ScriptInteractiveSession

from dvic_log_server.logs import info, warning, error, debug

app = FastAPI()

@dataclass
class ServerConfig():
    server_private_key_path: str  #? not using double auth, so server private key is not used at the moment. Would be a nice to have
    keys_save_path: str = "./keys"

@singleton
class ConnectionManager(CryptPhonebook):
    def __init__(self):
        self.config = None
        self.connections: dict[str, AConnection] = {}
        self.log_path = os.path.dirname(os.path.realpath(__file__))
        #remove the 'dvic_log_server' part of the path
        self.log_path = self.log_path[:self.log_path.rfind('/')]
        self.load_config()
        self.salt_dic = {}
        if not self.is_secure_auth_enabled():
            self.private_key_path = None
            warning(f'The API is configured to IGNORE cryptographic client authentication. DO NOT do this in a production setting.')
    
    def __setitem__(self, uid: str, connection: AConnection) -> None:    
        if uid in self.connections:
            if connection is not None:
                debug(f'[{uid}] Replacing connection')
                self.connections[uid].close()
                connection.inherit(self.connections[uid])
                #TODO behavior on connection overlap? testing
            else:
                if not self.connections[uid].is_disconnected(): 
                    return # don't replace connection with None if the connection was replaced before the disconnection #! is_disconnected_ is borked

        if connection is None:
            del self.connections[uid]
            return
        self.connections[uid] = connection

    def load_config(self):
        if not os.path.isfile("config.json"):
            with open("config.json", 'w+') as fh:
                fh.write(ServerConfig())
        try:
            with open("config.json") as fh:
                self.config = ServerConfig(**json.loads(fh.read()))
            info("Config loaded")
        except:
            traceback.print_exc()
            error('Failed to load server config')

    def get_public_key(self, uid: str) -> str:
        pkp = Path(self.config.keys_save_path, uid)
        if not pkp.exists(): return None
        return pkp.read_text()

    def __getitem__(self, uid: str) -> AConnection:
        if uid not in self.connections: return None
        return self.connections[uid]
    
    def get_client_salt(self, uid: str) -> str:
        return self.salt_dic[uid]
    
    def set_client_salt(self, uid: str, salt: str) -> None:
        self.salt_dic[uid] = salt
    
    # def add_node_addition_request(self, source_node_uid: str, hostname: str, )

    # def handle_client_message(self, message : json):
    #     if message['type'] in MESSAGE_TYPES_SERVER:
    #         if MESSAGE_TYPES_SERVER[message['type']] is not None:
    #             MESSAGE_TYPES_SERVER[message['type']](message['data'])
    #         else:
    #             print(f'No callback function for message type {message["type"]}')
    #     else:
    #         print(f'Unknown message type {message["type"]}')

# @app.get('/install/{install_token}')
# def installer_download(install_token: str):
#     """
#     Initiates download of the pre-packaged installer with UID set to a generated UID for the new node.
#     The install_token is a one-time unique token generated when receiving a PacketNodeCreation
#     """

#     pass

# @app.get('/install_script/uid_node={uid}')
# def installer_script(uid : str):
#     """
#     Returns the installer script for the node.
#     ---------
#     args:
#         uid: the UID of the node installer
#         target_ip: the IP of the node that will be installed
#     """
#     path = f'./dvic_log_server/utils/install_script.sh'
#     file_content = ''
#     with open(path, 'r') as f:
#         file_content = f.read()
#     interactive_session = ScriptInteractiveSession(uid = uid,
#                                                     target_machine = target_ip,
#                                                     script_content = file_content)
#     interactive_session.run_script()           


    
    

@app.get('/preauth/{uid}')
def get_salt(uid):
    cm: CryptPhonebook = ConnectionManager()
    if not cm.is_secure_auth_enabled():
        debug(f'[AUTH] Ignore pre auth')
        return {'message': 'Pre-auth is disabled'}
    if cm.get_public_key(uid) is None:
        warning(f"[AUTH] Rejected preauth for {uid} (no such UID)")
        return {'message': 'UID unknown'}
    
    salt = CryptClient.get_salt()
    cm.set_client_salt(uid, salt)
    info(f'[AUTH] Preauth for {uid}: {salt}')
    return {"preauth_key": salt}

    
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    cm = ConnectionManager()
    cry = CryptClient(private_key = cm.config.server_private_key_path)
    uid, packet_ok = cry.verify_initial_packet(token, cm)

    await websocket.accept()
    if not packet_ok or False: #FIXME testing
        warning(f'[CONNECTION] ({uid}) ({websocket.client.host}) Connection token rejected')
        await websocket.send_text(f'Connection token rejected.')
        await websocket.close()
        return

    from dvic_log_server.connection import Connection # needed for init but cannot import before or cycle dependencies
    conn = Connection(websocket, uid)
    ConnectionManager()[uid] = conn 

    async def send_packets():
        while True:
            try:
                await asyncio.sleep(1/120)
                if conn.is_disconnected(): return
                pck = conn.next_packet()
                if pck is None: continue
                await websocket.send_text(pck.encode())
                
            except WebSocketDisconnect: break
            except asyncio.CancelledError: break
            except: traceback.print_exc()
        # print(f"[{uid}] Send loop closing")

    loop = asyncio.get_running_loop()
    try:
        info(f"[{uid}] Accepted connection from {websocket.client.host}")

        # rect = loop.create_task(receive_packets())
        send: asyncio.Task = loop.create_task(send_packets())
        while True:
            try:
                conn.receive_packet(decode_packet(await websocket.receive_text()))
            except WebSocketDisconnect: raise
            except: 
                if conn.is_disconnected(): break
                traceback.print_exc()
                try: await websocket.close()
                except: pass

    except WebSocketDisconnect:
        error(f'[{uid}] Err: disconnected')
    conn.in_use = False #FIXME put in a method
    send.cancel()
    ConnectionManager()[uid] = None
    warning(f"[{uid}] Connection Closed")
