from abc import ABC, abstractmethod

from client.network.packets import Packet

class AbstractDVICNode(ABC):
    
    @abstractmethod
    def send_packet(self, pck: Packet) -> None: ...

    @abstractmethod
    def _unregister_interactive_session(self, session: str) -> None: ...

    @abstractmethod
    def execute_shell_command(self, command: str) -> None: ...