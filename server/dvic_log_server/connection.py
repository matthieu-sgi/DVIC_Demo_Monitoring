from fastapi import WebSocket

from dvic_log_server.network.packets import *
from multiprocessing import Queue




class Connection:
    def __init__(self, ws: WebSocket, uid: str) -> None:
        self.ws = ws
        self.uid = uid
        self.send_queue: Queue = Queue()

    def send_packet(self, pck: Packet):
        self.send_queue.put(pck)

    def next_packet(self) -> Packet:
        return self.send_queue.get()

    def receive_packet(self, pck: Packet):
        getattr(self, f'_handle_{pck.identifier}')(pck)
    
    # handlers

    def _handle_machine_hardware_state(self, pck: PacketHardwareState):
        raise NotImplementedError()

    def _handle_interactive_session(self, pck: PacketInteractiveSession):
        from dvic_log_server.interactive_sessions import InteractiveSession # defer import *shrug*
        InteractiveSession.handle_packet(self, pck)

class MachineConnection(Connection): #? usefull
    def __init__(self, ws: WebSocket) -> None:
        super().__init__(ws)
        self.identity = None

    
    
