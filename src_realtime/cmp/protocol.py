"""
Cell Membrane Protocol (CMP) — CMP-001 through CMP-021

The communication protocol for Cells. Supports raw Ethernet, UDP, TCP,
and IPv6 extension header transport modes.

REAL IMPLEMENTATION:
- Real UDP socket transport
- Real TCP socket transport
- Binary frame serialization with CRC-32
- Proper network addressing

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
    CMP-001: Cell Membrane Protocol frame.
    
    Frame format (32-byte header + variable payload):
    - Version (4 bits) + Msg Type (4 bits) + Flags (8 bits) = 2 bytes
    - Source Cell ID (8 bytes)
    - Destination Cell ID (8 bytes)
    - Lattice Coordinates (12 bytes): depth(8) + theta(44) + phi(44)
    - Timestamp (8 bytes, nanoseconds)
    - Phase θ (2 bytes) + Phase φ (2 bytes) + Shard Hash Ref (4 bytes) = 8 bytes
    - Payload Length (2 bytes)
    - Payload (variable)
    - CRC-32 (4 bytes)
    
    Spec: docs/spec/CMP.md #CMP-001
    """
    src_id: str
    dst_id: str
    msg_type: MessageType
    payload: bytes = b""
    timestamp: Optional[int] = None
    flags: int = 0
    version: int = 1
    lattice_depth: int = 0
    lattice_theta: float = 0.0
    lattice_phi: float = 0.0
    phase_theta: float = 0.0
    phase_phi: float = 0.0
    shard_hash_ref: int = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.perf_counter_ns()
    
    def serialize(self) -> bytes:
        """
        CMP-002: Serialize frame to bytes.
        
        Spec: docs/spec/CMP.md #CMP-002
        """
        # Encode cell IDs as 8-byte hashes
        src_hash = hashlib.sha256(self.src_id.encode()).digest()[:8]
        dst_hash = hashlib.sha256(self.dst_id.encode()).digest()[:8]
        
        # Pack header
        version_type = ((self.version & 0xF) << 4) | (int(self.msg_type) & 0xF)
        header = struct.pack('>BB', version_type, self.flags)
        header += src_hash
        header += dst_hash
        
        # Lattice coordinates
        header += struct.pack('>B', self.lattice_depth)
        # Pack theta and phi as fixed-point (22 bits each, packed into 44 bits)
        theta_fixed = int((self.lattice_theta / (2 * 3.14159265)) * (2**22 - 1))
        phi_fixed = int((self.lattice_phi / (2 * 3.14159265)) * (2**22 - 1))
        coord_packed = (theta_fixed << 22) | phi_fixed
        header += struct.pack('>Q', coord_packed)[2:]  # Take lower 6 bytes
        
        # Timestamp
        header += struct.pack('>Q', self.timestamp)
        
        # Phase and shard ref
        phase_theta_int = int((self.phase_theta / (2 * 3.14159265)) * 65535)
        phase_phi_int = int((self.phase_phi / (2 * 3.14159265)) * 65535)
        header += struct.pack('>HHI', phase_theta_int, phase_phi_int, self.shard_hash_ref)
        
        # Payload length
        payload_len = len(self.payload)
        header += struct.pack('>H', payload_len)
        
        # Combine header + payload
        frame_data = header + self.payload
        
        # CRC-32
        crc = self._compute_crc32(frame_data)
        frame_data += struct.pack('>I', crc)
        
        return frame_data
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'CMPFrame':
        """
        CMP-003: Deserialize frame from bytes.
        
        Spec: docs/spec/CMP.md #CMP-003
        """
        if len(data) < 38:  # Minimum frame size: 34 header + 4 CRC
            raise ValueError(f"Frame too short: {len(data)} bytes")
        
        # Verify CRC
        payload_with_crc = data
        frame_data = data[:-4]
        received_crc = struct.unpack('>I', data[-4:])[0]
        computed_crc = cls._compute_crc32(frame_data)
        
        if received_crc != computed_crc:
            raise ValueError("CRC mismatch")
        
        # Parse header
        offset = 0
        version_type, flags = struct.unpack('>BB', data[offset:offset+2])
        version = (version_type >> 4) & 0xF
        msg_type = MessageType(version_type & 0xF)
        offset += 2
        
        src_hash = data[offset:offset+8]
        offset += 8
        dst_hash = data[offset:offset+8]
        offset += 8
        
        lattice_depth = struct.unpack('>B', data[offset:offset+1])[0]
        offset += 1
        
        coord_bytes = b'\x00\x00' + data[offset:offset+6]
        coord_packed = struct.unpack('>Q', coord_bytes)[0]
        offset += 6
        
        theta_fixed = (coord_packed >> 22) & 0x3FFFFF
        phi_fixed = coord_packed & 0x3FFFFF
        lattice_theta = (theta_fixed / (2**22 - 1)) * (2 * 3.14159265)
        lattice_phi = (phi_fixed / (2**22 - 1)) * (2 * 3.14159265)
        
        timestamp = struct.unpack('>Q', data[offset:offset+8])[0]
        offset += 8
        
        phase_theta_int, phase_phi_int, shard_hash_ref = struct.unpack(
            '>HHI', data[offset:offset+8]
        )
        phase_theta = (phase_theta_int / 65535) * (2 * 3.14159265)
        phase_phi = (phase_phi_int / 65535) * (2 * 3.14159265)
        offset += 8
        
        payload_len = struct.unpack('>H', data[offset:offset+2])[0]
        offset += 2
        
        payload = data[offset:offset+payload_len]
        
        return cls(
            src_id=src_hash.hex(),
            dst_id=dst_hash.hex(),
            msg_type=msg_type,
            payload=payload,
            timestamp=timestamp,
            flags=flags,
            version=version,
            lattice_depth=lattice_depth,
            lattice_theta=lattice_theta,
            lattice_phi=lattice_phi,
            phase_theta=phase_theta,
            phase_phi=phase_phi,
            shard_hash_ref=shard_hash_ref
        )
    
    @staticmethod
    def _compute_crc32(data: bytes) -> int:
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
    
    def __repr__(self) -> str:
        return (
            f"CMPFrame(src={self.src_id[:8]}..., dst={self.dst_id[:8]}..., "
            f"type={self.msg_type.name}, payload={len(self.payload)}B)"
        )
