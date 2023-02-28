import json
import sys
import base64
import traceback
from typing import Any, Union

PACKET_ID_MATCHING = {
    "hardware_state": "HardwareState",
    "log_entry": "LogEntry",
    "demo_proc_state": "DemoProcState",
    "interactive_session": "InteractiveSession"
} # identifier -> str(class<Packet>)

class Packet:

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        
    def _encode_str(self, s: Union[str, bytes]) -> str:
        if type(s) is not bytes: s = s.encode('utf-8')
        return base64.b64encode(s).decode()
    
    def _decode_str(self, s: str, to_str: bool = True) -> Union[bytes, str]:
        b: bytes = base64.b64decode(s)
        return b.decode('utf-8') if to_str else b

    def encode(self) -> str:
        return json.dumps({
            'type': self.identifier,
            'data': self.get_data()
        })

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

    def set_data(self, data: dict) -> None:
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

class PacketHardwareState(Packet):
    def __init__(self, data : dict) -> None:
        super().__init__("hardware_state")
        self.data = data

    def get_data(self) -> dict:
        return self.data
    
    def set_data(self, data: dict) -> None:
        self.data = data

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
        return pck.set_data(data = data['data'])
    except:
        traceback.print_exc()
        print(f"Packet was: ", source)
        raise
