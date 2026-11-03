"""
Cell Differentiation Engine — DIFF-001 through DIFF-009

Controls how Cells differentiate into specialized types (GPU, CPU, Memory, etc.)

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
        DIFF-002: Check if the Cell can differentiate to the target type.
        
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
        DIFF-003: Differentiate the Cell to the target type.
        
        Spec: docs/spec/DIFFERENTIATION.md #DIFF-003
        """
        if not self.can_differentiate(target_type):
            raise ValueError(f"Cannot differentiate to {target_type}")
        
        # Configure based on type
        if target_type == CellType.GPU:
            self.configure_gpu(parallel_units=1024)
        elif target_type == CellType.CPU:
            self.configure_cpu(recursion_depth=20)
        elif target_type == CellType.MEMORY:
            self.configure_memory(address_bits=32)
        elif target_type == CellType.NETWORK:
            self.configure_network(protocol_mode="raw_ethernet")
        elif target_type == CellType.IO:
            self.configure_io(interface_type="stdin_stdout")
        
        self.cell.set_type(target_type)
    
    def get_potential(self) -> List[CellType]:
        """
        DIFF-004: Get available differentiation types.
        
        Spec: docs/spec/DIFFERENTIATION.md #DIFF-004
        """
        all_types = [CellType.GPU, CellType.CPU, CellType.MEMORY, CellType.NETWORK, CellType.IO]
        return [t for t in all_types if t not in self._blocked_types]
    
    def configure_gpu(self, parallel_units: int = 1024) -> None:
        """DIFF-005: Configure as GPU cell."""
        self.cell.get_shard().get_capability().resource_capacity["parallel_units"] = parallel_units
    
    def configure_cpu(self, recursion_depth: int = 20) -> None:
        """DIFF-006: Configure as CPU cell."""
        self.cell.get_shard().get_capability().resource_capacity["recursion_depth"] = recursion_depth
    
    def configure_memory(self, address_bits: int = 32) -> None:
        """DIFF-007: Configure as Memory cell."""
        self.cell.get_shard().get_capability().resource_capacity["address_bits"] = address_bits
    
    def configure_network(self, protocol_mode: str = "raw_ethernet") -> None:
        """DIFF-008: Configure as Network cell."""
        self.cell.get_shard().get_capability().resource_capacity["protocol_mode"] = protocol_mode
    
    def configure_io(self, interface_type: str = "stdin_stdout") -> None:
        """DIFF-009: Configure as I/O cell."""
        self.cell.get_shard().get_capability().resource_capacity["interface_type"] = interface_type
