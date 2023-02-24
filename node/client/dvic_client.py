'''Client for the DVIC log server. Run as system service on the DVIC node.'''
from __future__ import annotations

import json
import subprocess

from websocket import create_connection


class DVICClient:
    '''Client for the DVIC log server. Run as system service on the DVIC node.'''
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ws = None
    
    def send_str(self, message : str):
        self.ws.send(message)

    def send_json(self, message : dict):
        self.ws.send(message)
        response = self.ws.recv()
        while response != message:
            print(f'Error: Message received: {response}')
            self.ws.send(message)
            response = self.ws.recv()

        print(f'Message received: {response}')


    def create_json_message(self, message_type : str, data_dict : dict) -> json:
        return json.dumps({
            'type': message_type,
            'data': data_dict
        })
    
    def receive(self):
        return self.ws.recv()
    
    def receive_json(self):
        return json.loads(self.ws.recv(), object_hook=dict)

    
    def handle_server_message(self):
        message = self.receive_json()
        print(f'Message received: {message}')
        if message['type'] in MESSAGE_TYPES_CLIENT:
            if MESSAGE_TYPES_CLIENT[message['type']] is not None:
                MESSAGE_TYPES_CLIENT[message['type']](message['data'])
            else:
                print(f'No callback function for message type {message["type"]}')
        else:
            print(f'Unknown message type {message["type"]}')

    def get_machine_hardware_info(self):
        # Get system temperature
        counter = 0
        data = {}

        # Machine name 
        with open('/etc/hostname', 'r') as f:
            data["machine_name"] = f.read().strip()
        
        # Machine IP address ## Has to be fixed, only display the local IP address
        with open('/etc/hosts', 'r') as f:
            data["machine_ip"] = f.read().split()[0]


        temps = {}
        while True :
            try:
                temp_name = ''
                temp_temp = 0
                with open(f'/sys/class/thermal/thermal_zone{counter}/type', 'r') as type_file:
                    temp_name = type_file.read().strip()
                with open(f'/sys/class/thermal/thermal_zone{counter}/temp', 'r') as temp_file:
                    temp_temp = float(temp_file.read()) / 1000
                temps[temp_name] = temp_temp
                counter += 1
            except FileNotFoundError:
                break
        data["temperature"] = temps
        
        with open('/proc/stat') as f:
            fields = [float(column) for column in f.readline().strip().split()[1:]]
        idle, total = fields[3], sum(fields)
        cpu_usage = 100 * (1.0 - (float)(idle / total))
        data["cpu_usage"] = cpu_usage

        # Get system memory
        with open('/proc/meminfo') as f:
            meminfo = dict((i.split()[0].rstrip(':'), int(i.split()[1])) for i in f.readlines())
        mem_total = meminfo['MemTotal']
        mem_free = meminfo['MemFree']
        mem_available = meminfo['MemAvailable']
        mem_used = 100 * (1.0 - (float)(mem_available / mem_total))
        memory_info = {
            'total': mem_total,
            'free': mem_free,
            'available': mem_available,
            'used': mem_used
        }
        data["memory_info"] = memory_info


    def close(self):
        self.ws.close(status=1000, reason='Client closed connection.')
    
    def __enter__(self):
        self.ws = create_connection(f'ws://{self.host}:{self.port}/ws')
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @staticmethod
    def execute_shell_command(data : dict):
        '''Execute a shell command on the DVIC node.'''
        command = data['command']
        print(f'Executing shell command: {command}')
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            for line in process.stdout:
                print(line)
            for line in process.stderr:
                print(line)

MESSAGE_TYPES_CLIENT = { # Put future callbacks handle functions here
    # For the client, the message types are likely to change
    'shell_command': DVICClient.execute_shell_command
}


if __name__ == '__main__':  
   with DVICClient('0.0.0.0', 9240) as client:

        print('Connected to DVIC log server.')
        input('Press enter to send json...')
        print('Sending data...')
        message = client.create_json_message('machine_hardware_state', {'test': 'test'})
        client.send_json(message)
        client.handle_server_message()
        print('Message sent.')
        input('Press enter to close connection...')
        print('Closing connection...')

    