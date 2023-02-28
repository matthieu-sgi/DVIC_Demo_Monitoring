from dvic_demo_cli.network.packets import Packet
from abc import ABC, abstractmethod

class DVICDemoWatcherCliBase(ABC):
    @abstractmethod
    def send_packet(self, pck: Packet) -> None: ...