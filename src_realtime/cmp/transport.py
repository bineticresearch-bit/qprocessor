"""
CMP Transport Layer — Real UDP/TCP/Raw Ethernet transport.

REAL IMPLEMENTATION:
- Actual UDP socket send/receive
- Actual TCP socket send/receive
- Proper socket lifecycle management
- Non-blocking I/O support

Spec Reference: docs/spec/CMP.md
"""

import socket
import struct
import time
import threading
import selectors
from enum import Enum
from typing import Optional, List, Callable
from .protocol import CMPFrame


class TransportMode(Enum):
    """CMP transport modes."""
    RAW_ETHERNET = "raw_ethernet"   # EtherType 0xCE11
    UDP = "udp"                      # Port 2837
    TCP = "tcp"                      # Port 2837
    IPV6_EXT = "ipv6_ext"           # IPv6 Extension Header
    LOOPBACK = "loopback"           # In-process (for testing)


# CMP-007, CMP-008: Protocol constants
ETHERTYPE_CMP = 0xCE11
UDP_PORT = 2837
TCP_PORT = 2837


class CMPTransport:
    """
    CMP-004: Real transport layer for CMP frames.
    
    Supports UDP, TCP, and loopback modes with actual socket I/O.
    
    Parameters:
        mode: Transport mode (default: LOOPBACK for testing)
        bind_address: Address to bind to (default: "127.0.0.1")
        bind_port: Port to bind to (default: 2837)
    
    Spec: docs/spec/CMP.md #CMP-004
    """
    
    def __init__(
        self,
        mode: TransportMode = TransportMode.LOOPBACK,
        bind_address: str = "127.0.0.1",
        bind_port: int = UDP_PORT
    ):
        self.mode = mode
        self.bind_address = bind_address
        self.bind_port = bind_port
        self._socket: Optional[socket.socket] = None
        self._running = False
        self._receive_thread: Optional[threading.Thread] = None
        self._incoming_frames: List[CMPFrame] = []
        self._lock = threading.Lock()
        self._on_receive: Optional[Callable] = None
        
        # Loopback mode: in-process message queue
        self._loopback_queue: List[CMPFrame] = []
        
        if mode != TransportMode.LOOPBACK:
            self._setup_socket()
    
    def _setup_socket(self) -> None:
        """Set up the network socket."""
        if self.mode == TransportMode.UDP:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.bind_address, self.bind_port))
            self._socket.settimeout(0.1)
        
        elif self.mode == TransportMode.TCP:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.bind_address, self.bind_port))
            self._socket.listen(10)
            self._socket.settimeout(0.1)
        
        elif self.mode == TransportMode.RAW_ETHERNET:
            # Raw Ethernet requires root/CAP_NET_RAW
            try:
                self._socket = socket.socket(
                    socket.AF_PACKET, socket.SOCK_RAW,
                    socket.htons(ETHERTYPE_CMP)
                )
                self._socket.bind((self.bind_address, 0))
                self._socket.settimeout(0.1)
            except PermissionError:
                raise RuntimeError(
                    "Raw Ethernet requires root privileges or CAP_NET_RAW capability"
                )
    
    def send(self, frame: CMPFrame, target_address: Optional[str] = None) -> bool:
        """
        CMP-005: Send a CMP frame.
        
        Args:
            frame: Frame to send
            target_address: Target address (host:port for UDP/TCP)
        
        Returns:
            True if sent successfully
        
        Spec: docs/spec/CMP.md #CMP-005
        """
        data = frame.serialize()
        
        if self.mode == TransportMode.LOOPBACK:
            with self._lock:
                self._loopback_queue.append(frame)
            return True
        
        elif self.mode == TransportMode.UDP:
            try:
                if target_address:
                    host, port = target_address.rsplit(':', 1)
                    port = int(port)
                else:
                    host, port = self.bind_address, self.bind_port
                
                self._socket.sendto(data, (host, port))
                return True
            except Exception as e:
                print(f"UDP send error: {e}")
                return False
        
        elif self.mode == TransportMode.TCP:
            try:
                if target_address:
                    host, port = target_address.rsplit(':', 1)
                    port = int(port)
                else:
                    host, port = self.bind_address, self.bind_port
                
                # Create new connection for each send (simple model)
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.connect((host, port))
                
                # Send length-prefixed frame
                length_prefix = struct.pack('>I', len(data))
                conn.sendall(length_prefix + data)
                conn.close()
                return True
            except Exception as e:
                print(f"TCP send error: {e}")
                return False
        
        elif self.mode == TransportMode.RAW_ETHERNET:
            try:
                self._socket.send(data)
                return True
            except Exception as e:
                print(f"Raw Ethernet send error: {e}")
                return False
        
        return False
    
    def receive(self, timeout: float = 0.1) -> Optional[CMPFrame]:
        """
        CMP-006: Receive a CMP frame.
        
        Args:
            timeout: Receive timeout in seconds
        
        Returns:
            Received CMPFrame or None
        
        Spec: docs/spec/CMP.md #CMP-006
        """
        if self.mode == TransportMode.LOOPBACK:
            with self._lock:
                if self._loopback_queue:
                    return self._loopback_queue.pop(0)
            return None
        
        if self._socket is None:
            return None
        
        try:
            self._socket.settimeout(timeout)
            
            if self.mode == TransportMode.UDP:
                data, addr = self._socket.recvfrom(65535)
                return CMPFrame.deserialize(data)
            
            elif self.mode == TransportMode.TCP:
                conn, addr = self._socket.accept()
                # Read length prefix
                length_data = conn.recv(4)
                if len(length_data) < 4:
                    conn.close()
                    return None
                frame_length = struct.unpack('>I', length_data)[0]
                # Read frame
                data = b""
                while len(data) < frame_length:
                    chunk = conn.recv(frame_length - len(data))
                    if not chunk:
                        break
                    data += chunk
                conn.close()
                if data:
                    return CMPFrame.deserialize(data)
            
            elif self.mode == TransportMode.RAW_ETHERNET:
                data = self._socket.recv(65535)
                # Skip Ethernet header (14 bytes)
                return CMPFrame.deserialize(data[14:])
        
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Receive error: {e}")
            return None
        
        return None
    
    def start_listening(self, callback: Optional[Callable] = None) -> None:
        """Start background listening for incoming frames."""
        if self._running:
            return
        
        self._running = True
        self._on_receive = callback
        
        self._receive_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )
        self._receive_thread.start()
    
    def _listen_loop(self) -> None:
        """Background listen loop."""
        while self._running:
            frame = self.receive(timeout=0.1)
            if frame:
                with self._lock:
                    self._incoming_frames.append(frame)
                if self._on_receive:
                    self._on_receive(frame)
    
    def stop_listening(self) -> None:
        """Stop background listening."""
        self._running = False
        if self._receive_thread:
            self._receive_thread.join(timeout=1.0)
    
    def get_pending_frames(self) -> List[CMPFrame]:
        """Get all pending incoming frames."""
        with self._lock:
            frames = list(self._incoming_frames)
            self._incoming_frames.clear()
            return frames
    
    def close(self) -> None:
        """Close the transport."""
        self.stop_listening()
        if self._socket:
            self._socket.close()
            self._socket = None
    
    def __del__(self):
        self.close()
    
    def __repr__(self) -> str:
        return (
            f"CMPTransport(mode={self.mode.value}, "
            f"addr={self.bind_address}:{self.bind_port})"
        )
