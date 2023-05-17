from fastapi import WebSocket

import asyncio
from dvic_log_server.network.packets import *
from dvic_log_server.api import ConnectionManager
from multiprocessing import Queue
from dvic_log_server.logs import info, warning, error, debug
from dvic_log_server.database_drivers import ElasticConnector
from dvic_log_server.meta import AConnection
from dvic_log_server.interactive_sessions import InteractiveSession, ScriptInteractiveSession, SSHScriptInteractiveSession

from time import time
from starlette.websockets import WebSocketState

from dvic_log_server.logs import info, warning, error, debug

elk_host = 'localhost'
elk_port = 9200


class Connection(AConnection):
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

    def _protocol_error(self, msg: str):
        error(f'Protocol error: {msg}')
        self.close()

    def receive_packet(self, pck: Packet):
        if pck is None: self._protocol_error("Packet cannot be decoded")
        self.last_seen = time()
        fct = getattr(self, f'_handle_{pck.identifier}')
        if fct is None: self._protocol_error(f'no such packet {pck.identifier}')
        try: fct(pck)
        except:
            error(f"Failed to handle packet {pck.identifier}")
            traceback.print_exc()
    
    def close(self):
        self.in_use = False
        asyncio.run_coroutine_threadsafe(self.ws.close(), asyncio.get_event_loop())

    # handlers
    #################! REMOVE THIS ##################
    def _handle_machine_log(self, pck : PacketMachineLog): # TODO : Im changing this to log_entry
        '''Handle a machine log packet'''
        elk = ElasticConnector(elk_host,elk_port,index='machine_logs')
        dict_to_store = {'node': self.uid, 
                         'type': pck.identifier, 
                         'kind': pck.kind, 
                         'name' : pck.name, 
                         'log' : pck.log, 
                         'timestamp': time()}
        elk.insert(dict_to_store)
        elk.close()
    
    #################! REMOVE THIS ##################

    def _handle_hardware_state(self, pck: PacketHardwareState):
        '''Handle a hardware state packet'''
        elk = ElasticConnector(elk_host,elk_port,index='machine_hardware_state')
        # info(f'Log to store : {pck.log} and type {type(pck.log)}')
        elk.insert({
                'node': self.uid, 
                'type': pck.identifier, 
                'kind': pck.kind, 
                'data' : json.dumps(pck.data), 
                'timestamp': time()    
            })
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
        InteractiveSession.handle_packet(self, pck)
    
    def _handle_script_interactive_session(self, pck: PacketScriptInteractiveSession):
        info(f"[SESSION] Initiating script sessions on {pck.targets}")
        for m in pck.targets:
            c = ConnectionManager()[m]
            if c is None: 
                error(f"[SESSION] Cannot start script session on {m}: machine not connected")
                self.send_packet(PacketInteractiveSession(None, None, f'[SERVER] Cannot start script session on {m}: machine not connected', -1))
                continue # TODO send message to client: no such machine, but no IS is started 
            interactive_session = ScriptInteractiveSession(uid = None, target_machine=c, script_content=pck.script, script_exec_method=ScriptInteractiveSession.SCRIPT_EXEC_PUSH)
            interactive_session.subscribe(self)
            interactive_session.run_script()


    def _handle_log_entry(self, pck: PacketLogEntry):
        '''Handle a log entry packet'''
        elk = ElasticConnector(elk_host,elk_port,index='machine_logs')
        dict_to_store = {'node': self.uid, 
                         'type': pck.identifier, 
                         'kind': pck.kind, 
                         'name' : pck.name, 
                         'log' : pck.log, 
                         'timestamp': time()}
        elk.insert(dict_to_store)
    
    def _handle_node_addition_request(self, pck: PacketNodeAdditionRequest):
        cm = ConnectionManager()
        #? TODO create connection addition with retry and timeout 
        
        # For now, we will make only one attempt at adding a node. Saving the node id and connection parameters for a retry
        # in a second step

        if cm[pck.source_node_uid] is None:
            pass
        
        
        def post_install_hook(session: SSHScriptInteractiveSession, return_value: int, message: str):
            if return_value == 0:
                #TODO  ok, new node install successful
                pass
            else:
                #TODO not ok, new node did not install, disregard the generated node id+ key
                pass

        specific_script = "" #TODO install script parsed with the template and new node uid, private key are replaced
        session = SSHScriptInteractiveSession(None, cm[pck.source_node_uid], specific_script, pck.username, pck.ip, pck.password)
        session.register_termination_hook(post_install_hook)
        session.run_script()
        info(f'Installing new node via session {session.uid}')


    def _handle_demo_proc_state(self, pck: PacketDemoProcState):
        '''Handle a demo process state packet'''
        raise NotImplementedError()

class MachineConnection(Connection): #? usefull
    def __init__(self, ws: WebSocket) -> None:
        super().__init__(ws)
        self.identity = None

    
    
