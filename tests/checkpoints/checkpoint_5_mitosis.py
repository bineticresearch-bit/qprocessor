"""
Checkpoint 5: Cell Mitosis
Verifies that Cells can replicate and daughters have correct lineage.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cell.cell import Cell


def main():
    print("CP-5: Cell Mitosis")
    
    # Create parent
    parent = Cell()
    parent_id = parent.get_id()
    parent_gen = parent.get_generation()
    
    assert parent_gen == 0, "Parent should be generation 0"
    
    # Replicate
    d1, d2 = parent.mitosis()
    
    # Check daughters
    assert d1 is not None and d2 is not None
    assert d1.get_id() != d2.get_id(), "Daughters should have different IDs"
    assert d1.get_id() != parent_id, "Daughter should differ from parent"
    assert d1.get_generation() == 1, "Daughters should be generation 1"
    assert d2.get_generation() == 1
    
    # Check parent died
    assert not parent.is_alive(), "Parent should die after mitosis"
    
    # Check lineage
    d1_lineage = d1.get_shard().get_lineage()
    assert parent_id in d1_lineage.ancestor_chain, "Parent should be in daughter's ancestry"
    
    # Second generation mitosis
    d1a, d1b = d1.mitosis()
    assert d1a.get_generation() == 2
    assert d1b.get_generation() == 2
    
    d1a_lineage = d1a.get_shard().get_lineage()
    assert d1.get_id() in d1a_lineage.ancestor_chain
    assert parent_id in d1a_lineage.ancestor_chain
    
    print(f"  ✓ Parent: {parent_id} (gen 0) → died")
    print(f"  ✓ Daughter 1: {d1.get_id()} (gen 1)")
    print(f"  ✓ Daughter 2: {d2.get_id()} (gen 1)")
    print(f"  ✓ Granddaughter: {d1a.get_id()} (gen 2)")
    print(f"  ✓ Lineage preserved across generations")
    print("  ✓ CP-5 PASSED")


if __name__ == "__main__":
    main()
