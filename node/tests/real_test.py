'''Testing the whole pipeline of DVIC'''


from client.dvic_client import  DVICClient
from client.collectors import HardwareInfo, DataAggregatorManager, LogReader

if __name__ == '__main__':
    client = DVICClient()
    manager = DataAggregatorManager()
    manager.add_data_aggregator(LogReader(file_path='/var/log/syslog'))
    manager.add_data_aggregator(LogReader(journal_unit='systemd-journald'))
    manager.add_data_aggregator(HardwareInfo())

    
    client.run()