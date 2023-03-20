'''Testing the whole pipeline of DVIC'''


from client.dvic_client import  DVICClient
from client.collectors import HardwareInfo, DataAggregatorManager, LogReader

if __name__ == '__main__':
    client = DVICClient()
    manager = DataAggregatorManager()
    # log_r = LogReader(client = client, file_path='/home/wanikatako/audrey.txt')
    # log_r = HardwareInfo(client=client)
    # manager.add_data_aggregator(log_r)
    log_r_2 = LogReader(client = client, journal_unit='systemd-journald')
    manager.add_data_aggregator(log_r_2)
    manager.launch_all()
    client.run()
    # manager.add_data_aggregator (LogReader(client = client, journal_unit='systemd-journald'))
    # manager.add_data_aggregator (HardwareInfo(client=client))
    # manager.launch_all()
    