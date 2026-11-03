"""
CELLULARIS — Cell-Based Temporal Quantum Network Processor

A revolutionary computing paradigm where the Cell is the fundamental unit
of computation. Cells self-organize into tissues, organs, and eventually
complete computers — all living within the network.

"The Cell is the Computer. The Network is Life."
"""

__version__ = "1.0.0"
__author__ = "CELLULARIS Project"

from .cell.cell import Cell, CellType, CellState
from .cell.shard import SelfDescribingShard
from .cell.differentiation import DifferentiationEngine
from .cell.mitosis import MitosisEngine
from .pisphere.pisphere import Pisphere
from .pisphere.register import Register
from .temporal.engine import TemporalEngine
from .temporal.timer import Timer
from .temporal.gates import TemporalGate, GateType
from .hash.non_avalanche import non_avalanche_hash, compute_similarity
from .cmp.protocol import CMPFrame, MessageType
from .cmp.transport import CMPTransport, TransportMode

__all__ = [
    # Cell
    "Cell", "CellType", "CellState",
    "SelfDescribingShard",
    "DifferentiationEngine",
    "MitosisEngine",
    # Pisphere
    "Pisphere", "Register",
    # Temporal
    "TemporalEngine", "Timer",
    "TemporalGate", "GateType",
    # Hash
    "non_avalanche_hash", "compute_similarity",
    # CMP
    "CMPFrame", "MessageType",
    "CMPTransport", "TransportMode",
]
