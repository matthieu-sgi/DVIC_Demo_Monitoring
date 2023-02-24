from fastapi import WebSocket

from server.dvic_log_server.network.packets import Packet


class Connection:
    def __init__(self, ws: WebSocket) -> None:
        self.ws = ws

    def send_packet(self, pck: Packet):
        pass

    def receive_packet(self, s: str):
        pass

    def _emission_packet_thread_target(self):
        pass

    def _reception_packet_thread_target(self):
        pass

class MachineConnection(Connection):
    def __init__(self, ws: WebSocket) -> None:
        super().__init__(ws)
        self.identity = None

    
    
