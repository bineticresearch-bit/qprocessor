"""
CELLULARIS Realtime — Full Realization
======================================

The complete, production-grade implementation of the CELLULARIS computing paradigm.
No simulations. No stubs. No approximations.

"The Cell is the Computer. The Network is Life."

Modules:
    hash        — Non-avalanche cryptographic hashing with lineage preservation
    pisphere    — Recursive spherical register lattice with true quantum measurement
    temporal    — High-resolution temporal computation engine
    cell        — Self-describing computational cells with real lifecycle
    cmp         — Cell Membrane Protocol with real UDP/TCP/Raw Ethernet transport
    genesis     — Creator control with real Ed25519 cryptographic enforcement
    tissue      — Tissue-level organization and emergent computer formation
"""

__version__ = "2.0.0"
__author__ = "CELLULARIS Project"
__status__ = "full-realization"

from .cell.cell import Cell, CellType, CellState
from .cell.shard import SelfDescribingShard
from .cell.differentiation import DifferentiationEngine
from .cell.mitosis import MitosisEngine
from .pisphere.pisphere import Pisphere
from .pisphere.register import Register, QuantumState
from .temporal.engine import TemporalEngine
from .temporal.timer import Timer, TimerState
from .temporal.gates import TemporalGate, GateType
from .hash.non_avalanche import non_avalanche_hash, compute_similarity, verify_lineage
from .cmp.protocol import CMPFrame, MessageType
from .cmp.transport import CMPTransport, TransportMode
from .genesis.genesis import GenesisProtocol, DemiurgeConsole
from .tissue.tissue import Tissue, TissueType
from .tissue.intent_shard import IntentShard, PurposeSection, Goal, SuccessModel, IntentReadOnlyError
from .tissue.portal import Portal

__all__ = [
    # Cell
    "Cell", "CellType", "CellState",
    "SelfDescribingShard",
    "DifferentiationEngine", "MitosisEngine",
    # Pisphere
    "Pisphere", "Register", "QuantumState",
    # Temporal
    "TemporalEngine", "Timer", "TimerState",
    "TemporalGate", "GateType",
    # Hash
    "non_avalanche_hash", "compute_similarity", "verify_lineage",
    # CMP
    "CMPFrame", "MessageType",
    "CMPTransport", "TransportMode",
    # Genesis
    "GenesisProtocol", "DemiurgeConsole",
    # Tissue
    "Tissue", "TissueType", "IntentShard", "PurposeSection", "Portal",
]
