"""
CMP Transport Layer — Transport modes for Cell communication.

Spec Reference: docs/spec/CMP.md
"""

from enum import Enum
from typing import Optional
from .protocol import CMPFrame


class TransportMode(Enum):
    """CMP transport modes."""
    RAW_ETHERNET = "raw_ethernet"   # EtherType 0xCE11
    UDP = "udp"                      # Port 2837
    TCP = "tcp"                      # Port 2837
    IPV6_EXT = "ipv6_ext"           # IPv6 Extension Header


class CMPTransport:
    """
    CMP-004: Transport layer for CMP frames.
    
    Parameters:
        mode: Transport mode (default: UDP)
        interface: Network interface (default: "lo")
    
    Spec: docs/spec/CMP.md #CMP-004
    """
    
    ETHERTYPE_RAW = 0xCE11  # CMP-007
    UDP_PORT = 2837          # CMP-008
    
    def __init__(self, mode: TransportMode = TransportMode.UDP, interface: str = "lo"):
        self.mode = mode
        self.interface = interface
    
    def send(self, frame: CMPFrame) -> None:
        """
        CMP-005: Send a CMP frame.
        
        Spec: docs/spec/CMP.md #CMP-005
        """
        data = frame.serialize()
        # In production, this would use raw sockets / UDP / TCP
        # For now, this is a stub
        pass
    
    def receive(self) -> Optional[CMPFrame]:
        """
        CMP-006: Receive a CMP frame.
        
        Spec: docs/spec/CMP.md #CMP-006
        """
        # Stub — would read from socket
        return None
