import sys
import os    
import tty
import io
import threading
import uuid
import traceback

from colorama import Fore, Back, Style
from dvic_demo_cli.network.packets import PacketInteractiveSession
from dvic_demo_cli.meta import DVICDemoWatcherCliBase
from multiprocessing import Lock

class InteractiveSession():
    def __init__(self, client: DVICDemoWatcherCliBase, target_machine: str, executable: str = "/bin/bash", uid = None) -> None:
        self.client = client
        self.running = True
        self.uuid = uid if uid is not None else str(uuid.uuid4())
        self.executable = executable
        self.target_machine = target_machine
        self.wait_lock = Lock()
        self.stdin: io.FileIO = None

    def get_unbuffered_stdin(self) -> io.FileIO:
        tty.setcbreak(sys.stdin.fileno()) # read stdin char by char
        return os.fdopen(sys.stdin.fileno(), 'rb', buffering=0) # disable buffering, read in binary mode

    def _send_packet(self, **kwargs):
        self.client.send_packet(PacketInteractiveSession(uuid=self.uuid, **kwargs))

    def _print_termination_message(self, ret: int, msg: str):
        if msg is None: msg = f'[CLI] Session terminated with code {ret}'
        color = f'{Fore.RED}{Style.BRIGHT}' if ret != 0 else f'{Fore.GREEN}'
        print(f'{color}{msg}{Style.RESET_ALL}')

    def receive_packet(self, pck: PacketInteractiveSession) -> bool:
        if pck.return_value is not None:
            # terminate session
            self._print_termination_message(pck.return_value, pck.value.decode() if pck.value is not None else None)
            self.running = False
            self.stdin.close() # force read thread exit
            self.wait_lock.release() #restore stdin?
            return True
        # just print
        print(pck.value.decode('utf-8'), end="", flush=True)
        return False

    def _read_stdin_thread_target(self):
        self.stdin = self.get_unbuffered_stdin()
        while self.running:
            try:
                c = self.stdin.read(1)
                self._send_packet(value=c)
            except:
                if not self.running: return
                traceback.print_exc()
        
    def wait(self):
        self.wait_lock.acquire(block=True)
        self.wait_lock.release()

    def _launch_frontend(self) -> None:
        self.wait_lock.acquire(block=False) #TODO handle
        threading.Thread(target=self._read_stdin_thread_target, daemon=True).start()

    def join(self) -> None:
        self._launch_frontend()
        print(f'[{self.uuid}] Attempting to join session... (press any key)')
        self._send_packet(action="register")

    def launch(self) -> None:
        self._launch_frontend()
        print(f'[{self.uuid}] Launching {self.executable} on {self.target_machine}')
        self._send_packet(target_machine=self.target_machine, executable=self.executable)