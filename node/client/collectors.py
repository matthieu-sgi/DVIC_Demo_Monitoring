'''Collectors for the DVIC node.'''

# import Queue
from multiprocessing import Queue

import datetime
import subprocess
import threading
import os

#################### Only for testing ####################
import logging
import time




class DataAggregator():
    '''Class used to handle the data aggregation'''

    def __init__(self):
        self.running = False
        self.process : subprocess.Popen = None
        self.queue = Queue()

    def _thread_target(self):
        '''Target for the thread'''
        raise NotImplementedError

    def launch(self):
        '''Launch the data aggregator
        Create a thread to read the data.'''      
        self.running = True
        self.thread = threading.Thread(target=self._thread_target, daemon=True)
        self.thread.start()
    
    def stop(self):
        '''Stop the data aggregator, kill the thread and the process (if any)'''
        self.running = False
        # Set a timeout to avoid blocking
        if self.process is not None:
            self.process.kill()
        self.thread.join(timeout=1)
        if self.process is not None:
            self.process.wait(timeout=1)
        

    def get_logs(self):
        '''Get the logs from the log readers'''
        raise NotImplementedError





class LogReader(DataAggregator):
    '''Class used to handle the log reading
        ----- Parameters -----
        file_path : str = None
        journal_unit : str = None
    '''
    def __init__(self, *, file_path : str = None, journal_unit : str = None, hardware_info : str = None) -> None:
        super().__init__()
        self.file_path = file_path
        self.journal_unit = journal_unit
        self.process = self._define_process()
        self.thread = None
    
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
        '''Get the logs from the queue'''
        data = {}
        if not self.queue.empty():
            if self.get_type() == 'file':
                data['path'] = self.file_path
            elif self.get_type() == 'journal':
                data['unit'] = self.journal_unit
            temp = {}
            size = self.queue.qsize()
            # print(self.queue.qsize())
            while not self.queue.empty():
                content = self.queue.get()
                if self.get_type() == 'file':
                    temp['content'] = content
                elif self.get_type() == 'journal':
                    content = content.split(' ')
                    temp['date'] = ' '.join(content[0:2])
                    temp['time'] = content[2]
                    temp['machine'] = content[3]
                    temp['content'] = ' '.join(content[4:])

                
                data[size - self.queue.qsize()] = temp
        return data
    
    def __len__(self):
        return self.queue.qsize()
    
class LogReaderManager():
    def __init__(self) -> None:
        self.log_readers = []
    
    def add_log_reader(self, log_reader : LogReader) -> None:
        self.log_readers.append(log_reader)

    def launch_reader(self, log_reader : LogReader) -> None:
        log_reader.launch()
    
    def launch_all(self) -> None:
        for log_reader in self.log_readers:
            self.launch_reader(log_reader)

    def stop_all(self) -> None:
        for log_reader in self.log_readers:
            log_reader.stop()
    
    def get_logs(self, log_reader : LogReader) -> dict: #FIXME : Has to be changed depending on the usage
        return log_reader.get_logs()
    

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
    


    def _get_machine_name(self) -> str:
        # Machine name
        data = ''
        with open('/etc/hostname', 'r') as f:
            data = f.read().strip()
        return data

    def _get_ip(self) -> str:
        # Machine IP address # FIXME: Has to be fixed, only display the local IP address
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
        data = {}
        if not self.queue.empty():
            temp = {}
            while not self.queue.empty():
                content = self.queue.get()
                temp['content'] = content
                data[ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")] = temp
        return data
        
        
    # def _get_disk_usage(self) -> dict: 
    # TODO : depends on the python version, if it's 3.3 or higher, we could use shutil library of use general psutil library. Is it native ? 
    # 
    #     '''Get the disk usage'''
    #     disk_usage = {}
    #     for partition in psutil.disk_partitions():
    #         if partition.fstype == 'ext4':
    #             disk_usage[partition.mountpoint] = psutil.disk_usage(partition.mountpoint)
    #     return disk_usage
    
    

    
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
















