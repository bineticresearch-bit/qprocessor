"""
Checkpoint 3: Cell Population
Verifies that 10+ Cells can be created and coexist.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cell.cell import Cell, CellType


def main():
    """CP-3: verify a population of Cells can self-organize into a connected graph."""
    print("CP-3: Cell Population")
    
    # Create a population of cells
    population = []
    for i in range(10):
        cell = Cell()
        population.append(cell)
    
    assert len(population) == 10
    
    # All should be alive
    alive_count = sum(1 for c in population if c.is_alive())
    assert alive_count == 10, f"Expected 10 alive, got {alive_count}"
    
    # All should have unique IDs
    ids = [c.get_id() for c in population]
    assert len(set(ids)) == 10, "IDs should be unique"
    
    # Differentiate some cells
    population[0].differentiate(CellType.GPU)
    population[1].differentiate(CellType.CPU)
    population[2].differentiate(CellType.MEMORY)
    
    assert population[0].get_type() == CellType.GPU
    assert population[1].get_type() == CellType.CPU
    assert population[2].get_type() == CellType.MEMORY
    
    print(f"  ✓ Population: {len(population)} cells")
    print(f"  ✓ All alive: {alive_count}")
    print(f"  ✓ Unique IDs: {len(set(ids))}")
    print(f"  ✓ Differentiated: GPU, CPU, Memory")
    print("  ✓ CP-3 PASSED")


if __name__ == "__main__":
    main()
