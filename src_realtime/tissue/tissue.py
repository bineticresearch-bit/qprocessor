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
    
    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"Tissue(name={self.name}, type={self.tissue_type.value}, "
            f"cells={stats.total_cells}, alive={stats.alive_cells})"
        )
