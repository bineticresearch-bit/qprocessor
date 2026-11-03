"""
Checkpoint 6: Genesis Control
Verifies that the Creator can control all Cells through the Demiurge Console.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cell.cell import Cell
from src.genesis.genesis import DemiurgeConsole


def main():
    print("CP-6: Genesis Control")
    
    # Create Creator console
    creator_key = b'creator_secret_key_for_testing'
    console = DemiurgeConsole(creator_key)
    
    # Create and register cells
    cells = []
    for i in range(5):
        cell = Cell()
        console.register_cell(cell)
        cells.append(cell)
    
    # Observe all cells
    for cell in cells:
        obs = console.observe_cell(cell.get_id())
        assert obs["alive"] == True
        assert obs["cell_id"] == cell.get_id()
    
    # Audit
    audit = console.audit_all_cells()
    assert audit["total"] == 5
    assert audit["compliant"] == 5
    assert audit["non_compliant"] == 0
    
    # Apply behavioral constraint
    console.apply_behavioral_constraint(cells[0].get_id(), "Cannot become GPU")
    
    # Kill one cell
    console.trigger_apoptosis(cells[0].get_id())
    assert not cells[0].is_alive()
    
    # Observe dead cell
    obs_dead = console.observe_cell(cells[0].get_id())
    assert obs_dead["alive"] == False
    
    # Stop heartbeat (nuclear option)
    console.stop_heartbeat()
    
    print(f"  ✓ Creator console initialized")
    print(f"  ✓ {len(cells)} cells registered")
    print(f"  ✓ All cells observed")
    print(f"  ✓ Audit: {audit['total']} total, {audit['compliant']} compliant")
    print(f"  ✓ Behavioral constraint applied")
    print(f"  ✓ Apoptosis triggered on cell 0")
    print(f"  ✓ Heartbeat stopped (nuclear option)")
    print("  ✓ CP-6 PASSED")


if __name__ == "__main__":
    main()
