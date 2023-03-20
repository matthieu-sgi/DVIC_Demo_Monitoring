'''Collectors for the DVIC node.'''

from abc import ABC, abstractmethod
from client.network.packets import Packet, PacketHardwareState, PacketMachineLog, PacketLogEntry
from client.dvic_client import DVICClient, AbstractDVICNode


import datetime
import subprocess
import threading
import time
import os

#################### Only for testing ####################
import logging


class DataAggregator(ABC): 
    '''Class used to handle the data aggregation'''

    def __init__(self, client : AbstractDVICNode):
        self.running = False
        self.process : subprocess.Popen = None
        self.thread : threading.Thread = None
        self.client : AbstractDVICNode = client

    @abstractmethod
    def _thread_target(self):
        '''Target for the thread used to get the data, transform it into a packet and send it to the server'''
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


        


class LogReader(DataAggregator):
    '''Class used to handle the log reading
        ----- Parameters -----
        file_path : str = None
        journal_unit : str = None
    '''
    def __init__(self, client : AbstractDVICNode, *, file_path : str = None, journal_unit : str = None) -> None:
        super().__init__(client)
        self.file_path = file_path
        self.journal_unit = journal_unit
        self.process = self._define_process()
        print("Proc started")
    
    def _define_process(self) -> subprocess.Popen:
        '''Define the process to use'''

        if self.file_path is not None:
            return subprocess.Popen(['tail', '-f', self.file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True) #TODO @Matthieu just in case tail is actually not installed, use a pure python logic
        elif self.journal_unit is not None:
            return subprocess.Popen(['journalctl', '-f', '-u', self.journal_unit], stdout=subprocess.PIPE, stderr=subprocess.PIPE) #NOTE journaltcl is installed on all systemd managed machines
        else:
            raise Exception('No file path or journal unit specified')

    
    def _thread_target(self)-> None:
        """Read from the log file.
        Get a dict with the data collected from the log file
        Create a packet and send it to the server

        Returns
        -------
        None

        Data sent
        ---------
        The data sent to the server looks like
        ```
        {
            'kind': 'file or systemd' 
            'name' : '/var/log/syslog',
            'log': value
        }
        ```

        Where `kind` can be "file" if the log is watching a file or "systemd" if the object is watching a systemd unit
        `logs` can contain multiple lines

        """
        while self.running:
            content = self.process.stdout.readline().decode()
            if content:
                kind, name = self._get_reader_type_with_target()
                data = {'kind': kind, 'name': name}
                if data['kind'] == 'journal': 
                    content = ' '.join(content.split(' ')[4:]) 
                data['log'] = content
                self.client.send_packet(PacketLogEntry(**data))              



    def _get_reader_type_with_target(self) -> tuple[str]:
        if self.file_path is not None:
            return 'file', self.file_path
        elif self.journal_unit is not None:
            return 'journal', self.journal_unit
        else:
            raise RuntimeError()



HARDWARE_INFO_ENUM = ['machine_name', 'ip', 'temperature', 'cpu_usage', 'memory_usage']


class HardwareInfo(DataAggregator):
    def __init__(self, client : AbstractDVICNode) -> None:
        super().__init__(client)
    
    def _thread_target(self) -> None:
        while self.running :
            gen = self.get_hardware_info()
            for data in gen:
                print(data)
                packet = PacketHardwareState(**data)
                self.client.send_packet(packet)
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
    
    def get_hardware_info(self,*, info : str | list[str] = None) -> dict:
        '''Get the logs from the queue. This empty the queue'''
        # TODO : transform this into a generator that fecth the logs and yield them

        # Verify if info is included in the enum
        if info is not None and info not in HARDWARE_INFO_ENUM:
            raise ValueError(f'Invalid info type, must be in {HARDWARE_INFO_ENUM}')
        if info is None:
            info = HARDWARE_INFO_ENUM
        elif isinstance(info, str):
            info = [info]
        for i in info:
            data = {'kind' : i, 'data' : {}}
            data['data'] = getattr(self, f'_get_{i}')()
            yield data

        
        
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
        self.data_aggregators : list[DataAggregator] = []
    
    def add_data_aggregator(self, data_aggregators : DataAggregator) -> None:
        self.data_aggregators.append(data_aggregators)
    
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

    hard = HardwareInfo(None)
    
    for i in hard.get_hardware_info():
        print(i)
















