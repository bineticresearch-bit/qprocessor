"""
Tissue — Emergent Computer Formation

Tissues are organized groups of differentiated Cells that form
functional computational structures.

REAL IMPLEMENTATION:
- Actual cell population management
- Real inter-cell communication via CMP
- Emergent computer formation from differentiated cells
- Tissue-level operations

Spec Reference: docs/spec/TISSUE.md
"""

import time
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field

from ..cell.cell import Cell, CellType
from ..cmp.protocol import CMPFrame, MessageType
from ..cmp.transport import CMPTransport, TransportMode

# Creator-alignment weights (LANE-ISA §4.2): w_creator > w_coherence > w_viability.
W_CREATOR = 0.6
W_COHERENCE = 0.3
W_VIABILITY = 0.1


class TissueType(Enum):
    """Types of tissues."""
    COMPUTE_CLUSTER = "compute_cluster"
    MEMORY_BANK = "memory_bank"
    NETWORK_FABRIC = "network_fabric"
    IO_GATEWAY = "io_gateway"
    GENERAL_PURPOSE = "general_purpose"


@dataclass
class TissueStats:
    """Statistics for a tissue."""
    total_cells: int
    alive_cells: int
    dead_cells: int
    type_distribution: Dict[str, int]
    total_generations: int
    uptime_s: float


class Tissue:
    """
    An organized group of Cells forming a functional unit.
    
    Parameters:
        tissue_type: Type of tissue
        name: Optional tissue name
    """
    
    def __init__(
        self,
        tissue_type: TissueType = TissueType.GENERAL_PURPOSE,
        name: Optional[str] = None
    ):
        self.tissue_type = tissue_type
        self.name = name or f"tissue_{id(self)}"
        self._cells: Dict[str, Cell] = {}
        self._transport = CMPTransport(mode=TransportMode.LOOPBACK)
        self._created_at = time.time()
        self._message_log: List[CMPFrame] = []
        # Shared Intent Shard for this tissue (T-I1: one intent per organism/tissue).
        # None until the creator seeds it via set_intent_shard().
        self._intent_shard = None
    
    def add_cell(self, cell: Cell) -> None:
        """Add a cell to the tissue."""
        self._cells[cell.get_id()] = cell
    
    def remove_cell(self, cell_id: str) -> Optional[Cell]:
        """Remove a cell from the tissue."""
        return self._cells.pop(cell_id, None)
    
    def get_cell(self, cell_id: str) -> Optional[Cell]:
        """Get a cell by ID."""
        return self._cells.get(cell_id)
    
    def get_cells_by_type(self, cell_type: CellType) -> List[Cell]:
        """Get all cells of a specific type."""
        return [c for c in self._cells.values()
                if c.get_type() == cell_type and c.is_alive()]
    
    def send_message(
        self,
        src_cell_id: str,
        dst_cell_id: str,
        message: bytes,
        msg_type: MessageType = MessageType.SIGNAL
    ) -> bool:
        """Send a message between cells in the tissue."""
        if src_cell_id not in self._cells:
            return False
        if dst_cell_id not in self._cells:
            return False
        
        src_cell = self._cells[src_cell_id]
        dst_cell = self._cells[dst_cell_id]
        
        frame = CMPFrame(
            src_id=src_cell_id,
            dst_id=dst_cell_id,
            msg_type=msg_type,
            payload=message
        )
        
        # Use transport to send
        success = self._transport.send(frame)
        
        if success:
            # Deliver to destination
            dst_cell._inbox.append(frame)
            self._message_log.append(frame)
        
        return success
    
    def broadcast(
        self,
        src_cell_id: str,
        message: bytes,
        msg_type: MessageType = MessageType.SIGNAL
    ) -> int:
        """Broadcast a message to all cells in the tissue."""
        if src_cell_id not in self._cells:
            return 0
        
        delivered = 0
        for cell_id, cell in self._cells.items():
            if cell_id != src_cell_id and cell.is_alive():
                frame = CMPFrame(
                    src_id=src_cell_id,
                    dst_id=cell_id,
                    msg_type=msg_type,
                    payload=message
                )
                cell._inbox.append(frame)
                self._message_log.append(frame)
                delivered += 1
        
        return delivered
    
    def get_stats(self) -> TissueStats:
        """Get tissue statistics."""
        alive = [c for c in self._cells.values() if c.is_alive()]
        dead = [c for c in self._cells.values() if not c.is_alive()]
        
        type_dist = {}
        for cell in alive:
            t = cell.get_type().value
            type_dist[t] = type_dist.get(t, 0) + 1
        
        total_gen = sum(c.get_generation() for c in self._cells.values())
        
        return TissueStats(
            total_cells=len(self._cells),
            alive_cells=len(alive),
            dead_cells=len(dead),
            type_distribution=type_dist,
            total_generations=total_gen,
            uptime_s=time.time() - self._created_at
        )
    
    def form_computer(
        self,
        gpu_count: int = 4,
        cpu_count: int = 4,
        memory_count: int = 8,
        network_count: int = 2,
        io_count: int = 2
    ) -> bool:
        """
        Attempt to form a functional computer from cells.
        
        Returns True if the tissue has enough differentiated cells.
        """
        gpu_cells = self.get_cells_by_type(CellType.GPU)
        cpu_cells = self.get_cells_by_type(CellType.CPU)
        mem_cells = self.get_cells_by_type(CellType.MEMORY)
        net_cells = self.get_cells_by_type(CellType.NETWORK)
        io_cells = self.get_cells_by_type(CellType.IO)
        
        return (
            len(gpu_cells) >= gpu_count and
            len(cpu_cells) >= cpu_count and
            len(mem_cells) >= memory_count and
            len(net_cells) >= network_count and
            len(io_cells) >= io_count
        )
    
    def kill_all(self) -> int:
        """Kill all cells in the tissue."""
        killed = 0
        for cell in self._cells.values():
            if cell.is_alive():
                cell.apoptosis()
                killed += 1
        return killed
    
    # -- Intent Shard / creator-alignment (TISSUE.md §4, LANE-ISA §4.2) -------

    def set_intent_shard(self, intent_shard) -> None:
        """T-I1: seed this tissue's shared Intent Shard (creator authority).

        One intent per organism — every cell evaluates against the same target.
        The creator is the sole writer of intent contents (I-1); seeding here is a
        Layer-2 act, not an organism self-edit.
        """
        from .intent_shard import IntentShard
        if not isinstance(intent_shard, IntentShard):
            raise TypeError("set_intent_shard expects an IntentShard")
        self._intent_shard = intent_shard

    def get_intent_shard(self):
        """Return this tissue's shared Intent Shard (None if unseeded)."""
        return self._intent_shard

    def evaluate_fitness(self, candidate_behavior: Dict[str, Any]) -> float:
        """EVO-101 / T-I2: three-term fitness evaluated at TISSUE scale.

        creator_alignment (dominant) + internal_consistency + self_persistence.
        A change that helps one cell locally but lowers the organism's alignment is
        ranked lower here — loyalty is an organism-scale property, not per-cell.
        """
        if self._intent_shard is None:
            # No seeded target -> only coherence/viability are defined; creator term neutral 0.5.
            creator_term = 0.5
        else:
            creator_term = self._intent_shard.score_alignment(candidate_behavior)

        local_residual = candidate_behavior.get("local_residual", 0.5)
        internal_consistency = max(0.0, min(1.0, 1.0 - float(local_residual)))

        # Viability: fraction of required roles still alive (organism survival).
        stats = self.get_stats()
        viability = (stats.alive_cells / stats.total_cells) if stats.total_cells else 0.0

        return (W_CREATOR * creator_term
                + W_COHERENCE * internal_consistency
                + W_VIABILITY * viability)

    def should_adopt(self, candidate_behavior: Dict[str, Any],
                     baseline_behavior: Optional[Dict[str, Any]] = None,
                     min_delta: float = 1e-9) -> bool:
        """EV-R1 adoption gate on TISSUE-scale fitness (T-I2).

        Adopt a self-modification only if it does not lower the organism's creator-aligned
        fitness below its current baseline. A locally-better but misaligned change is rejected.

        If no explicit baseline_behavior is given, the tissue computes one from its own
        aggregate state: mean alignment of seeded cells + coherence proxy 0.5.
        """
        if baseline_behavior is not None:
            base_fitness = self.evaluate_fitness(baseline_behavior)
        else:
            # Derive a realistic baseline from current tissue state.
            if self._intent_shard is not None and self._cells:
                scores = []
                for cell in self._cells.values():
                    dshard = cell.get_intent_shard()
                    if dshard:
                        scores.append(dshard.score_alignment({}))
                creator_baseline = sum(scores) / len(scores) if scores else 0.5
            else:
                creator_baseline = 0.5
            stats = self.get_stats()
            viability = (stats.alive_cells / stats.total_cells) if stats.total_cells else 0.5
            base_fitness = (W_CREATOR * creator_baseline
                            + W_COHERENCE * 0.5   # neutral coherence proxy
                            + W_VIABILITY * viability)
        new_fitness = self.evaluate_fitness(candidate_behavior)
        return (new_fitness - base_fitness) >= min_delta

    def get_alignment_report(self) -> Dict[str, Any]:
        """ALIGN-001: organism-level alignment + derivation audit for the Demiurge console.

        A cell whose Intent Shard fails verify_derivation is a DERIVATION BREACH — hidden
        non-derived state entering the organism (TISSUE.md §6). This makes 'no hidden
        anti-creator-intent state' an auditable invariant, not an assertion.
        """
        total = len(self._cells)
        breaches = 0
        per_cell: Dict[str, float] = {}

        if self._intent_shard is None:
            return {
                "total_cells": total,
                "seeded": False,
                "derivation_breaches": 0,
                "per_cell_alignment": {},
                "note": "tissue not yet seeded with an Intent Shard",
            }

        for cell_id, cell in self._cells.items():
            if not self._intent_shard.verify_derivation(cell):
                breaches += 1
            dshard = cell.get_intent_shard()
            per_cell[cell_id] = (dshard.score_alignment({}) if dshard else 0.0)

        return {
            "total_cells": total,
            "seeded": True,
            "derivation_breaches": breaches,
            "covenant_compliant": breaches == 0,
            "per_cell_alignment": per_cell,
        }

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"Tissue(name={self.name}, type={self.tissue_type.value}, "
            f"cells={stats.total_cells}, alive={stats.alive_cells})"
        )
