from abc import ABC, abstractmethod
from dvic_log_server.network.packets import Packet

class AConnection(ABC):

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def is_disconnected(self) -> bool: ...

    @abstractmethod
    def inherit(self, conn) -> None: ...

    @abstractmethod
    def send_packet(self, pck: Packet) -> None: ...

