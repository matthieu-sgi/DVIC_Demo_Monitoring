from threading import Thread
from subprocess import Popen
import subprocess
import os
import pty
from typing import NoReturn
import traceback

import logging
from client.meta import AbstractDVICNode

from client.network.packets import PacketInteractiveSession

class InteractiveSession:
    def __init__(self, target: str, uid: str, client: AbstractDVICNode) -> None:
        self.target_executable: str = target
        self.uid = uid # global IS UID as seen on API
        self.input_buffer = os.pipe()
        
        self.client: AbstractDVICNode = client
        self.running = True

    def push(self, c: bytes):
        os.write(self.input_buffer[1], c)

    def _read_process(self, a):
        while self.running:
            self.client.send_packet(PacketInteractiveSession(uuid=self.uid, value=os.read(a, 1024)))

    def _read_input_buffer(self, a):
        while self.running:
            os.write(a, os.read(self.input_buffer[0], 10))

    def _send_termination(self, ret: int, msg: str = None):
        self.client.send_packet(PacketInteractiveSession(uuid=self.uid, return_value=ret, value=msg))
        self.client._unregister_interactive_session(self.uid)

    def kill(self) -> None:
        self.process_obj.kill()

    def launch(self) -> None:
        Thread(target=self.run, daemon=True).start()

    def run(self) -> int:
        logging.info(f'[SESSION] Starting session {self.uid} with cmd {self.target_executable}')
        msg = None # termination message
        try:
            master, slave = pty.openpty() # ptty for session handling
            self.process_obj = Popen([self.target_executable], shell=False, start_new_session=True, stdin=slave, stdout=slave, stderr=slave, bufsize=0) # notice buffering, session_start
            Thread(target=self._read_process,      args=(master,), daemon=True).start()
            Thread(target=self._read_input_buffer, args=(master,), daemon=True).start()            
            self.process_obj.wait() # wait here for process termination
        except Exception as e:
            traceback.print_exc()
            msg = f'Exception {type(e)} in session: {str(e)}'

        # Process exited, teardown the session
        rt = self.process_obj.returncode
        print(f'[SESSION] Session {self.uid} terminated with code {rt}')
        self.running = False
        self._send_termination(rt, msg)
        return rt
