'''Collectors for the DVIC node.'''

# import Queue
from multiprocessing import Queue

import subprocess
import threading
import os
import logging #### Only for testing

class LogReader():
    '''Class used to handle the log reading
        ----- Parameters -----
        file_path : str = None
        journal_unit : str = None
    '''
    def __init__(self, *, file_path : str = None, journal_unit : str = None):
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
            logging.info(f'Launching log reader for {self.file_path}')
            self.process = subprocess.Popen(['tail', '-f', self.file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif self.journal_unit is not None:
            logging.info(f'Launching log reader for {self.journal_unit}')
            self.process = subprocess.Popen(['journalctl', '-f', '-u', self.journal_unit], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            raise Exception('No file path or journal unit specified')
        
        self.running = True
        self.thread = threading.Thread(target=self.read_loop, daemon=True)
        self.thread.start()

    def get_type(self):
        '''Get the type of log reader'''
        if self.file_path is not None:
            return 'file'
        elif self.journal_unit is not None:
            return 'journal'
        else:
            return 'unknown'
    
    def get_logs(self):
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
    
    def stop(self):
        '''Stop the log reader'''
        self.running = False
        self.thread.join()
        self.process.kill()
        self.process.wait()

class LogReaderManager():
    def __init__(self):
        self.log_readers = []
    
    def add_log_reader(self, log_reader : LogReader):
        self.log_readers.append(log_reader)

    def launch_reader(self, log_reader : LogReader):
        log_reader.launch()
    
    def launch_all(self):
        for log_reader in self.log_readers:
            self.launch_reader(log_reader)

    def stop_all(self):
        for log_reader in self.log_readers:
            log_reader.stop()
    
    def get_logs(self, log_reader : LogReader): #FIXME : Has to be changed depending on the usage
        return log_reader.get_logs()
    
    

    
if __name__ == '__main__': # Only for testing

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")
    logging.info("Main    : before creating thread")

    log_reader = LogReader(journal_unit='docker.service')
    log_reader.launch()

    try :
        while True:
            # logging.info(f'manual : {process.stdout.readline().decode("utf-8").strip()}')
            logs = log_reader.get_logs()
            if logs:
                logging.info(f'Logs : {logs}')
            continue
    except KeyboardInterrupt:
        log_reader.running = False
        log_reader.thread.join()
        log_reader.process.kill()
        log_reader.process.wait()











def get_machine_hardware_info(): # TODO : Has to be merged with the new class. Not sur how to do it yet
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





