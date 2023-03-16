from fastapi import WebSocket

import asyncio
from dvic_log_server.network.packets import *
from multiprocessing import Queue
from dvic_log_server.database_drivers import ElasticConnector

from time import time
from starlette.websockets import WebSocketState

elk_host = 'localhost'
elk_port = 9200


class Connection:
    def __init__(self, ws: WebSocket, uid: str) -> None:
        self.ws = ws
        self.uid = uid
        self.send_queue: Queue = Queue()
        self.in_use = True
        self.last_seen = time()

    def inherit(self, connection):
        """Inherit previous connection that was reset
        The method will replace and maintain state where the previous connection was unbiased

        Parameters
        ----------
        connection : Connection
            The previous, disconnected, Connection object
        """
        pass

    def is_disconnected(self) -> bool:
        return self.ws.application_state != WebSocketState.CONNECTED or not self.in_use

    def send_packet(self, pck: Packet):
        self.send_queue.put(pck)

    def next_packet(self) -> Packet:
        try: return self.send_queue.get(block=False)
        except: return None

    def receive_packet(self, pck: Packet):
        self.last_seen = time()
        getattr(self, f'_handle_{pck.identifier}')(pck)
    
    def close(self):
        self.in_use = False
        asyncio.run_coroutine_threadsafe(self.ws.close(), asyncio.get_event_loop())

    # handlers

    def _handle_machine_hardware_state(self, pck: PacketHardwareState):
        '''Handle a hardware state packet'''
        elk = ElasticConnector(elk_host,elk_port,index='machine_hardware_state')
        elk.insert(pck.get_data())
        elk.close()
    
    def _handle_machine_log(self, pck: PacketMachineLog):
        elk = ElasticConnector(elk_host,elk_port,index='machine_logs')
        elk.insert(pck.get_data())
        elk.close()

    def _handle_node_status(self, pck: PacketNodeStatus):
        from dvic_log_server.api import ConnectionManager #! fix this mess haiyaa
        if pck.action is not None:
            if pck.action == NodeStatusAction.LIST_NODES:
                connections = {
                    k: {
                        'status': "connected" if v is not None and not v.is_disconnected() else "disconnected",
                        'last_seen': v.last_seen
                       } 
                    for k, v in ConnectionManager().connections.items()
                }
                self.send_packet(PacketNodeStatus(node_status=connections))

    def _handle_interactive_session(self, pck: PacketInteractiveSession):
        from dvic_log_server.interactive_sessions import InteractiveSession # defer import *shrug*
        InteractiveSession.handle_packet(self, pck)
    
    def _handle_log_entry(self, pck: PacketLogEntry):
        '''Handle a log entry packet'''
        raise NotImplementedError()
    
    def _handle_demo_proc_state(self, pck: PacketDemoProcState):
        '''Handle a demo process state packet'''
        raise NotImplementedError()

class MachineConnection(Connection): #? usefull
    def __init__(self, ws: WebSocket) -> None:
        super().__init__(ws)
        self.identity = None

    
    
