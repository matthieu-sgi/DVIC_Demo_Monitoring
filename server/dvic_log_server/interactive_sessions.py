import uuid

from dvic_log_server.connection import Connection
from dvic_log_server.network.packets import InteractiveSession as InteractiveSessionPacket, Packet

class InteractiveSession:
    def __init__(self, target_machine: Connection, target_executable: str = "/bin/bash") -> None:
        self.id = str(uuid.uuid1())
        self.target_machine = target_machine
        self.target_executable = target_executable
        self.subscribers: list[Connection] = []
        self.target_machine.send_packet(InteractiveSessionPacket(self.id).set_data({'executable': self.target_executable})) # initial packet to start interactive session

    def push(self, c: bytes):
        """Push a char from client to node

        Parameters
        ----------
        c : bytes
            The char to send. The size can be >1 for utf8 compatibility
        """
        self.target_machine.send_packet(InteractiveSessionPacket(self.id).set_data({'value': c}))

    def pull(self, c: bytes):
        """Pull data from node to subscribed clients

        Parameters
        ----------
        c : bytes
            The data to dispatch to subscribed clients
        """
        self.dispatch(InteractiveSessionPacket(self.id).set_data({'value': c}))

    def dispatch(self, pck: Packet):
        for c in self.subscribers:
            c.send_packet(pck)

    def kill(self, ret_value: int = None, msg: str = None):
        p = InteractiveSessionPacket(self.id).set_data({'value': msg if msg is not None else f'Interactive session terminated with error code {ret_value}.', 'return_value': ret_value})
        self.dispatch(p)
        for c in self.subscribers:
            self.unsubscribe(c)

    def subscribe(self, co: Connection):
        self.subscribers.append(co)
        #TODO screen-like session with server maintained state

    def unsubscribe(self, co: Connection):
        del self.subscribers[co]