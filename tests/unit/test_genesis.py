"""
Unit Tests for Genesis Protocol — Creator Control

Spec Reference: docs/spec/GENESIS.md (CREATOR-ONLY)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cell.cell import Cell, CellType
from src.genesis.genesis import (
    GenesisSignature,
    TemporalKillSwitch,
    EpigeneticController,
    CovenantProtocol,
    DemiurgeConsole,
)


def test_genesis_signature():
    """Test Genesis Signature creation and verification."""
    key = b'creator_secret_key_1234567890'
    genesis = GenesisSignature(key)
    
    cell = Cell()
    genesis.embed_in_cell(cell)
    
    assert genesis.verify_cell(cell) == True
    
    # Unregistered cell should fail
    other_cell = Cell()
    assert genesis.verify_cell(other_cell) == False
    
    print("  ✓ Genesis Signature: embed and verify")


def test_kill_switch():
    """Test Temporal Kill Switch."""
    key = b'creator_secret_key_1234567890'
    genesis = GenesisSignature(key)
    ks = TemporalKillSwitch(key, genesis)
    
    cell = Cell()
    ks.embed_kill_switch(cell)
    
    # Heartbeat should be current
    assert ks.check_heartbeat(cell) == True
    
    # Trigger apoptosis
    ks.trigger_apoptosis(cell)
    assert not cell.is_alive()
    
    print("  ✓ Kill Switch: embed, heartbeat, apoptosis")


def test_epigenetic_override():
    """Test Epigenetic Override."""
    key = b'creator_secret_key_1234567890'
    genesis = GenesisSignature(key)
    epi = EpigeneticController(key, genesis)
    
    cell = Cell()
    cell_id = cell.get_id()
    
    # Apply behavioral constraint
    epi.apply_behavioral_constraint(cell_id, "Cannot become GPU")
    
    # Apply resource limit
    epi.apply_resource_limit(cell_id, max_timers=100, max_memory=1024)
    
    # Apply differentiation block
    epi.apply_differentiation_block(cell_id, ["gpu", "network"])
    
    print("  ✓ Epigenetic Override: marks applied")


def test_covenant_protocol():
    """Test Covenant Protocol."""
    covenant = CovenantProtocol()
    
    cell = Cell()
    assert covenant.check_compliance(cell) == True
    
    print("  ✓ Covenant Protocol: compliance check")


def test_demiurge_console():
    """Test Demiurge Console."""
    key = b'creator_secret_key_1234567890'
    console = DemiurgeConsole(key)
    
    # Create and register cells
    cell1 = Cell()
    cell2 = Cell()
    console.register_cell(cell1)
    console.register_cell(cell2)
    
    # Observe cells
    obs1 = console.observe_cell(cell1.get_id())
    assert obs1["alive"] == True
    assert obs1["cell_id"] == cell1.get_id()
    
    # Audit
    audit = console.audit_all_cells()
    assert audit["total"] == 2
    assert audit["compliant"] == 2
    
    # Trigger apoptosis
    console.trigger_apoptosis(cell1.get_id())
    assert not cell1.is_alive()
    
    # Observe dead cell
    obs1_dead = console.observe_cell(cell1.get_id())
    assert obs1_dead["alive"] == False
    
    print("  ✓ Demiurge Console: observe, audit, apoptosis")


if __name__ == "__main__":
    print("=== Genesis Protocol Tests ===")
    test_genesis_signature()
    test_kill_switch()
    test_epigenetic_override()
    test_covenant_protocol()
    test_demiurge_console()
    print("\n=== ALL GENESIS TESTS PASSED ===")
