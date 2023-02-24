"""
Workbench to test some code
"""

from subprocess import Popen
from threading import Thread

import subprocess
import os
import sys
import tty
import pty

tty.setcbreak(sys.stdin.fileno()) # read stdin char by char
unbuffered_stdin = os.fdopen(sys.stdin.fileno(), 'rb', buffering=0) # disable buffering, read in binary mode

def read_proco(a):
    # reads process stdout to console
    print('Writing')
    while True:
        b = os.read(a, 1024)
        print(b.decode('utf-8'), end='', flush=True)

def read_stdin(a):
    # reads python stdin character by character
    while True:
        c = unbuffered_stdin.read(10)
        os.write(a, c)

if __name__ == '__main__':
    master, slave = pty.openpty() # ptty for session handling
    a = Popen(["/bin/bash"], shell=False, start_new_session=True, stdin=slave, stdout=slave, stderr=slave, bufsize=0) # notice buffering, session_start
    Thread(target=read_proco, args=(master,), daemon=True).start()
    Thread(target=read_stdin, args=(master,), daemon=True).start()
    while True:
        try: rt = a.wait(1); break
        except subprocess.TimeoutExpired: pass
        
    print(f'Process exited with code {rt} ')
    exit(0)