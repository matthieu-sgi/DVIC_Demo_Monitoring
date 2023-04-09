'''Test module for the python library'''

import pytest
from dvic_log import dvic_log
import os


def remove_fifo():
    '''Removes the fifo file'''
    if dvic_log.ISLINUX:
        os.remove(dvic_log.path)

def test_log():
    '''Test for the log function'''
    remove_fifo()
    dvic_log.log('test')

    # Check if the log is written to the file
    with open(dvic_log.path, 'r') as log_file:
        assert log_file.read() == 'Log : test'

def test_log_with_level():
    '''Test for the log function with a level'''
    remove_fifo()
    dvic_log.warning('test')
    dvic_log.error('test')

    # Check if the log is written to the file
    with open(dvic_log.path, 'r') as log_file:
       assert log_file.read() == 'Warning : test\nError : test'

if __name__ == '__main__':
    dvic_log.log('test')
    dvic_log.warning('test')
    dvic_log.error('test')


