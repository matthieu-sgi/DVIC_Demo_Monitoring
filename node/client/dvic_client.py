'''Client for the DVIC log server. Run as system service on the DVIC node.'''

import json
import subprocess

from websocket import create_connection


class DVICClient:
    '''Client for the DVIC log server. Run as system service on the DVIC node.'''
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ws = None
        self.MESSAGE_TYPES_CLIENT = { # Put future callbacks handle functions here
        # For the client, the message types are likely to change
        'shell_command': self.execute_shell_command
        }
    
    def send_str(self, message : str):
        self.ws.send(message)

    def send_json(self, message : dict) -> int:
        self.ws.send(message)
        response = self.ws.recv()
        while response != message:
            # print(f'Error: Message received: {response}')
            self.ws.send(message)
            response = self.ws.recv()
        return 1
        # print(f'Message received: {response}')


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
        if message['type'] in self.MESSAGE_TYPES_CLIENT:
            if self.MESSAGE_TYPES_CLIENT[message['type']] is not None:
                self.send_json(self.MESSAGE_TYPES_CLIENT[message['type']](message['data']))
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
        cpu_usage = round(100 * (1.0 - (float)(idle / total)), 2)
        data["cpu_usage"] = cpu_usage

        # Get system memory
        with open('/proc/meminfo') as f:
            meminfo = dict((i.split()[0].rstrip(':'), int(i.split()[1])) for i in f.readlines())
        mem_total = meminfo['MemTotal']
        mem_free = meminfo['MemFree']
        mem_available = meminfo['MemAvailable']
        mem_used = round(100 * (1.0 - (float)(mem_available / mem_total)), 2)
        memory_info = {
            'total': mem_total,
            'free': mem_free,
            'available': mem_available,
            'used': mem_used
        }
        data["memory_info"] = memory_info
        return self.create_json_message("machine_hardware_state",data)
    
    def get_machine_software_info(self):
        '''Get the software information of the DVIC node (demo proc IsAlive).'''

        # Fetch the state of the demo process
        stdout, stderr = None, None
        with subprocess.Popen('ps -A | grep demo', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            stdout, stderr = process.communicate()
        
        return [stdout.decode('utf-8'), stderr.decode('utf-8')]


    def close(self):
        self.ws.close(status=1000, reason='Client closed connection.')
    
    def __enter__(self):
        self.ws = create_connection(f'ws://{self.host}:{self.port}/ws')
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()





    
    def execute_shell_command(self, data : dict):
        '''Execute a shell command on the DVIC node.'''
        command = data['command']
        print(f'Executing shell command: {command}')
        stdout, stderr = None, None
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            stdout, stderr = process.communicate()
        return self.create_json_message('shell_command_response', {'stdout': stdout.decode('utf-8'), 'stderr': stderr.decode('utf-8')})




if __name__ == '__main__':  
   with DVICClient('0.0.0.0', 9240) as client:

        # print('Connected to DVIC log server.')
        # input('Press enter to send json...')
        # print('Sending data...')
        # # message = client.create_json_message('machine_hardware_state', {'test': 'test'})
        # # client.send_json(message)
        # print(client.get_machine_hardware_info())
        # input('Press enter to send json...')
        # client.send_json(client.get_machine_hardware_info())
        # print('Message sent.')
        # client.handle_server_message()
        # input('Press enter to close connection...')
        # print('Closing connection...')
        print(client.get_machine_software_info())

    