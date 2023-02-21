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
    try:
        # Log the connection into the log file
        with open(os.path.join(os.path.dirname(__file__), '.logs/websockets_connection.log'), 'a') as log_file:
            log_file.write(f'New connection from {websocket.client.host}:{websocket.client.port}\n')
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await websocket.close()