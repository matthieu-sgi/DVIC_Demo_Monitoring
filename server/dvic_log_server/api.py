'''API module for the DVIC log and monitor server.'''

import traceback
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import uuid
import json
import asyncio
import os

from dvic_log_server.connection import Connection
from dvic_log_server.network.packets import Packet, decode as decode_packet
from dvic_log_server.utils import singleton


app = FastAPI()



@singleton
class ConnectionManager:
    def __init__(self):
        self.connections = {}
        self.log_path = os.path.dirname(os.path.realpath(__file__))
        #remove the 'dvic_log_server' part of the path
        self.log_path = self.log_path[:self.log_path.rfind('/')]
    
    def __setitem__(self, uid: str, connection: Connection) -> None:
        if connection is None:
            pass #TODO trigger disconnection 
        
        if uid in self.connections and connection is not None:
            print(f'[{uid}] Replacing connection')
            #TODO behavior on connection overlap?

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

    
@app.websocket("/ws/{uid}") #TODO identifier in initial request?
async def websocket_endpoint(websocket: WebSocket, uid: str):
    # uid = str(uuid.uuid4()) # uid  generated here, to auth a connection. #TODO use preset uuid to handle connection reset
    #TODO add authentication later
    conn = Connection(websocket, uid)
    ConnectionManager()[uid] = conn 

    async def receive_packets():
        while True:
            try:
                conn.receive_packet(decode_packet(await websocket.receive_text()))
            except WebSocketDisconnect: return
            except: 
                if conn.is_disconnected(): return
                traceback.print_exc()

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
        print(f"[{uid}] Send loop closing")

    loop = asyncio.get_running_loop()
    try:
        await websocket.accept()      
        print(f"[{uid}] Accepted connection from {websocket.client.host}")

        # rect = loop.create_task(receive_packets())
        send: asyncio.Task = loop.create_task(send_packets())
        while True:
            try:
                conn.receive_packet(decode_packet(await websocket.receive_text()))
            except: 
                if conn.is_disconnected(): break
                traceback.print_exc()
                try: await websocket.close()
                except: pass

    except WebSocketDisconnect:
        print('[{uid}] Err: disconnected')
    send.cancel()
    print(f"[{uid}] Disconnected")
    ConnectionManager()[uid] = None
