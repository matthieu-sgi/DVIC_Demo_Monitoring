import random, string
from dvic_log_server.network.packets import PacketInteractiveSession, Packet, PacketFileTransfer

import dvic_log_server.connection as co
import dvic_log_server.api as api
from dvic_log_server.logs import error, info, warning

INTERACTIVE_SESSIONS = {}

class InteractiveSession:
    def __init__(self, uid, target_machine: co.Connection, target_executable: str = "/bin/bash") -> None:
        self.id = uid
        self.target_machine = target_machine
        self.target_executable = target_executable
        self.subscribers: list[co.Connection] = []
        self.running = True
        self.target_machine.send_packet(PacketInteractiveSession(self.id, executable=self.target_executable)) # initial packet to start interactive session

    def _print_log(self, log_fn: callable, log_line: str):
        log_fn(f'[SESSION] ({self.uid}) {log_line}')

    def error(self, log_line: str):
        self._print_log(error, log_line)

    def info(self, log_line: str):
        self._print_log(info, log_line)

    def warning(self, log_line: str):
        self._print_log(warning, log_line)

    @property
    def uid(self):
        return self.id

    def push(self, c: bytes):
        """Push a char from client to node

        Parameters
        ----------
        c : bytes
            The char(s) to send. The size can be >1 for utf8 compatibility or script execution
        """
        if not self.running: return
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
        self.running = False
        self.info(f'Terminated with code {ret_value} and message: {msg}')
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
        self.subscribers.remove(co)

    @staticmethod
    def handle_packet(src: co.Connection, pck: PacketInteractiveSession):
        # if interactive session does not exist
        if pck.uuid not in INTERACTIVE_SESSIONS:
            # if this is initial packet with target machine and executable
            if pck.target_machine is not None:
                # check if the machine is available
                if api.ConnectionManager()[pck.target_machine] is None:
                    src.send_packet(PacketInteractiveSession(pck.uuid, return_value=-1, value=f'[SERVER] Machine {pck.target_machine} is not online.'))
                    return
                # create interactive session, this sends the initial packet
                
                session = InteractiveSession(pck.uuid, api.ConnectionManager()[pck.target_machine])
                INTERACTIVE_SESSIONS[pck.uuid] = session
                session.info(f'Registered session')
                # subscribe sender
                session.subscribe(src)
                return 
            else:
                src.send_packet(PacketInteractiveSession(pck.uuid, return_value=-1, value=f'[SERVER] Initial Interactive Session packet must contain an executable.'))
                return

        session: InteractiveSession = INTERACTIVE_SESSIONS[pck.uuid]
        # if this is ret_value (final) packet
        if pck.return_value is not None:
            # kill session, remove session, return
            session.kill(pck.return_value, pck.value)
            return
        
        # handle special action
        if pck.action is not None:
            if pck.action == "register":
                session.subscribe(src)
                session.info(f'Registered {src.uid} on session')
                return
        
        # identify if we push or pull data
        method = session.pull if src is session.target_machine else session.push
        method(pck.value)



class ScriptInteractiveSession(InteractiveSession):
    SCRIPT_EXEC_UPLOAD = "upload"
    SCRIPT_EXEC_PUSH   = "push"

    """ScriptInteractiveSession
    This interactive session is automated via a script whose content is given in script_content
    The script execution can be done in 2 ways: 
        - Upload the script on the target machine and run it from the interactive session
        - Send the script line by line from the server to the node.
    """
    def __init__(self, uid, target_machine: co.Connection, script_content: str, interpreter: str = "/bin/bash", script_exec_method: str = SCRIPT_EXEC_UPLOAD) -> None:
        super().__init__(uid, target_machine, interpreter)
        self.script_content: str = script_content
        self.gen_name: str = self._random_name()
        self.exec_method = script_exec_method
        if self.exec_method not in [ScriptInteractiveSession.SCRIPT_EXEC_PUSH, ScriptInteractiveSession.SCRIPT_EXEC_UPLOAD]:
            raise Exception(f'Invalid exec method {script_exec_method}')

    def _random_name(self):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k = 10))

    def _upload_script(self):
        self.info(f'Uploading script to machine {self.target_machine.uid} with name {self.gen_name} ({len(self.script_content)} bytes)')
        self.target_machine.send_packet(PacketFileTransfer(f'/tmp/{self.gen_name}', content=self.script_content.encode(), mode="600", owner="root"))

    def push_line(self, line: str):
        self.push(line.encode()+b'\n')

    def run_script(self):
        if self.exec_method == ScriptInteractiveSession.SCRIPT_EXEC_UPLOAD:
            self._upload_script()
            #TODO delay for upload and execute
        else: #Push
            self.info(f'Pushing script on console')
            for line in self.script_content.split('\n'):
                self.push_line(line)


class SSHScriptInteractiveSession(ScriptInteractiveSession):
    """SSHScriptInteractiveSession
    This class is the same as SSHScriptInteractiveSession but will attempt to connect to the REMOTE_HOST ssh server on port PORT with the provided credentials
    Once the connection is established, the script is uploaded to the REMOTE_HOST
    """

    def __init__(self, uid, target_machine: co.Connection, username: str, hostname: str, password: str = None) -> None:
        super().__init__(uid, target_machine, "/bin/bash", script_exec_method=ScriptInteractiveSession.SCRIPT_EXEC_PUSH)
        self.push_line(f'ssh {username}@{hostname} || exit 1')
        if password is not None:
            self.push_line(password)