"""
Cell Membrane Protocol (CMP) — CMP-001 through CMP-021

The communication protocol for Cells. Supports raw Ethernet, UDP, TCP,
and IPv6 extension header transport modes.

Spec Reference: docs/spec/CMP.md
"""

import struct
import time
import hashlib
from typing import Optional
from enum import IntEnum
from dataclasses import dataclass


class MessageType(IntEnum):
    """CMP-009 through CMP-021: Message types."""
    SIGNAL = 0x01
    TIMER_SYNC = 0x02
    STATE_TRANSFER = 0x03
    MITOSIS_REQ = 0x04
    DIFFERENTIATE = 0x05
    APOPTOSIS = 0x06
    FUSION_REQ = 0x07
    SHARD_EXCHANGE = 0x08
    BELL_INIT = 0x09
    MEASURE = 0x0A
    GATE_APPLY = 0x0B
    ROUTE = 0x0C


@dataclass
class CMPFrame:
    """
    CMP-001: A Cell Membrane Protocol frame.
    
    Frame format (36 bytes header + variable payload):
    - Version (4 bits) + Msg Type (4 bits) + Flags (8 bits)
    - Source Cell ID (64 bits)
    - Destination Cell ID (64 bits)
    - Lattice Coordinates (96 bits): depth(8) + theta(44) + phi(44)
    - Timestamp (64 bits, nanoseconds)
    - Phase θ (16 bits) + Phase φ (16 bits) + Shard Hash Ref (32 bits)
    - Payload Length (16 bits) + Payload (variable)
    - CRC-32 Checksum (32 bits)
    
    Spec: docs/spec/CMP.md #CMP-001
    """
    src_id: str
    dst_id: str
    msg_type: MessageType
    payload: bytes = b''
    timestamp: Optional[int] = None
    flags: int = 0
    phase_theta: int = 0
    phase_phi: int = 0
    lattice_depth: int = 0
    lattice_theta: int = 0
    lattice_phi: int = 0
    shard_hash_ref: int = 0
    
    VERSION = 1
    HEADER_SIZE = 36  # bytes
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = int(time.time() * 1e9)
    
    def serialize(self) -> bytes:
        """
        CMP-002: Serialize the frame to bytes.
        
        Spec: docs/spec/CMP.md #CMP-002
        """
        # Pack header
        version_type_flags = (self.VERSION << 12) | (self.msg_type << 8) | self.flags
        
        # Encode cell IDs as 8-byte hashes
        src_hash = int.from_bytes(
            hashlib.sha256(self.src_id.encode()).digest()[:8], 'big'
        )
        dst_hash = int.from_bytes(
            hashlib.sha256(self.dst_id.encode()).digest()[:8], 'big'
        )
        
        # Pack lattice coordinates (truncate to 64 bits for simplicity)
        lattice = ((self.lattice_depth & 0xFF) << 56) | ((self.lattice_theta & 0xFFFF) << 40) | (self.lattice_phi & 0xFFFF)
        
        header = struct.pack(
            '>HQQQQIII',
            version_type_flags,
            src_hash,
            dst_hash,
            lattice,
            self.timestamp & 0xFFFFFFFFFFFFFFFF,
            self.phase_theta & 0xFFFFFFFF,
            self.phase_phi & 0xFFFFFFFF,
            self.shard_hash_ref & 0xFFFFFFFF
        )
        
        # Payload length + payload
        payload_section = struct.pack('>H', len(self.payload)) + self.payload
        
        # CRC-32
        frame_data = header + payload_section
        crc = self._compute_crc(frame_data)
        
        return frame_data + struct.pack('>I', crc)
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'CMPFrame':
        """
        CMP-003: Deserialize a frame from bytes.
        
        Spec: docs/spec/CMP.md #CMP-003
        """
        if len(data) < 46:  # Updated header size
            raise ValueError("Frame too short")
        
        # Unpack header: >HQQQQIII
        version_type_flags = struct.unpack('>H', data[0:2])[0]
        version = (version_type_flags >> 12) & 0xF
        msg_type = MessageType((version_type_flags >> 8) & 0xF)
        flags = version_type_flags & 0xFF
        
        src_hash, dst_hash, lattice, timestamp = struct.unpack('>QQQQ', data[2:34])
        phase_theta, phase_phi, shard_hash_ref = struct.unpack('>III', data[34:46])
        
        # Extract lattice coordinates (truncated format)
        lattice_depth = (lattice >> 56) & 0xFF
        lattice_theta = (lattice >> 40) & 0xFFFF
        lattice_phi = lattice & 0xFFFF
        
        # Payload
        payload_len = struct.unpack('>H', data[46:48])[0]
        payload = data[48:48 + payload_len]
        
        return cls(
            src_id=f"0x{src_hash:016x}",
            dst_id=f"0x{dst_hash:016x}",
            msg_type=msg_type,
            payload=payload,
            timestamp=timestamp,
            flags=flags,
            phase_theta=phase_theta,
            phase_phi=phase_phi,
            lattice_depth=lattice_depth,
            lattice_theta=lattice_theta,
            lattice_phi=lattice_phi,
            shard_hash_ref=shard_hash_ref,
        )
    
    @staticmethod
    def _compute_crc(data: bytes) -> int:
        """Compute CRC-32 checksum."""
        crc = 0xFFFFFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc >>= 1
        return crc ^ 0xFFFFFFFF
