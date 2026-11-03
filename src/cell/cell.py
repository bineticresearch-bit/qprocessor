"""
Cell Core — CELL-001 through CELL-015

The Cell is the fundamental unit of computation in CELLULARIS.
Each Cell contains a pisphere register lattice, a temporal engine,
and a self-describing shard.

Spec Reference: docs/spec/CELL.md
"""

import time
import uuid
from typing import Optional, List, Dict
from enum import Enum
from dataclasses import dataclass

from .shard import SelfDescribingShard
from ..pisphere.pisphere import Pisphere
from ..temporal.engine import TemporalEngine


class CellType(Enum):
    """Cell differentiation types."""
    UNDIFFERENTIATED = "undifferentiated"
    GPU = "gpu"
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    IO = "io"


@dataclass
class CellState:
    """Snapshot of Cell state."""
    cell_id: str
    cell_type: CellType
    generation: int
    is_alive: bool
    timer_count: int
    register_count: int
    timestamp: float


class Cell:
    """
    CELL-001: The fundamental computational unit.
    
    Each Cell contains:
    - A self-describing shard (complete provenance)
    - A pisphere register lattice (recursive spherical registers)
    - A temporal engine (timer-based computation)
    - A differentiation engine (can become GPU, CPU, etc.)
    - A mitosis engine (self-replication)
    
    Parameters:
        cell_type: Initial cell type (default: UNDIFFERENTIATED)
        pisphere_config: Configuration for pisphere lattice
        temporal_config: Configuration for temporal engine
    
    Spec: docs/spec/CELL.md #CELL-001
    """
    
    def __init__(
        self,
        cell_type: CellType = CellType.UNDIFFERENTIATED,
        pisphere_config: Optional[dict] = None,
        temporal_config: Optional[dict] = None,
        parent_lineage: Optional[dict] = None,
        lattice_coords: tuple = (0, 0.0, 0.0)
    ):
        # Generate unique cell ID
        self._cell_id = f"cell_{uuid.uuid4().hex[:12]}"
        
        # Create self-describing shard
        self._shard = SelfDescribingShard(
            cell_id=self._cell_id,
            lattice_coords=lattice_coords,
            lineage=parent_lineage
        )
        
        # Create pisphere register lattice
        pisphere_config = pisphere_config or {}
        self._pisphere = Pisphere(
            base_radius=pisphere_config.get("base_radius", 1.0),
            max_depth=pisphere_config.get("max_depth", 5),  # Reduced for performance
            branching_factor=pisphere_config.get("branching_factor", 4)
        )
        
        # Create temporal engine
        temporal_config = temporal_config or {}
        self._temporal_engine = TemporalEngine(
            resolution_us=temporal_config.get("resolution_us", 1),
            max_timers=temporal_config.get("max_timers", 1000)
        )
        
        # Cell state
        self._cell_type = cell_type
        self._is_alive = True
        self._generation = 0
        self._created_at = time.time()
        
        # Record creation in shard
        self._shard.record_operation("CREATE", {"type": cell_type.value}, self._cell_id)
    
    def get_id(self) -> str:
        """CELL-002: Get cell ID."""
        return self._cell_id
    
    def get_shard(self) -> SelfDescribingShard:
        """CELL-003: Get self-describing shard."""
        return self._shard
    
    def get_pisphere(self) -> Pisphere:
        """CELL-004: Get pisphere register lattice."""
        return self._pisphere
    
    def get_temporal_engine(self) -> TemporalEngine:
        """CELL-005: Get temporal engine."""
        return self._temporal_engine
    
    def get_type(self) -> CellType:
        """CELL-006: Get cell type."""
        return self._cell_type
    
    def set_type(self, cell_type: CellType) -> None:
        """CELL-007: Set cell type."""
        old_type = self._cell_type
        self._cell_type = cell_type
        self._shard.record_operation(
            "SET_TYPE",
            {"old": old_type.value, "new": cell_type.value},
            cell_type.value
        )
    
    def differentiate(self, target_type: CellType) -> None:
        """
        CELL-008: Differentiate into a specialized cell type.
        
        Parameters:
            target_type: The target cell type
        
        Spec: docs/spec/CELL.md #CELL-008
        """
        if not self._is_alive:
            raise RuntimeError("Cannot differentiate a dead cell")
        
        if target_type not in [CellType.GPU, CellType.CPU, CellType.MEMORY, CellType.NETWORK, CellType.IO]:
            raise ValueError(f"Cannot differentiate to {target_type}")
        
        old_type = self._cell_type
        self._cell_type = target_type
        
        # Configure based on type
        if target_type == CellType.GPU:
            # GPU: many parallel timers, shallow recursion
            pass
        elif target_type == CellType.CPU:
            # CPU: deep timer chains, complex control flow
            pass
        elif target_type == CellType.MEMORY:
            # Memory: pisphere lattice as storage
            pass
        elif target_type == CellType.NETWORK:
            # Network: boundary cell with CMP processing
            pass
        
        self._shard.record_operation(
            "DIFFERENTIATE",
            {"from": old_type.value, "to": target_type.value},
            target_type.value
        )
    
    def mitosis(self) -> tuple:
        """
        CELL-009: Replicate through mitosis, producing two daughter cells.
        
        Returns:
            Tuple of (daughter_1, daughter_2)
        
        Spec: docs/spec/CELL.md #CELL-009
        """
        if not self._is_alive:
            raise RuntimeError("Cannot replicate a dead cell")
        
        # Create lineage info for daughters
        lineage = {
            "ancestor_chain": [self._cell_id] + self._shard.get_lineage().ancestor_chain,
            "lineage_hash": self._shard.get_self_reference(),
            "generation_path": self._shard.get_lineage().generation_path + [self._generation + 1]
        }
        
        # Create two daughter cells
        daughter_1 = Cell(
            cell_type=self._cell_type,
            parent_lineage=lineage,
            lattice_coords=self._shard.get_position().lattice_coords
        )
        daughter_1._generation = self._generation + 1
        
        daughter_2 = Cell(
            cell_type=self._cell_type,
            parent_lineage=lineage,
            lattice_coords=self._shard.get_position().lattice_coords
        )
        daughter_2._generation = self._generation + 1
        
        # Record mitosis
        self._shard.record_operation(
            "MITOSIS",
            {"daughter_1": daughter_1.get_id(), "daughter_2": daughter_2.get_id()},
            "success"
        )
        
        # Original cell undergoes apoptosis
        self._is_alive = False
        
        return daughter_1, daughter_2
    
    def apoptosis(self) -> None:
        """
        CELL-010: Programmed cell death.
        
        Spec: docs/spec/CELL.md #CELL-010
        """
        self._is_alive = False
        self._shard.record_operation("APOPTOSIS", {}, "dead")
    
    def send_message(self, target_cell: 'Cell', message: dict) -> None:
        """
        CELL-011: Send a message to another cell via CMP.
        
        Spec: docs/spec/CELL.md #CELL-011
        """
        if not self._is_alive:
            raise RuntimeError("Dead cell cannot send messages")
        
        # Record send operation
        self._shard.record_operation(
            "SEND_MESSAGE",
            {"target": target_cell.get_id(), "message_type": message.get("type", "unknown")},
            "sent"
        )
    
    def receive_message(self, message: dict) -> dict:
        """
        CELL-012: Receive a message from another cell.
        
        Spec: docs/spec/CELL.md #CELL-012
        """
        if not self._is_alive:
            raise RuntimeError("Dead cell cannot receive messages")
        
        # Record receive operation
        self._shard.record_operation(
            "RECEIVE_MESSAGE",
            {"message_type": message.get("type", "unknown")},
            "received"
        )
        
        return message
    
    def get_state(self) -> CellState:
        """CELL-013: Get current cell state."""
        return CellState(
            cell_id=self._cell_id,
            cell_type=self._cell_type,
            generation=self._generation,
            is_alive=self._is_alive,
            timer_count=self._temporal_engine.get_timer_count(),
            register_count=self._pisphere.count_registers(),
            timestamp=time.time()
        )
    
    def is_alive(self) -> bool:
        """CELL-014: Check if cell is alive."""
        return self._is_alive
    
    def get_generation(self) -> int:
        """CELL-015: Get generation number."""
        return self._generation
    
    def __repr__(self) -> str:
        return (
            f"Cell(id={self._cell_id}, type={self._cell_type.value}, "
            f"gen={self._generation}, alive={self._is_alive})"
        )
