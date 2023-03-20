import json
import sys
import base64
import traceback
from typing import Any, Union
from enum import Enum
from dataclasses import dataclass

class NodeStatusAction(Enum):
    LIST_NODES = "list"
    
PACKET_ID_MATCHING = {
    "hardware_state": "HardwareState",
    "log_entry": "LogEntry",
    "demo_proc_state": "DemoProcState",
    "machine_log" : "MachineLog",
    "interactive_session": "InteractiveSession",
    "node_status": "NodeStatus"
} # identifier -> str(class<Packet>)

@dataclass
class NodeSelector: #TODO add selector 
    """
    Node selector used to select nodes to which send certain specific packets
    Used for cli -> api
    """
    uids: list[str] = None 
    tags: list[str] = None

class Packet:

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        
    def _encode_str(self, s: Union[str, bytes]) -> str:
        if type(s) is not bytes: s = str(s).encode('utf-8')
        return base64.b64encode(s).decode('utf-8')

    
    def _encode_dict(self, d: dict) -> dict:
        encoded_dict = json.dumps(d).encode('utf-8')
        return self._encode_str(encoded_dict)
    
    def _decode_str(self, s: str, to_str: bool = True) -> Union[bytes, str]: # FIXME : @gregor Problem here with padding
        # b: bytes = base64.b64decode(s)
        b: bytes = base64.b64decode(s + '=' * (len(s) % 4))
        return b.decode('utf-8') if to_str else b
    
    def _decode_dict(self, d: dict) -> dict:
        encoded_dict = self._decode_str(d, to_str=False)
        return json.loads(encoded_dict)

    def encode(self) -> str:
        return json.dumps({
            'type': self.identifier,
            'data': self.get_data()
        })
    
    # def to_dict(self) -> dict : # ? Easier to call properties
    #     '''convert the packet to a dict to store in the database''' 
    #     raise NotImplementedError()

    def get_data(self) -> dict:
        """get data from this packet

        Returns
        -------
        dict
            The data in serializable dictionary form

        Raises
        ------
        NotImplementedError
            This method must be implemented in the classes expanding from Packet
        """
        raise NotImplementedError()

    def set_data(self, data: dict) -> "Packet":
        """set the data values of the class form a dict representation

        Parameters
        ----------
        data : dict
            The dict representation of the data

        Raises
        ------
        NotImplementedError
            This method must be implemented in the classes expanding from Packet
        """
        raise NotImplementedError()


class PacketFileTransfer(Packet):
    def __init__(self, path: str = None, content: bytes = None, mode: str = None, owner: str = None) -> None:
        super().__init__("file_transfer")

class PacketNodeConfig(Packet):
    """
    Change a config element in a node or pull the current config
    """
    def __init__(self, mode: str = None, key: str = None, value: str = None) -> None:
        super().__init__("node_config_update")


class PacketNodeStatus(Packet):
    def __init__(self, action: NodeStatusAction = None, node_status: dict[str, str] = None) -> None:
        super().__init__("node_status")
        self.action = action.value if action is not None else None
        self.node_status = node_status

    def get_data(self) -> dict:
        return {
            'action': self.action,
            'node_status': self.node_status
        }
    
    def set_data(self, data: dict) -> Packet:
        self.action = NodeStatusAction(data['action']) if data['action'] is not None else None
        self.node_status = data['node_status']
        return self

class PacketHardwareState(Packet):
    def __init__(self, kind : str = None, log : str = None) -> None:
        super().__init__("hardware_state")
        self.kind = kind
        self.log  = log
        self.DICT_KINDS = ['temperature', 'memory_usage' ]

    def get_data(self) -> dict:
        log = self.log
        if self.kind in self.DICT_KINDS: log = self._encode_dict(log)
        else: log = self._encode_str(log)
        return {'kind': self.kind, 'log': log}
    
    def set_data(self, data: dict) -> None:
        self.kind = data['kind']
        log = data['log']
        if self.kind in self.DICT_KINDS: self.log = self._decode_dict(log)
        else: self.log = self._decode_str(log)
    

class PacketLogEntry(Packet):
    def __init__(self, data : dict) -> None:
        super().__init__("log_entry")
        self.data = data

    def get_data(self) -> dict:
        return self.data

    def set_data(self, data: dict) -> None:
        self.data = data


class PacketDemoProcState(Packet):
    def __init__(self, data : dict) -> None:
        super().__init__("demo_proc_state")
        self.data = data

    def get_data(self) -> dict:
        return self.data
    
    def set_data(self, data: dict) -> None:
        self.data = data
    
class PacketMachineLog(Packet):
    def __init__(self, kind: str = None, name: str = None, log: str = None) -> None:
        super().__init__("machine_log")
        self.kind = kind
        self.name = name
        self.log  = log

    def get_data(self) -> dict:
        return {'kind': self._decode_str(self.kind),
                'name': self._encode_str(self.name), 
                'log': self._encode_str(self.log)}
    
    def set_data(self, data: dict) -> None:
        self.kind = self._decode_str(data['kind'])
        self.name = self._decode_str(data['name'])
        self.log  = self._encode_str(data['log'])

class PacketShellCommandResponse(Packet):
    def __init__(self, data : dict) -> None:
        super().__init__("shell_command_response")
        self.data = data

    def get_data(self) -> dict:
        return self.data
    
    def set_data(self, data: dict) -> None:
        self.data = data


class PacketInteractiveSession(Packet):
    def __init__(self, uuid: str = None, executable = None, value = None, return_value = None, target_machine = None, action = None) -> None:
        super().__init__("interactive_session")
        self.uuid: str = uuid
        self.executable: str = executable
        self.value: Union[str, bytes] = value
        self.return_value: int = return_value
        self.target_machine: str = target_machine
        self.action: str = action

    def get_data(self) -> dict:
        data = {'uuid': self.uuid}
        if self.executable is not None: data |= {'executable': self.executable}
        if self.return_value is not None: data |= {'return_value': int(self.return_value)}
        if self.value is not None: data |= {'value': self._encode_str(self.value)}
        if self.target_machine is not None: data |= {'target_machine': self.target_machine}
        if self.action is not None: data |= {'action': self.action}
        return data
    
    def set_data(self, data: dict):
        self.uuid = data['uuid']
        self.executable = data['executable'] if "executable" in data else None
        self.value = self._decode_str(data['value'], False) if "value" in data else None
        self.return_value = data['return_value'] if "return_value" in data else None
        self.target_machine = data['target_machine'] if 'target_machine' in data else None
        self.action = data['action'] if 'action' in data else None
        return self


def decode(source: str) -> Packet:
    """Decodes a Packet from a str representation

    Parameters
    ----------
    source : str
        The representation as received over ws

    Returns
    -------
    Packet
        The crafted packet from the representation
    """
    try:
        data = json.loads(source)
        pck: Packet = getattr(sys.modules[__name__], f'Packet{PACKET_ID_MATCHING[data["type"]]}')()
        pck.set_data(data = data['data'])
        return pck
    except:
        traceback.print_exc()
        print(f"Packet was: ", source)
        raise

if __name__ == "__main__":
    pck = PacketHardwareState('temperature', {'a': 1, 'b': 2})
    data = pck.encode()
    print(data)
    pck2 = decode(data)
    print(pck2.to_dict())
