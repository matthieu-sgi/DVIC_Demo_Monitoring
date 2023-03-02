'''Collectors for the DVIC node.'''

# import Queue
from multiprocessing import Queue

import asyncio
import subprocess
import threading
import os

class LogReader():
    '''Class used to handle the log reading
        ----- Parameters -----
        file_path : str = None
        journal_unit : str = None
    '''
    def __init__(self, file_path : str = None, journal_unit : str = None):
        self.file_path = file_path
        self.journal_unit = journal_unit
        self.process = None
        self.thread = None
        self.running = False
        self.queue : Queue = Queue()
    
    def read_loop(self):
        '''Read the log file'''
        while self.running:
            line = self.process.stdout.readline()
            if line:
                self.queue.put(line.decode('utf-8').strip())
    
    def launch(self):
        '''Launch the log reader'''
        if self.file_path is not None:
            self.process = subprocess.Popen(['tail', '-f', self.file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif self.journal_unit is not None:
            self.process = subprocess.Popen(['journalctl', '-f', '-u', self.journal_unit], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            raise Exception('No file path or journal unit specified')
        
        self.running = True
        self.thread = threading.Thread(target=self.read_loop, daemon=True)
        self.thread.start()

class LogReaderManager():
    def __init__(self):
        self.log_readers = []
    
    def add_log_reader(self, log_reader : LogReader):
        self.log_readers.append(log_reader)

    def launch_reader(self, log_reader : LogReader):
        log_reader.launch()
    
    

    












def get_machine_hardware_info():
    # Get system temperature
    counter = 0
    data = {}

    # Machine name 
    with open('/etc/hostname', 'r') as f:
        data["machine_name"] = f.read().strip()
    
    #FIXME Machine IP address ## Has to be fixed, only display the local IP address
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
    return data







def get_machine_software_info(*wanted_log_names : str):
    '''Get the software information of the DVIC node.
    The information include the IsAlive state of the demo process, the logs of the system, the status of the services, etc.'''
    #TODO : Check if the demo process is running, return the state of the demo process (IS_ALIVE, IS_DEAD, IS_NOT_RUNNING)
    #FIXME : convert the journal log to a readable format
    data = {}
    # older version of the code
    # special_files = ['dmesg', 'syslog']
    # # Get all .log files in the /var/log directory
    # log_files = []
    # for file in os.listdir('/var/log'):
    #     if file.endswith('.log') or file in special_files:
    #         log_files.append(file)
    
    # for log_file in log_files:
    #     with open(f'/var/log/{log_file}', 'r') as f:
    #         name_to_save = log_file.split('.')[0]
    #         data[name_to_save] = f.read()


    
    # # Fetch the log of journalctl
    # for dir in os.listdir('/var/log/journal'):
    #     for file in os.listdir(f'/var/log/journal/{dir}'):
    #         if file.endswith('.journal'):
    #             with open(f'/var/log/journal/{dir}/{file}', 'r') as f:
    #                 data[file] = f.read()





    return data
    

    # Get the status of the services
    





async def read_fifo(filename):
    with open(filename) as fifo:
        while True:
            data = fifo.readline()
            if not data:
                await asyncio.sleep(0.01)  # sleep for 10 milliseconds to avoid CPU spikes
            else:
                return data

async def fetch_fifos(path):
    '''Get the list of fifo files in the path, create a routine to read the fifo files and return the data read from the fifo files.
    Handle the creation of a new fifo file and put it in a routine'''
    #TODO : Get the fifo data in a blocking way in another thread
    fifo_files = []
    while True:
        for file in os.listdir(path):
            if file.endswith('.fifo'):
                fifo_files.append(file)

        
        # Create a routine to read the fifo files
        tasks = []
        for fifo_file in fifo_files:
            if fifo_file not in tasks:
                tasks.append(asyncio.create_task(read_fifo(fifo_file)))
        return await asyncio.gather(*tasks)
    
    



base_path = '/tmp/dvic_demo_log_fifo'


async def get_demo_logs():
    '''Get the logs of the demo processes. Fetch the logs from the fifo files.
    The fifo files are created by the demo processes and are located in /tmp/dvic_demo_log_fifo_<pid>'''

    # Get the list of fifo files
    return await fetch_fifos(base_path)


if __name__ == '__main__':
    print(get_machine_software_info())    

