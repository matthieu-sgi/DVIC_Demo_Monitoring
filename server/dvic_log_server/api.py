'''API module for the DVIC log and monitor server.'''

import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect


app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    print(f'New connection from {websocket.client.host}:{websocket.client.port}')
    try:
        # Log the connection into the log file
        path = os.path.dirname(os.path.realpath(__file__))
        #remove the 'dvic_log_server' part of the path
        path = path[:path.rfind('/')]
        with open(os.path.join(path, '.logs/websockets_connection.log'), 'a') as log_file:
            log_file.write(f'New connection from {websocket.client.host}:{websocket.client.port}\n')
            print("Logged connection to file")
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await websocket.close()