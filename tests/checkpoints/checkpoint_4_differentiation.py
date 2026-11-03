"""
Checkpoint 4: Cell Differentiation
Verifies that Cells can differentiate into all types.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cell.cell import Cell, CellType
from src.cell.differentiation import DifferentiationEngine


def main():
    print("CP-4: Cell Differentiation")
    
    types_to_test = [CellType.GPU, CellType.CPU, CellType.MEMORY, CellType.NETWORK, CellType.IO]
    
    for target_type in types_to_test:
        cell = Cell()
        engine = DifferentiationEngine(cell)
        
        # Check potential
        potential = engine.get_potential()
        assert target_type in potential, f"{target_type} should be in potential"
        
        # Differentiate
        engine.differentiate(target_type)
        assert cell.get_type() == target_type, f"Cell should be {target_type}"
        
        print(f"  ✓ {target_type.value}: differentiated successfully")
    
    print("  ✓ CP-4 PASSED")


if __name__ == "__main__":
    main()
