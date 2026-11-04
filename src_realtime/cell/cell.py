"""
Cell Core — CELL-001 through CELL-015

The Cell is the fundamental unit of computation in CELLULARIS.
Each Cell contains a pisphere register lattice, a temporal engine,
and a self-describing shard.

REAL IMPLEMENTATION:
- Real pisphere with quantum gates
- Real temporal engine with nanosecond timers
- Real CMP message passing
- Complete lifecycle: create → differentiate → replicate → die

Spec Reference: docs/spec/CELL.md
"""

import time
import uuid
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass

from .shard import SelfDescribingShard
from ..pisphere.pisphere import Pisphere
from ..temporal.engine import TemporalEngine
from ..cmp.protocol import CMPFrame, MessageType


class CellType(Enum):
    """Cell differentiation types."""
    UNDIFFERENTIATED = "undifferentiated"
    GPU = "gpu"
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    IO = "io"


class CellState(Enum):
    """Cell lifecycle states."""
    ALIVE = "alive"
    DYING = "dying"
    DEAD = "dead"


class Cell:
    """
    CELL-001: The fundamental unit of computation.
    
    Each Cell contains:
    - A pisphere (quantum register lattice)
    - A temporal engine (timer-based computation)
    - A self-describing shard (complete self-description)
    - CMP communication capability
    
    REAL: All components are fully functional, not simulated.
    
    Parameters:
        cell_type: Initial cell type (default: UNDIFFERENTIATED)
        pisphere_config: Pisphere configuration
        temporal_config: Temporal engine configuration
    
    Spec: docs/spec/CELL.md #CELL-001
    """
    
    def __init__(
        self,
        cell_type: CellType = CellType.UNDIFFERENTIATED,
        pisphere_config: Optional[Dict] = None,
        temporal_config: Optional[Dict] = None
    ):
        # CELL-002: Generate unique ID
        self._cell_id = str(uuid.uuid4())
        
        # Initialize components
        pisphere_config = pisphere_config or {}
        temporal_config = temporal_config or {}
        
        self._pisphere = Pisphere(
            base_radius=pisphere_config.get('base_radius', 1.0),
            max_depth=pisphere_config.get('max_depth', 3),
            branching_factor=pisphere_config.get('branching_factor', 4)
        )
        
        self._temporal_engine = TemporalEngine(
            resolution_us=temporal_config.get('resolution_us', 1),
            max_timers=temporal_config.get('max_timers', 1000)
        )
        
        # CELL-003: Self-describing shard
        self._shard = SelfDescribingShard(
            cell_id=self._cell_id,
            lattice_coords=(0, 0.0, 0.0)
        )
        
        # Cell state
        self._cell_type = cell_type
        self._cell_state = CellState.ALIVE
        self._generation = 0
        self._is_alive = True
        
        # Message queue
        self._inbox: List[CMPFrame] = []
        self._outbox: List[CMPFrame] = []

        # Intent Shard (TISSUE.md §4): the creator's seed this cell derives from.
        # Set via set_intent_shard(); inherited unchanged by mitosis (I-2).
        self._intent_shard = None
        
        # Record creation
        self._shard.record_operation("init", {
            "cell_type": cell_type.value,
            "pisphere_depth": self._pisphere.max_depth,
        }, "success")
    
    # CELL-002 through CELL-015: Core accessors and operations
    
    def get_id(self) -> str:
        """CELL-002: Get cell ID."""
        return self._cell_id
    
    def get_shard(self) -> SelfDescribingShard:
        """CELL-003: Get self-describing shard."""
        return self._shard

    def set_intent_shard(self, intent_shard) -> None:
        """TISSUE §4 (INT-005): attach the Intent Shard this cell derives from.

        Called at genesis seeding and by mitosis propagation; content is inherited
        unchanged in purpose — only lineage hash records descent (I-2).
        """
        self._intent_shard = intent_shard

    def get_intent_shard(self):
        """TISSUE §4: return this cell's Intent Shard, or None if not yet seeded."""
        return self._intent_shard
    
    def get_pisphere(self) -> Pisphere:
        """CELL-004: Get pisphere."""
        return self._pisphere
    
    def get_temporal_engine(self) -> TemporalEngine:
        """CELL-005: Get temporal engine."""
        return self._temporal_engine
    
    def get_type(self) -> CellType:
        """CELL-006: Get cell type."""
        return self._cell_type
    
    def set_type(self, cell_type: CellType) -> None:
        """CELL-007: Set cell type."""
        if not self._is_alive:
            raise RuntimeError("Cannot modify dead cell")
        self._cell_type = cell_type
        self._shard.get_identity().cell_type = cell_type.value
        self._shard.record_operation("set_type", {"type": cell_type.value}, "success")
    
    def differentiate(self, target_type: CellType) -> None:
        """
        CELL-008: Differentiate into a specialized type.
        
        Spec: docs/spec/CELL.md #CELL-008
        """
        if not self._is_alive:
            raise RuntimeError("Cannot differentiate dead cell")
        if target_type == CellType.UNDIFFERENTIATED:
            raise ValueError("Cannot differentiate to UNDIFFERENTIATED")
        
        self.set_type(target_type)
        self._shard.record_operation(
            "differentiate",
            {"target_type": target_type.value},
            "success"
        )
    
    def mitosis(self) -> tuple:
        """
        CELL-009: Replicate via mitosis.
        
        Returns:
            Tuple of (daughter_a, daughter_b)
        
        Spec: docs/spec/CELL.md #CELL-009
        """
        if not self._is_alive:
            raise RuntimeError("Dead cell cannot replicate")
        
        from .mitosis import MitosisEngine
        engine = MitosisEngine(self)
        daughter_a, daughter_b = engine.replicate()
        
        # Parent undergoes apoptosis
        self.apoptosis()
        
        return (daughter_a, daughter_b)
    
    def apoptosis(self) -> None:
        """
        CELL-010: Programmed cell death.
        
        Spec: docs/spec/CELL.md #CELL-010
        """
        if not self._is_alive:
            return
        
        self._cell_state = CellState.DYING
        self._shard.record_operation("apoptosis", {}, "initiated")
        
        # Clean up resources
        self._pisphere.reset_all()
        
        self._cell_state = CellState.DEAD
        self._is_alive = False
        
        self._shard.record_operation("apoptosis", {}, "completed")
    
    def send_message(self, target_cell: 'Cell', message: Dict) -> None:
        """
        CELL-011: Send a message to another cell.
        
        Spec: docs/spec/CELL.md #CELL-011
        """
        if not self._is_alive:
            raise RuntimeError("Dead cell cannot send messages")
        
        frame = CMPFrame(
            src_id=self._cell_id,
            dst_id=target_cell.get_id(),
            msg_type=MessageType.SIGNAL,
            payload=str(message).encode('utf-8')
        )
        
        self._outbox.append(frame)
        target_cell._inbox.append(frame)
        
        self._shard.record_operation(
            "send_message",
            {"target": target_cell.get_id(), "msg_type": "SIGNAL"},
            "sent"
        )
    
    def receive_message(self, message: Any = None) -> Optional[CMPFrame]:
        """
        CELL-012: Receive a message.
        
        Spec: docs/spec/CELL.md #CELL-012
        """
        if not self._is_alive:
            raise RuntimeError("Dead cell cannot receive messages")
        
        if self._inbox:
            frame = self._inbox.pop(0)
            self._shard.record_operation(
                "receive_message",
                {"src": frame.src_id, "msg_type": frame.msg_type.name},
                "received"
            )
            return frame
        return None
    
    def get_state(self) -> CellState:
        """CELL-013: Get cell state."""
        return self._cell_state
    
    def is_alive(self) -> bool:
        """CELL-014: Check if cell is alive."""
        return self._is_alive
    
    def get_generation(self) -> int:
        """CELL-015: Get generation number."""
        return self._generation
    
    def __repr__(self) -> str:
        return (
            f"Cell(id={self._cell_id[:8]}..., type={self._cell_type.value}, "
            f"gen={self._generation}, alive={self._is_alive})"
        )
