'''API module for the DVIC log and monitor server.'''

import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect


app = FastAPI()

MESSAGE_TYPES = { # Put future callbacks handle functions here
    'machine_hardware_state': None ,
    'machine_ log': None,
    'machine_demo_proc_sate': None,
    'machine_demo_log': None
}

class ConnectionManager:
    def __init__(self):
        self.active_connections = []
        self.log_path = os.path.dirname(os.path.realpath(__file__))
        #remove the 'dvic_log_server' part of the path
        self.log_path = self.log_path[:self.log_path.rfind('/')]
        self.log_path = os.path.join(self.log_path, '.logs/websockets_connection.log')

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        with open(self.log_path, 'a') as log_file:
            log_file.write(f'New connection from {websocket.client.host}:{websocket.client.port}\n')
            print("Logged connection to file")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        with open(self.log_path, 'a') as log_file:
            log_file.write(f'Connection closed from {websocket.client.host}:{websocket.client.port}\n')
            print("Logged disconnection to file")
    
    def get_log_path(self):
        return self.log_path

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    print(f'New connection from {websocket.client.host}:{websocket.client.port}')
    try:
        
        while True:
            data = await websocket.receive_json(mode = 'text')
            print(f"Received message: {data} + len(data) = {len(data)}")
            if len(data) > 0 :
               await websocket.send_json(data) 
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        try: await websocket.close()
        except: pass # ignore exception as we are just making sure the connection is closed before returning