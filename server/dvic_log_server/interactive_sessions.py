import random, string
from dvic_log_server.network.packets import PacketInteractiveSession, Packet, PacketFileTransfer

from dvic_log_server.meta import AConnection
import dvic_log_server.api as api
from dvic_log_server.logs import error, info, warning
import uuid
import traceback

INTERACTIVE_SESSIONS = {}

class InteractiveSession:
    def __init__(self, uid, target_machine: AConnection, target_executable: str = "/bin/bash") -> None:
        self.id = uid
        if self.id == None:
            # Special case of API initiated InteractiveSession: we create the UUID ourselves
            # we also must register the session in the general interactive session dict at this point
            self.id = self._generate_uid()
            InteractiveSession._init_interactive_session(self)
        self.target_machine = target_machine
        self.target_executable = target_executable
        self.subscribers: list[AConnection] = []
        self.running = True
        self.target_machine.send_packet(PacketInteractiveSession(self.id, executable=self.target_executable)) # initial packet to start interactive session
        self.hooks = []

    def register_termination_hook(self, fct: callable):
        self.hooks.append(fct)

    def _print_log(self, log_fn: callable, log_line: str):
        log_fn(f'[SESSION] ({self.uid}) {log_line}')

    def error(self, log_line: str):
        self._print_log(error, log_line)

    def info(self, log_line: str):
        self._print_log(info, log_line)

    def warning(self, log_line: str):
        self._print_log(warning, log_line)

    def _generate_uid(self) -> str:
        return str(uuid.uuid4())

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
        for h in self.hooks:
            try:
                h(self, ret_value, msg)
            except:
                error(f'Error in termination hook {h}')
                traceback.print_exc()

    def subscribe(self, co: AConnection):
        self.subscribers.append(co)
        #TODO screen-like session with server maintained state

    def unsubscribe(self, co: AConnection):
        self.subscribers.remove(co)


    @staticmethod
    def _init_interactive_session(session: "InteractiveSession"):
        global INTERACTIVE_SESSIONS
        INTERACTIVE_SESSIONS[session.uid] = session
        print('registered')
        session.info(f'Registered session')

    @staticmethod
    def handle_packet(src: AConnection, pck: PacketInteractiveSession):
        
        # print(INTERACTIVE_SESSIONS)
        # if interactive session does not exist
        if pck.uuid not in INTERACTIVE_SESSIONS:
            # if this is initial packet with target machine and executable
            if pck.target_machine is None:
                src.send_packet(PacketInteractiveSession(pck.uuid, return_value=-1, value=f'[SERVER] No target machine provided or attempted to join an invalid session id.'))
                return

            # check if the machine is available
            if api.ConnectionManager()[pck.target_machine] is None:
                src.send_packet(PacketInteractiveSession(pck.uuid, return_value=-1, value=f'[SERVER] Machine {pck.target_machine} is not online.'))
                return
            
            # check executable is there
            
            if pck.executable is None:
                src.send_packet(PacketInteractiveSession(pck.uuid, return_value=-1, value=f'[SERVER] Initial Interactive Session packet must contain an executable.'))
                return

            # create interactive session, this sends the initial packet
            session = InteractiveSession(pck.uuid, api.ConnectionManager()[pck.target_machine])
            InteractiveSession._init_interactive_session(session)
            # subscribe sender
            session.subscribe(src)
            return

           

        session: InteractiveSession = INTERACTIVE_SESSIONS[pck.uuid]
        # if this is ret_value (final) packet
        if pck.return_value is not None:
            # kill session, remove session, return
            session.kill(pck.return_value, pck.value)
            del INTERACTIVE_SESSIONS[session.uid]
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
    def __init__(self, uid, target_machine: AConnection, script_content: str, interpreter: str = "/bin/bash", script_exec_method: str = SCRIPT_EXEC_UPLOAD) -> None:
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

    def __init__(self, uid, target_machine: AConnection, script_path_or_content: str, username: str, hostname: str, password: str = None) -> None:
        super().__init__(uid, target_machine, self._get_script_content(script_path_or_content), "/bin/bash", script_exec_method=ScriptInteractiveSession.SCRIPT_EXEC_PUSH)
        self.push_line(f'ssh {username}@{hostname} || exit 1')
        if password is not None:
            self.push_line(password)
        self.psd = password

    def run_script(self):
        ensure_sudo_script = f"""
if sudo -n true 2>/dev/null; then 
    sudo su
else
    echo "{self.password}" | sudo -S su"
fi
[[ `id -u` == 0 ]] || exit 1
        """
        for l in ensure_sudo_script: self.push_line(l)
        return super().run_script()

    def _get_script_content(self, script_path_or_content: str):
        from os import path
        if path.isfile(script_path_or_content):
            with open(script_path_or_content) as fh:
                return fh.read()
        return script_path_or_content