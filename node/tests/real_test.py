'''Testing the whole pipeline of DVIC'''


from client.dvic_client import DVICClient
from client.collectors import HardwareInfo, DataAggregatorManager, LogReader

import os


if __name__ == '__main__':
    client = DVICClient()
    manager = DataAggregatorManager()

    # Testing the hardware info collector
    # hi = HardwareInfo(client=client)
    # manager.add_data_aggregator(hi)

    # Testing the log reader collector
    log_r_2 = LogReader(client = client, journal_unit='systemd-journald')
    manager.add_data_aggregator(log_r_2)

    log_r_3 = LogReader(client = client, journal_unit='nm_dispatcher')
    manager.add_data_aggregator(log_r_3)

    log_r_4 = LogReader(client = client, journal_unit='systemd-udevd')
    manager.add_data_aggregator(log_r_4)

    log_r_5 = LogReader(client = client, journal_unit='systemd-timesyncd')
    manager.add_data_aggregator(log_r_5)

    log_r_6 = LogReader(client = client, journal_unit='systemd-networkd')
    manager.add_data_aggregator(log_r_6)

    log_r_7 = LogReader(client = client, journal_unit='systemd-resolved')
    manager.add_data_aggregator(log_r_7)

    log_r_8 = LogReader(client = client, journal_unit='systemd-logind')
    manager.add_data_aggregator(log_r_8)

    log_r_9 = LogReader(client = client, journal_unit='systemd-hostnamed')
    manager.add_data_aggregator(log_r_9)

    log_r_10 = LogReader(client = client, journal_unit='systemd-tmpfiles-clean')
    manager.add_data_aggregator(log_r_10)
    # Testing the log
    # Get the name of the log file 
    # files = os.listdir('/tmp/dvic_demo_log_fifo')
    # if len(files) != 1:
    #     raise RuntimeError()
    # log_file_name = files[0]
    # log_proc = LogReader(client = client, file_path=log_file_name)


    manager.launch_all()
    client.run()
    