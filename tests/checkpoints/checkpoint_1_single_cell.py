"""
Checkpoint 1: Single Cell
Verifies that a Cell can be created, has a shard, has a pisphere,
and has a temporal engine.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cell.cell import Cell, CellType


def main():
    print("CP-1: Single Cell")
    
    # Create a cell
    cell = Cell()
    assert cell is not None, "Cell creation failed"
    assert cell.is_alive(), "Cell should be alive"
    assert cell.get_type() == CellType.UNDIFFERENTIATED
    
    # Check shard
    shard = cell.get_shard()
    assert shard is not None, "Shard missing"
    assert shard.verify(), "Shard verification failed"
    identity = shard.get_identity()
    assert identity.cell_id == cell.get_id()
    
    # Check pisphere
    pisphere = cell.get_pisphere()
    assert pisphere is not None, "Pisphere missing"
    reg_count = pisphere.count_registers()
    assert reg_count > 0, f"Pisphere should have registers, got {reg_count}"
    
    # Check temporal engine
    engine = cell.get_temporal_engine()
    assert engine is not None, "Temporal engine missing"
    
    # Create a timer
    timer = engine.create_timer(delay_us=1000)
    assert timer is not None, "Timer creation failed"
    assert engine.get_timer_count() == 1
    
    # Check state
    state = cell.get_state()
    assert state.is_alive == True
    assert state.timer_count == 1
    assert state.register_count == reg_count
    
    print(f"  ✓ Cell created: {cell.get_id()}")
    print(f"  ✓ Shard verified: {len(shard.serialize())} bytes")
    print(f"  ✓ Pisphere: {reg_count} registers")
    print(f"  ✓ Temporal engine: {engine.get_timer_count()} timer(s)")
    print("  ✓ CP-1 PASSED")


if __name__ == "__main__":
    main()
