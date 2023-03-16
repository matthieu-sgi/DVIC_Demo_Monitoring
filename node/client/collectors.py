'''Collectors for the DVIC node.'''

from abc import ABC, abstractmethod
from multiprocessing import Queue
from network.packets import Packet


import datetime
import subprocess
import threading
import time
import os

#################### Only for testing ####################
import logging


class DataAggregator(ABC): 
    '''Class used to handle the data aggregation'''

    def __init__(self):
        self.running = False
        self.process : subprocess.Popen = None
        self.thread : threading.Thread = None
        self.queue = Queue()
        self.packet : Packet = None

    @abstractmethod
    def _thread_target(self):
        '''Target for the thread'''
        raise NotImplementedError()
    
    @abstractmethod
    def get_logs(self) -> dict:
        '''Get the logs from the queue'''
        raise NotImplementedError()

    def launch(self):
        '''Launch the data aggregator
        Create a thread to read the data.'''      
        self.running = True
        self.thread = threading.Thread(target=self._thread_target, daemon=True)
        self.thread.start()
    
    def stop(self):
        '''Stop the data aggregator, kill the thread and the process (if any)'''
        if self.running:
            self.running = False
            # Set a timeout to avoid blocking
            if self.process is not None:
                self.process.kill()
                        
            self.thread.join(timeout=1)
    
    def create_packet(self):
        '''Create a packet with the data'''
        self.packet
        return self.packet

        


class LogReader(DataAggregator):
    '''Class used to handle the log reading
        ----- Parameters -----
        file_path : str = None
        journal_unit : str = None
    '''
    def __init__(self, *, file_path : str = None, journal_unit : str = None) -> None:
        super().__init__()
        self.file_path = file_path
        self.journal_unit = journal_unit
        self.process = self._define_process()
    
    def _define_process(self) -> subprocess.Popen:
        '''Define the process to use'''
        if self.file_path is not None:
            self.process = subprocess.Popen(['tail', '-f', self.file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif self.journal_unit is not None:
            self.process = subprocess.Popen(['journalctl', '-f', '-u', self.journal_unit], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            raise Exception('No file path or journal unit specified')

    
    def _thread_target(self)-> None:
        '''Read the log file'''
        while self.running:
            line = self.process.stdout.readline()
            if line:
                self.queue.put(line.decode('utf-8').strip())

    def get_type(self) -> str:
        '''Get the type of log reader'''
        if self.file_path is not None:
            return 'file'
        elif self.journal_unit is not None:
            return 'journal'
        else:
            return 'unknown'
    
    def get_logs(self) -> dict:
        '''Get the logs from the queue
        Return a dict with the logs
        
        ----- Return -----
        data : dict
        
        ----- Example -----
        if the log reader is a file reader:
        data = {
            'path' : '/var/log/syslog',
            0 : {
                'content' : 'Jan  1 00:00:00 machine_name message'
            }}
        if the log reader is a journal reader:
        data = {
            'unit' : 'systemd-journald',
            0 : {
                'date' : 'Jan  1',
                'time' : '00:00:00',
                'machine' : 'machine_name',
                'content' : 'message'
            }}
            '''
        # FIXME @Matthieu use subroutines
        data = {}
        if not self.queue.empty(): # Verify if the queue is not empty
            if self.get_type() == 'file': # Verify the type of log reader
                data['path'] = self.file_path # Add the path to the dict
            elif self.get_type() == 'journal':
                data['unit'] = self.journal_unit # Add the unit to the dict
            temp = {}
            size = self.queue.qsize() # Get the size of the queue, in order to give ids to the logs
            while not self.queue.empty(): # While the queue is not empty
                content = self.queue.get() # Get the content of the first log
                if self.get_type() == 'file': # Verify the type of log reader
                    temp['content'] = content # Add the content to the dict, 'content' is the key
                elif self.get_type() == 'journal': 
                    content = content.split(' ') # Split the content by spaces
                    temp['date'] = ' '.join(content[0:2]) # Add the date to the dict, 'date' is the key
                    temp['time'] = content[2] # Add the time to the dict, 'time' is the key
                    temp['machine'] = content[3] # Add the machine name to the dict, 'machine' is the key
                    temp['content'] = ' '.join(content[4:]) # Add the content to the dict, 'content' is the key

                # Add the dict to the data dict, the id (total queue_size- actual queue size ) is the key
                # Might be changed because it's not very efficient, maybe replace the id by a timestamp
                data[size - self.queue.qsize()] = temp 
        return data
    
    def __len__(self) -> int:
        '''Get the size of the queue'''
        return self.queue.qsize()
    

    

class HardwareInfo(DataAggregator):
    def __init__(self):
        super().__init__()
    
    def _thread_target(self):
        while self.running :
            data = {}
            data['machine_name'] = self._get_machine_name()
            data['ip'] = self._get_ip()
            data['temperature'] = self._get_temperature()
            data['cpu_usage'] = self._get_cpu_usage()
            data['memory_usage'] = self._get_memory_usage()
            self.queue.put(data)
            time.sleep(10)
    


    def _get_machine_name(self) -> str:
        '''Get the machine name'''
        data = ''
        with open('/etc/hostname', 'r') as f:
            data = f.read().strip()
        return data

    def _get_ip(self) -> str:
        '''Get the IP address of the machine'''
        # FIXME: Has to be fixed, only display the local IP address
        data = ''
        with open('/etc/hosts', 'r') as f:
            data = f.read().split()[0]
        return data
    

    def _get_temperature(self) -> dict:
        '''Get the temperature of the machine'''
        #Fetch list of directories in /sys/class/thermal
        dirs = os.listdir('/sys/class/thermal')
        #Filter out the directories that don't contain 'thermal_zone'
        dirs = [d for d in dirs if 'thermal_zone' in d]
        #Read the temperature from each directory
        temps = {}
        for dir in dirs:
            temp_name = ''
            temp_temp = 0
            with open(f'/sys/class/thermal/{dir}/type', 'r') as type_file:
                temp_name = type_file.read().strip()
            with open(f'/sys/class/thermal/{dir}/temp', 'r') as temp_file:
                temp_temp = float(temp_file.read()) / 1000
            temps[temp_name] = temp_temp
        return temps

    def _get_cpu_usage(self) -> float:
        '''Get the CPU usage'''
        with open('/proc/stat') as f:
            fields = [float(column) for column in f.readline().strip().split()[1:]]
        idle, total = fields[3], sum(fields)
        cpu_usage = round(100 * (1.0 - (float)(idle / total)), 2)
        return cpu_usage

    def _get_memory_usage(self) -> dict:
        '''Get the memory usage'''
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
        return memory_info
    
    def get_logs(self) -> dict:
        '''Get the logs from the queue. This empty the queue'''
        data = {}
        if not self.queue.empty():
            temp = {}
            while not self.queue.empty():
                content = self.queue.get()
                temp['content'] = content
                data[datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")] = temp
        return data
        
        
    # def _get_disk_usage(self) -> dict: 
    # TODO : depends on the python version, if it's 3.3 or higher, we could use shutil library of use general psutil library. Is it native ? 
    # 
    #     '''Get the disk usage'''
    #     disk_usage = {}
    #     for partition in psutil.disk_partitions():
    #         if partition.fstype == 'ext4':
    #             disk_usage[partition.mountpoint] = psutil.disk_usage(partition.mountpoint)
    #    return disk_usage
    
    

class DataAggregatorManager(): # ? What do you think about the changes of this class ? Feel better
    def __init__(self) -> None:
        self.data_aggregators = []
    
    def add_data_aggregator(self, data_aggregators : DataAggregator) -> None:
        self.log_readers.append(data_aggregators)
    
    def launch_data_aggregator(self, data_aggregator : DataAggregator) -> None:
        data_aggregator.launch()
    
    def launch_all(self) -> None:
        for data_aggregator in self.data_aggregators:
            self.launch_data_aggregator(data_aggregator)
    
    def stop_all(self) -> None:
        for data_aggregator in self.data_aggregators:
            data_aggregator.stop()
    
    def __get__(self, index : int) -> DataAggregator:
        return self.data_aggregators[index]

    def __set__(self, index : int, data_aggregator : DataAggregator) -> None:
        self.data_aggregators[index] = data_aggregator
    
    
if __name__ == '__main__': # Only for testing

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")
    logging.info("Main    : before creating thread")

    hard = HardwareInfo()
    hard.launch()

    try :
        while True:
            # logging.info(f'manual : {process.stdout.readline().decode("utf-8").strip()}')
            logs = hard.get_logs()
            if logs:
                logging.info(f'Logs : {logs}')
            time.sleep(1)
            continue
    except KeyboardInterrupt:
        hard.stop()
        logging.info('Main    : all done')
















