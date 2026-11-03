"""
Unit Tests for Cell Core — CELL-001 through CELL-015

Spec Reference: docs/spec/CELL.md
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cell.cell import Cell, CellType, CellState
from src.cell.shard import SelfDescribingShard


def test_cell_001_creation():
    """CELL-001: Cell can be created."""
    cell = Cell()
    assert cell is not None
    assert cell.is_alive()
    print(f"  ✓ CELL-001: Cell created (id={cell.get_id()})")


def test_cell_002_get_id():
    """CELL-002: Get cell ID."""
    cell = Cell()
    cell_id = cell.get_id()
    assert cell_id is not None
    assert cell_id.startswith("cell_")
    print(f"  ✓ CELL-002: ID = {cell_id}")


def test_cell_003_get_shard():
    """CELL-003: Get self-describing shard."""
    cell = Cell()
    shard = cell.get_shard()
    assert shard is not None
    assert isinstance(shard, SelfDescribingShard)
    print("  ✓ CELL-003: Shard retrieved")


def test_cell_004_get_pisphere():
    """CELL-004: Get pisphere."""
    cell = Cell()
    pisphere = cell.get_pisphere()
    assert pisphere is not None
    assert pisphere.count_registers() > 0
    print(f"  ✓ CELL-004: Pisphere has {pisphere.count_registers()} registers")


def test_cell_005_get_temporal_engine():
    """CELL-005: Get temporal engine."""
    cell = Cell()
    engine = cell.get_temporal_engine()
    assert engine is not None
    print("  ✓ CELL-005: Temporal engine retrieved")


def test_cell_006_get_type():
    """CELL-006: Get cell type."""
    cell = Cell()
    assert cell.get_type() == CellType.UNDIFFERENTIATED
    print("  ✓ CELL-006: Type = UNDIFFERENTIATED")


def test_cell_007_set_type():
    """CELL-007: Set cell type."""
    cell = Cell()
    cell.set_type(CellType.GPU)
    assert cell.get_type() == CellType.GPU
    print("  ✓ CELL-007: Type set to GPU")


def test_cell_008_differentiate():
    """CELL-008: Differentiate cell."""
    cell = Cell()
    cell.differentiate(CellType.CPU)
    assert cell.get_type() == CellType.CPU
    print("  ✓ CELL-008: Differentiated to CPU")


def test_cell_009_mitosis():
    """CELL-009: Cell mitosis."""
    cell = Cell()
    original_id = cell.get_id()
    
    d1, d2 = cell.mitosis()
    
    assert d1 is not None
    assert d2 is not None
    assert d1.get_id() != d2.get_id()
    assert d1.get_id() != original_id
    assert d1.get_generation() == 1
    assert d2.get_generation() == 1
    assert not cell.is_alive(), "Original cell should die after mitosis"
    print(f"  ✓ CELL-009: Mitosis → {d1.get_id()}, {d2.get_id()}")


def test_cell_010_apoptosis():
    """CELL-010: Cell apoptosis."""
    cell = Cell()
    assert cell.is_alive()
    cell.apoptosis()
    assert not cell.is_alive()
    print("  ✓ CELL-010: Apoptosis completed")


def test_cell_013_get_state():
    """CELL-013: Get cell state."""
    cell = Cell()
    state = cell.get_state()
    assert isinstance(state, CellState)
    assert state.cell_id == cell.get_id()
    assert state.is_alive == True
    print(f"  ✓ CELL-013: State = {state.cell_type.value}, gen={state.generation}")


def test_cell_014_is_alive():
    """CELL-014: Check if alive."""
    cell = Cell()
    assert cell.is_alive() == True
    cell.apoptosis()
    assert cell.is_alive() == False
    print("  ✓ CELL-014: is_alive() works")


def test_cell_015_get_generation():
    """CELL-015: Get generation."""
    cell = Cell()
    assert cell.get_generation() == 0
    
    d1, d2 = cell.mitosis()
    assert d1.get_generation() == 1
    print("  ✓ CELL-015: Generation tracking works")


def test_shard_sections():
    """Test all 9 shard sections."""
    cell = Cell()
    shard = cell.get_shard()
    
    # SHARD-002: Identity
    identity = shard.get_identity()
    assert identity.cell_id == cell.get_id()
    
    # SHARD-003: Position
    position = shard.get_position()
    assert position.lattice_coords is not None
    
    # SHARD-004: Lineage
    lineage = shard.get_lineage()
    assert lineage.generation_path == [0]
    
    # SHARD-005: Operations
    ops = shard.get_operations()
    assert len(ops.operation_log) > 0  # At least CREATE
    
    # SHARD-006: Temporal
    temporal = shard.get_temporal_significance()
    assert temporal.creation_time_ns > 0
    
    # SHARD-007: Receipts
    receipts = shard.get_receipts()
    assert receipts is not None
    
    # SHARD-008: History
    history = shard.get_history()
    assert history is not None
    
    # SHARD-009: Capability
    capability = shard.get_capability()
    assert "gpu" in capability.differentiation_potential
    
    # SHARD-010: Self-reference
    self_hash = shard.get_self_reference()
    assert len(self_hash) == 32
    
    # SHARD-011: Serialize
    serialized = shard.serialize()
    assert len(serialized) > 0
    
    # SHARD-012: Verify
    assert shard.verify() == True
    
    print("  ✓ All 9 shard sections verified")


if __name__ == "__main__":
    print("=== Cell Tests ===")
    test_cell_001_creation()
    test_cell_002_get_id()
    test_cell_003_get_shard()
    test_cell_004_get_pisphere()
    test_cell_005_get_temporal_engine()
    test_cell_006_get_type()
    test_cell_007_set_type()
    test_cell_008_differentiate()
    test_cell_009_mitosis()
    test_cell_010_apoptosis()
    test_cell_013_get_state()
    test_cell_014_is_alive()
    test_cell_015_get_generation()
    test_shard_sections()
    print("\n=== ALL CELL TESTS PASSED ===")
