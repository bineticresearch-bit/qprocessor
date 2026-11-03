"""
Lane Framing — LANE-001 through LANE-008

The packet train IS the header: each datagram carries one 40-byte lane of a
logical header; reassembled at the membrane, concat(lane_0..lane_N-1) is the
executable header. Ordering is semantics (L-I1); loss is control flow (L-I2).

Wire layout (spec §1.1): a fixed 56-byte datagram =
    16B base routing header | 40B lane payload | ... see LaneFrame docstring.
Timestamp and phase are per-lane data carried in the lane payload region, so
the base header stays pure routing (survives middleboxes that only touch IP).

Spec Reference: docs/spec/LANE-ISA.md §1
"""

import struct
import zlib
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


# --- Constants -------------------------------------------------------------

LANE_PAYLOAD_SIZE = 40          # bytes per lane (spec: 320 bits)
BASE_HEADER_SIZE = 16           # bytes of pure routing header
CRC_SIZE = 4                    # CRC-32 trailer
DATAGRAM_SIZE = BASE_HEADER_SIZE + LANE_PAYLOAD_SIZE + CRC_SIZE  # 56 bytes

# Base header struct: u32 vtf | u8 k | u8 N | u8 hops | u32 train_id | u32 src_crc | u8 rsvd = 16
_BASE_FMT = ">IBBBIIB"
assert struct.calcsize(_BASE_FMT) == BASE_HEADER_SIZE

DEFAULT_WINDOW_NS = 25_000_000  # 25 ms reassembly window (LANE-007 default)


class AssemblerState(Enum):
    """LANE-005: assembler lifecycle states."""
    PARTIAL = "partial"      # Waiting for more lanes
    COMPLETE = "complete"    # All lanes present, contiguous from 0
    EXPIRED = "expired"      # Window elapsed with gaps (L-I2 interrupt)
    REJECTED = "rejected"    # Invalid frame / overflow; dropped


class TruncatedLaneError(Exception):
    """LANE-003: datagram shorter than DATAGRAM_SIZE or CRC mismatch."""


class IncompleteTrainError(Exception):
    """LANE-006: reassembled_header() called before COMPLETE."""


@dataclass(frozen=True)
class ResidualEvent:
    """
    LANE-008: sheaf input emitted when a train fails to complete (L-I2).

    residual_magnitude = |expected_arrival_window - actual| / window, per
    spec §1.3 — feeds the SHEAF sensor as a region observation so a chronically
    dropping edge raises its anomaly score before packet-loss metrics do.
    """
    train_id: int
    missing_lanes: tuple          # sorted lane indices never received
    last_seen_cell: str           # source cell ID from frames seen
    expected_edge: str            # hint: src -> dst edge suspected of loss
    residual_magnitude: float     # normalized lateness/completeness gap


# --- LANE-001/002/003: LaneFrame -------------------------------------------

class LaneFrame:
    """
    LANE-001: A single lane datagram (56 bytes on the wire).

    Base routing header (16B, spec §1.1):
        u32  vtf          : ISA version(4b) | msg type(4b) | flags(FIN..)(8b) + pad
        u8   lane_index k : position in train (= program counter, L-I1)
        u8   total N      : lanes in this train
        u8   hop_count    : transit hops (E-R4 overflow -> drop+residual)
        u32  train_id     : groups the datagrams into one logical header
        u32  src_crc      : CRC-32 of source cell id string
        u8   reserved

    Lane payload (40B): per-lane data. The FIRST 12 bytes are a standard
    temporal preamble — u64 timestamp_ns | u16 phase_theta | u16 phase_phi —
    so every lane self-describes its arrival timing/phase for the SYNC and
    PHASE_BANK ops (ISA-004, ISA-008); remaining 28 bytes are op data.

    Trailer: CRC-32 over header+lane payload.

    Spec: docs/spec/LANE-ISA.md #LANE-001
    """

    ISA_VERSION = 1
    TEMPORAL_PREAMBLE = 12        # ts(8) + th(2) + ph(2) at start of lane payload

    def __init__(self, lane_index: int, train_id: int, total_lanes: int,
                 payload_40b: bytes, seq: int = 0, is_final: bool = False,
                 msg_type: int = 0x01, hop_count: int = 0,
                 src_cell_id: str = "", timestamp_ns: Optional[int] = None,
                 phase_theta: int = 0, phase_phi: int = 0):
        if not (0 <= lane_index < total_lanes):
            raise ValueError(f"lane_index {lane_index} outside [0,{total_lanes})")
        if len(payload_40b) != LANE_PAYLOAD_SIZE:
            raise ValueError(
                f"lane payload must be exactly {LANE_PAYLOAD_SIZE} bytes, got {len(payload_40b)}")
        self.lane_index = lane_index
        self.train_id = train_id & 0xFFFFFFFF
        self.total_lanes = total_lanes
        # Stamp the temporal preamble into a copy of the payload.
        if timestamp_ns is None:
            import time as _t
            timestamp_ns = _t.perf_counter_ns()
        self.timestamp_ns = int(timestamp_ns) & 0xFFFFFFFFFFFFFFFF
        self.phase_theta = phase_theta & 0xFFFF
        self.phase_phi = phase_phi & 0xFFFF
        pre = struct.pack(">QHH", self.timestamp_ns, self.phase_theta, self.phase_phi)
        # Op data is whatever follows where the preamble sits: caller's bytes
        # [TEMPORAL_PREAMBLE:], zero-padded/truncated to exactly 28 bytes.
        op_data = payload_40b[self.TEMPORAL_PREAMBLE:]
        op_data = (op_data + bytes(28))[:28]
        self.payload_40b = pre + op_data
        self.seq = seq & 0xFFFF
        self.is_final = bool(is_final) or (lane_index == total_lanes - 1)
        self.msg_type = msg_type & 0x0F
        self.hop_count = hop_count & 0xFF
        self.src_cell_id = src_cell_id

    def serialize(self) -> bytes:
        """LANE-002: Serialize to a 56-byte datagram. Spec #LANE-002."""
        flags = (1 if self.is_final else 0) & 0xFF
        vtf = ((self.ISA_VERSION & 0x0F) << 28) | ((self.msg_type & 0x0F) << 24) | (flags & 0xFF)
        src_id = zlib.crc32(self.src_cell_id.encode("utf-8")) if self.src_cell_id else 0

        head = struct.pack(_BASE_FMT, vtf, self.lane_index, self.total_lanes,
                           self.hop_count, self.train_id, src_id & 0xFFFFFFFF, 0)
        body = head + self.payload_40b
        crc = zlib.crc32(body) & 0xFFFFFFFF
        return body + struct.pack(">I", crc)

    @classmethod
    def deserialize(cls, data: bytes) -> "LaneFrame":
        """LANE-003: Deserialize; raise TruncatedLaneError if short/CRC-bad. Spec #LANE-003."""
        if len(data) < DATAGRAM_SIZE:
            raise TruncatedLaneError(f"datagram {len(data)}B < required {DATAGRAM_SIZE}")
        body, (crc_stored,) = data[:-CRC_SIZE], struct.unpack(">I", data[-CRC_SIZE:])
        if zlib.crc32(body) & 0xFFFFFFFF != crc_stored:
            raise TruncatedLaneError("CRC mismatch — lane corrupted in transit")

        vtf, k, n, hops, train_id, src_id, _rsvd = struct.unpack(_BASE_FMT, body[:16])
        payload = body[16:16 + LANE_PAYLOAD_SIZE]
        ts, th, ph = struct.unpack(">QHH", payload[:cls.TEMPORAL_PREAMBLE])

        obj = cls.__new__(cls)
        obj.lane_index = k
        obj.train_id = train_id
        obj.total_lanes = n
        obj.hop_count = hops
        obj.src_cell_id = f"cell_{src_id:08x}"   # ID is a CRC; inverse not recoverable
        obj.timestamp_ns = ts
        obj.phase_theta = th
        obj.phase_phi = ph
        obj.payload_40b = payload
        obj.seq = 0
        obj.is_final = bool(vtf & 1) or (k == n - 1)
        obj.msg_type = (vtf >> 24) & 0x0F
        return obj


# --- LANE-004/005/006: TrainAssembler ---------------------------------------

class TrainAssembler:
    """
    LANE-004: Reassembles one train's lanes into the logical header.

    Contiguity rule (L-I1, spec §1.2): execution fires only when lanes {0..N-1}
    are all present — arrival order is irrelevant; lane index = program counter.

    Spec: docs/spec/LANE-ISA.md #LANE-004
    """

    def __init__(self, train_id: int, expected_lanes: int,
                 window_ns: int = DEFAULT_WINDOW_NS):
        if expected_lanes < 1:
            raise ValueError("expected_lanes must be >= 1")
        self.train_id = train_id & 0xFFFFFFFF
        self.expected_lanes = expected_lanes
        self.window_ns = window_ns
        self._lanes: Dict[int, bytes] = {}
        self.state = AssemblerState.PARTIAL
        self.created_at_ns: Optional[int] = None
        self.last_seen_cell = ""

    def feed(self, frame: LaneFrame) -> AssemblerState:
        """LANE-005: Accept one lane; return new state. Spec #LANE-005."""
        import time as _t
        now = _t.perf_counter_ns()
        if self.created_at_ns is None:
            self.created_at_ns = now

        if frame.train_id != self.train_id or frame.lane_index >= self.expected_lanes:
            self.state = AssemblerState.REJECTED
            return self.state

        # A lone first frame may authoritatively raise N (train announces width).
        if frame.total_lanes > self.expected_lanes and len(self._lanes) == 0:
            self.expected_lanes = frame.total_lanes

        self._lanes[frame.lane_index] = frame.payload_40b
        self.last_seen_cell = frame.src_cell_id

        if set(range(self.expected_lanes)) <= set(self._lanes.keys()):
            self.state = AssemblerState.COMPLETE
        elif now - self.created_at_ns > self.window_ns:
            self.state = AssemblerState.EXPIRED
        else:
            self.state = AssemblerState.PARTIAL
        return self.state

    def reassembled_header(self) -> bytes:
        """LANE-006: Logical header bytes; IncompleteTrainError unless COMPLETE."""
        if self.state != AssemblerState.COMPLETE:
            raise IncompleteTrainError(
                f"train {self.train_id} state={self.state.value}, "
                f"{len(self._lanes)}/{self.expected_lanes} lanes")
        return b"".join(self._lanes[k] for k in range(self.expected_lanes))

    def missing_lane_indices(self) -> List[int]:
        """LANE-008 support: which lane indices never arrived."""
        return sorted(set(range(self.expected_lanes)) - set(self._lanes.keys()))


# --- LANE-007/008: ReassemblyPolicy ------------------------------------------

class ReassemblyPolicy:
    """
    LANE-007: Owns the assembler buffer and window policy for a membrane.

    on_gap "buffer" (default): hold until expiry then EXPIRED -> LANE-008.
    on_gap "drop": reject immediately once a gap is detected past contiguity.

    Spec: docs/spec/LANE-ISA.md #LANE-007
    """

    def __init__(self, max_buffer_trains: int = 64,
                 window_ns: int = DEFAULT_WINDOW_NS, on_gap: str = "buffer"):
        if on_gap not in ("buffer", "drop"):
            raise ValueError("on_gap must be 'buffer' or 'drop'")
        self.max_buffer_trains = max_buffer_trains
        self.window_ns = window_ns
        self.on_gap = on_gap
        self._assemblers: Dict[int, TrainAssembler] = {}

    def get_or_create(self, frame: LaneFrame) -> TrainAssembler:
        """Route an incoming lane to its assembler (creating/evicting as needed)."""
        tid = frame.train_id
        asm = self._assemblers.get(tid)
        if asm is None:
            if len(self._assemblers) >= self.max_buffer_trains:
                old_tid = min(self._assemblers,
                              key=lambda t: self._assemblers[t].created_at_ns or 0)
                evicted = self._assemblers.pop(old_tid)
                evicted.state = AssemblerState.EXPIRED
            asm = TrainAssembler(tid, frame.total_lanes, self.window_ns)
            self._assemblers[tid] = asm
        return asm

    def on_expire(self, assembler: TrainAssembler) -> ResidualEvent:
        """LANE-008: Emit the sheaf residual for a failed train (L-I2)."""
        import time as _t
        missing = tuple(assembler.missing_lane_indices())
        elapsed_ns = 0
        if assembler.created_at_ns is not None:
            elapsed_ns = max(0, _t.perf_counter_ns() - assembler.created_at_ns)
        residual_magnitude = (abs(self.window_ns - elapsed_ns) / self.window_ns
                              if self.window_ns else 1.0)
        return ResidualEvent(
            train_id=assembler.train_id,
            missing_lanes=missing,
            last_seen_cell=assembler.last_seen_cell,
            expected_edge=f"{assembler.last_seen_cell} -> membrane",
            residual_magnitude=residual_magnitude,
        )

    def collect_completed(self) -> List[bytes]:
        """Drain completed logical headers in train-id order."""
        out = []
        for tid in sorted(self._assemblers):
            asm = self._assemblers[tid]
            if asm.state == AssemblerState.COMPLETE:
                out.append(asm.reassembled_header())
                del self._assemblers[tid]
        return out

    def collect_expired(self) -> List[ResidualEvent]:
        """Drain expired trains as residuals (feeds the SHEAF sensor)."""
        out = []
        for tid in sorted(list(self._assemblers)):
            asm = self._assemblers[tid]
            if asm.state == AssemblerState.EXPIRED:
                out.append(self.on_expire(asm))
                del self._assemblers[tid]
        return out
