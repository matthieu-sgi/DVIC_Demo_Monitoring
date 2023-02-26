import uuid
from dvic_log_server.network.packets import PacketInteractiveSession, Packet

import dvic_log_server.connection as co
import dvic_log_server.api as api

INTERACTIVE_SESSIONS = {}

class InteractiveSession:
    def __init__(self, target_machine: co.Connection, target_executable: str = "/bin/bash") -> None:
        self.id = str(uuid.uuid1())
        self.target_machine = target_machine
        self.target_executable = target_executable
        self.subscribers: list[co.Connection] = []
        self.target_machine.send_packet(PacketInteractiveSession(self.id, executable=self.target_executable)) # initial packet to start interactive session

    def push(self, c: bytes):
        """Push a char from client to node

        Parameters
        ----------
        c : bytes
            The char to send. The size can be >1 for utf8 compatibility
        """
        self.target_machine.send_packet(PacketInteractiveSession(self.id, value=c))

    def pull(self, c: bytes):
        """Pull data from node to subscribed clients

        Parameters
        ----------
        c : bytes
            The data to dispatch to subscribed clients
        """
        self.dispatch(PacketInteractiveSession(self.id, value=c))

    def dispatch(self, pck: Packet):
        for c in self.subscribers:
            c.send_packet(pck)

    def kill(self, ret_value: int = None, msg: str = None):
        p = PacketInteractiveSession(self.id, 
                                     value=msg if msg is not None else f'Interactive session terminated with error code {ret_value}.', 
                                     return_value = ret_value
            )
        self.dispatch(p)
        for c in self.subscribers:
            self.unsubscribe(c)

    def subscribe(self, co: co.Connection):
        self.subscribers.append(co)
        #TODO screen-like session with server maintained state

    def unsubscribe(self, co: co.Connection):
        del self.subscribers[co]

    @staticmethod
    def handle_packet(src: co.Connection, pck: PacketInteractiveSession):
        # if interactive session does not exist
        if INTERACTIVE_SESSIONS[pck.uuid] is None:
            # if this is initial packet with target machine and executable
            if pck.target_machine is not None:
            # create interactive session, this sends the initial packet
                session = InteractiveSession(api.ConnectionManager()[pck.target_machine])
                # subscribe sender
                session.subscribe(src)
                return 
            else:
                raise RuntimeError("Initial InteractiveSession packet must have a target machine")

        session: InteractiveSession = INTERACTIVE_SESSIONS[pck.uuid]
        # if this is ret_value (final) packet
        if pck.return_value is not None:
            #   kill session, remove session, return
            session.kill(pck.return_value, pck.value)
            return
        
        # identify if we push or pull data
        method = session.pull if src is session.target_machine else session.push
        method(pck.value)