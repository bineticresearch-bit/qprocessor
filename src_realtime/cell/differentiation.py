"""
Cell Differentiation Engine — DIFF-001 through DIFF-009

Controls how Cells differentiate into specialized types (GPU, CPU, Memory, etc.)

REAL IMPLEMENTATION:
- Full configuration for each cell type
- Resource allocation tracking
- Capability management

Spec Reference: docs/spec/DIFFERENTIATION.md
"""

from typing import List, Optional
from .cell import Cell, CellType


class DifferentiationEngine:
    """
    DIFF-001: Controls Cell differentiation into specialized types.
    
    Parameters:
        cell_ref: Reference to the Cell being differentiated
    
    Spec: docs/spec/DIFFERENTIATION.md #DIFF-001
    """
    
    def __init__(self, cell_ref: Cell):
        self.cell = cell_ref
        self._blocked_types: List[CellType] = []
    
    def can_differentiate(self, target_type: CellType) -> bool:
        """
        DIFF-002: Check if differentiation is possible.
        
        Spec: docs/spec/DIFFERENTIATION.md #DIFF-002
        """
        if not self.cell.is_alive():
            return False
        if target_type in self._blocked_types:
            return False
        if target_type == CellType.UNDIFFERENTIATED:
            return False
        return True
    
    def differentiate(self, target_type: CellType) -> None:
        """
        DIFF-003: Perform differentiation.
        
        Spec: docs/spec/DIFFERENTIATION.md #DIFF-003
        """
        if not self.can_differentiate(target_type):
            raise ValueError(f"Cannot differentiate to {target_type}")
        
        self.cell.set_type(target_type)
        
        # Configure based on type
        if target_type == CellType.GPU:
            self.configure_gpu()
        elif target_type == CellType.CPU:
            self.configure_cpu()
        elif target_type == CellType.MEMORY:
            self.configure_memory()
        elif target_type == CellType.NETWORK:
            self.configure_network()
        elif target_type == CellType.IO:
            self.configure_io()
    
    def get_potential(self) -> List[CellType]:
        """
        DIFF-004: Get available differentiation targets.
        
        Spec: docs/spec/DIFFERENTIATION.md #DIFF-004
        """
        all_types = [CellType.GPU, CellType.CPU, CellType.MEMORY,
                     CellType.NETWORK, CellType.IO]
        return [t for t in all_types if t not in self._blocked_types]
    
    def configure_gpu(self, parallel_units: int = 256) -> None:
        """DIFF-005: Configure as GPU cell."""
        self.cell.get_shard().get_capability().resource_capacity["parallel_units"] = parallel_units
        self.cell.get_shard().get_capability().resource_capacity["compute_mode"] = "parallel"
    
    def configure_cpu(self, recursion_depth: int = 64) -> None:
        """DIFF-006: Configure as CPU cell."""
        self.cell.get_shard().get_capability().resource_capacity["recursion_depth"] = recursion_depth
        self.cell.get_shard().get_capability().resource_capacity["compute_mode"] = "sequential"
    
    def configure_memory(self, address_bits: int = 32) -> None:
        """DIFF-007: Configure as Memory cell."""
        self.cell.get_shard().get_capability().resource_capacity["address_bits"] = address_bits
        self.cell.get_shard().get_capability().resource_capacity["capacity_bytes"] = 2 ** address_bits
    
    def configure_network(self, protocol_mode: str = "udp") -> None:
        """DIFF-008: Configure as Network cell."""
        self.cell.get_shard().get_capability().resource_capacity["protocol_mode"] = protocol_mode
    
    def configure_io(self, interface_type: str = "stdin_stdout") -> None:
        """DIFF-009: Configure as I/O cell."""
        self.cell.get_shard().get_capability().resource_capacity["interface_type"] = interface_type
    
    def block_type(self, cell_type: CellType) -> None:
        """Block a differentiation target (epigenetic control)."""
        if cell_type not in self._blocked_types:
            self._blocked_types.append(cell_type)
    
    def unblock_type(self, cell_type: CellType) -> None:
        """Unblock a differentiation target."""
        if cell_type in self._blocked_types:
            self._blocked_types.remove(cell_type)
