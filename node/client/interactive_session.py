from threading import Thread
from subprocess import Popen
import subprocess
import os
import pty
from typing import NoReturn
import io, _io

import client.dvic_client as dvc

class InteractiveSession:
    def __init__(self, target: str, uid: str, client: dvc.DVICClient) -> None:
        self.target_executable: str = target
        self.uid = uid # global IS UID as seen on API
        r, w, = os.pipe()
        r, w = os.fdopen(r, "rw"), os.fdopen(w, "wb")
        self.input_buffer = r, w
        self.client: dvc.DVICClient = client

    def push(self, c: bytes):
        self.input_buffer[1].write(c)

    def read_proco(self, a):
        while True:
            b = os.read(a, 1024) 
            #TODO send packet with b
            # print(b.decode('utf-8'), end='', flush=True)

    def read_input_buffer(self, a):
        # reads python stdin character by character
        buf: _io.BufferedReader = self.input_buffer[0]
        while True:
            c = buf.read()
            os.write(a, c)

    def launch(self) -> NoReturn:
        master, slave = pty.openpty() # ptty for session handling
        a = Popen([self.target_executable], shell=False, start_new_session=True, stdin=slave, stdout=slave, stderr=slave, bufsize=0) # notice buffering, session_start
        Thread(target=self.read_proco,        args=(self, master), daemon=True).start()
        Thread(target=self.read_input_buffer, args=(self, master), daemon=True).start()
        while True:
            try: rt = a.wait(1); break
            except subprocess.TimeoutExpired: pass

        #TODO send termination packet
