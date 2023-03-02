'''API module for the DVIC log and monitor server.'''

import traceback
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import asyncio
import os

from dvic_log_server.connection import Connection
from dvic_log_server.network.packets import Packet, decode as decode_packet
from dvic_log_server.utils import singleton


app = FastAPI()

@singleton
class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, Connection] = {}
        self.log_path = os.path.dirname(os.path.realpath(__file__))
        #remove the 'dvic_log_server' part of the path
        self.log_path = self.log_path[:self.log_path.rfind('/')]
    
    def __setitem__(self, uid: str, connection: Connection) -> None:
        if connection is None:
            pass #TODO trigger disconnection 
        
        if uid in self.connections:
            if connection is not None:
                print(f'[{uid}] Replacing connection')
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

    def __getitem__(self, uid: str) -> Connection:
        if uid not in self.connections: return None
        return self.connections[uid]
    
    # def handle_client_message(self, message : json):
    #     if message['type'] in MESSAGE_TYPES_SERVER:
    #         if MESSAGE_TYPES_SERVER[message['type']] is not None:
    #             MESSAGE_TYPES_SERVER[message['type']](message['data'])
    #         else:
    #             print(f'No callback function for message type {message["type"]}')
    #     else:
    #         print(f'Unknown message type {message["type"]}')

@app.get('/install/{install_token}')
def installer_download(install_token: str):
    """
    Initiates download of the pre-packaged installer with UID set to a generated UID for the new node.
    The install_token is a one-time unique token generated when receiving a PacketNodeCreation
    """

    pass
    
@app.websocket("/ws/{uid}/{conn_token}") #TODO identifier in initial request?
async def websocket_endpoint(websocket: WebSocket, uid: str):
    # uid = str(uuid.uuid4()) # uid  generated here, to auth a connection. #TODO use preset uuid to handle connection reset
    #TODO add authentication later
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
        await websocket.accept()      
        print(f"[{uid}] Accepted connection from {websocket.client.host}")

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
        print(f'[{uid}] Err: disconnected')
    conn.in_use = False #FIXME put in a method
    send.cancel()
    print(f"[{uid}] Disconnected")
    ConnectionManager()[uid] = None
