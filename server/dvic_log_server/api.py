'''API module for the DVIC log and monitor server.'''

from fastapi import FastAPI, WebSocket, WebSocketDisconnect


import json
import dvic_log_server.message_handler as message_handler
import os


app = FastAPI()

MESSAGE_TYPES_SERVER = { # Put future callbacks handle functions here
    'machine_hardware_state': message_handler.machine_hardware_state,
    'machine_ log': message_handler.machine_log,
    'machine_demo_proc_sate': message_handler.machine_demo_proc_state,
    'machine_demo_log': message_handler.machine_demo_log,
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
    
    def _create_json_message(self, message_type : str, data_dict : dict) ->  json:
        return json.dumps({
            'type': message_type,
            'data': data_dict
        })
    
    def handle_client_message(self, message : json):
        if message['type'] in MESSAGE_TYPES_SERVER:
            if MESSAGE_TYPES_SERVER[message['type']] is not None:
                MESSAGE_TYPES_SERVER[message['type']](message['data'])
            else:
                print(f'No callback function for message type {message["type"]}')
        else:
            print(f'Unknown message type {message["type"]}')

    async def send_shell_command(self, websocket : WebSocket,  command : str):
        message = self._create_json_message('shell_command', {'command': command})
        await websocket.send_text(message)
    
    def get_log_path(self):
        return self.log_path

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    '''Endpoint for the websocket connection.'''
    await manager.connect(websocket)
    print(f'New connection from {websocket.client.host}:{websocket.client.port}')
    try:
        while True:
            data = await websocket.receive_json(mode = 'text')
            print(f"Received message: {data} + len(data) = {len(data)}")
            if len(data) > 0 :
               await websocket.send_json(data)
            await manager.send_shell_command(websocket, 'ls -l')
            
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        try: await websocket.close()
        except: pass # ignore exception as we are just making sure the connection is closed before returning