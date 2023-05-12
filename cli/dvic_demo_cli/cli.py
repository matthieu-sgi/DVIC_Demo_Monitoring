import argparse
import os
import traceback
import uuid

from threading import Thread
from multiprocessing import Queue
from dvic_demo_cli.interactive_session import InteractiveSession
from dvic_demo_cli.meta import DVICDemoWatcherCliBase
from dvic_demo_cli.network.packets import *
from websocket import create_connection, WebSocket

DEFAULT_ENDPOINT = 'wss://dvic.devinci.fr/demo_control/ws/'

class DVICDemoWatcherCli(DVICDemoWatcherCliBase):
    def __init__(self) -> None:
        super().__init__()
        self.uid = os.environ.get("DEMO_WATCHER_UID") or str(uuid.uuid4())
        self.send_queue = Queue()
        self.sessions: dict[str, InteractiveSession] = {}
        print(f'[STARTUP] Connection to {self.url}')
        self.ws: WebSocket = create_connection(self.url)
        Thread(target=self._packet_reception_thread_target, daemon=True).start()
        Thread(target=self._packet_send_thread_target, daemon=True).start()

    @property
    def url(self) -> str:
        base = os.environ.get('WEBSOCKET_URL') or DEFAULT_ENDPOINT
        if not base.endswith('/'): base = f'{base}/'
        return f'{base}{self.uid}' #FIXME use crypto

    def __enter__(self):
        return self
    
    def __exit__(self, a, b, c):
        self.close()

    def _packet_reception_thread_target(self):
        while True:
            data = self.ws.recv()
            if data is None or len(data) == 0: return #EOF
            pck: Packet = decode(data)
            self.receive_packet(pck)

    def _packet_send_thread_target(self):
        while True:
            try:
                pck: Packet = self.send_queue.get()
                self.ws.send(pck.encode())
            except:
                traceback.print_exc()

    def request_node_list(self):
        self.send_packet(PacketNodeStatus(action=NodeStatusAction.LIST_NODES))

    def receive_packet(self, pck: Packet):
        try:
            getattr(self, f'_handle_packet_{pck.identifier}')(pck)
        except:
            traceback.print_exc()

    def join_interactive_session(self, session_id: str, block: bool):
        session = InteractiveSession(self, None, None, uid = session_id)
        self.sessions[session.uuid] = session
        session.join()
        if block: session.wait()

    def launch_interactive_session(self, target_machine: str, exec: str, block: bool):
        session = InteractiveSession(self, target_machine, exec)
        self.sessions[session.uuid] = session
        session.launch()
        if block: session.wait()

    def send_packet(self, pck: Packet) -> None:
        self.send_queue.put(pck)

    def close(self):
        self.ws.close()

    def _handle_packet_interactive_session(self, pck: PacketInteractiveSession):
        uuid = pck.uuid
        if uuid in self.sessions:
            if self.sessions[uuid].receive_packet(pck):
                del self.sessions[uuid]

    def _handle_packet_node_status(self, pck: PacketNodeStatus):
        print(pck.node_status)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=str)
    parser.add_argument("--exec", type=str, default="/bin/bash")
    parser.add_argument("--local", "-l", action="store_true")
    parser.add_argument("--join", type=str)
    args = parser.parse_args()

    if args.join and args.target:
        print("Cannot join and launch")
        exit(1)

    if args.local:
        os.environ['WEBSOCKET_URL'] = "ws://127.0.0.1:8000/ws"

    cli = DVICDemoWatcherCli()
    with cli:

        cli.request_node_list()
        # input()    

        if args.target:
            cli.launch_interactive_session(args.target, args.exec, True)
        else:
            cli.join_interactive_session(args.join, True)

if __name__ == '__main__':
    main()