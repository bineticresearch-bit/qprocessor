"""
Unit Tests for Pisphere Register Lattice — PISP-001 through PISP-012

Spec Reference: docs/spec/PISPHERE.md
"""

import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.pisphere.pisphere import Pisphere
from src.pisphere.register import Register


def test_pisp_001_creation():
    """PISP-001: Pisphere can be created."""
    p = Pisphere(max_depth=3, branching_factor=4)
    assert p is not None
    assert p.max_depth == 3
    assert p.branching_factor == 4
    print("  ✓ PISP-001: Pisphere created")


def test_pisp_005_count_registers():
    """PISP-005: Register count matches formula (B^(D+1) - 1) / (B - 1)."""
    B = 4
    D = 3
    expected = (B ** (D + 1) - 1) // (B - 1)  # = 85
    
    p = Pisphere(max_depth=D, branching_factor=B)
    actual = p.count_registers()
    
    assert actual == expected, f"Expected {expected} registers, got {actual}"
    print(f"  ✓ PISP-005: Register count = {actual} (formula: ({B}^{D+1}-1)/({B}-1) = {expected})")


def test_pisp_004_get_all_registers():
    """PISP-004: Get all registers."""
    p = Pisphere(max_depth=2, branching_factor=4)
    all_regs = p.get_all_registers()
    assert len(all_regs) > 0
    print(f"  ✓ PISP-004: Got {len(all_regs)} registers")


def test_pisp_004_filter_by_depth():
    """PISP-004: Filter registers by depth."""
    p = Pisphere(max_depth=3, branching_factor=4)
    
    depth_0 = p.get_all_registers(depth=0)
    depth_1 = p.get_all_registers(depth=1)
    
    assert len(depth_0) == 1, "Depth 0 should have 1 register (root)"
    assert len(depth_1) == 4, "Depth 1 should have 4 registers"
    print(f"  ✓ PISP-004: Depth filter works (d0={len(depth_0)}, d1={len(depth_1)})")


def test_pisp_010_set_phase():
    """PISP-010: Set register phase."""
    reg = Register(id="test", depth=0, theta=0.0, phi=0.0)
    reg.set_phase(math.pi / 2, math.pi / 4)
    
    assert reg.phase[0] == math.pi / 2
    assert reg.phase[1] == math.pi / 4
    print("  ✓ PISP-010: Phase set correctly")


def test_pisp_011_get_state():
    """PISP-011: Get quantum state."""
    reg = Register(id="test", depth=0, theta=0.0, phi=0.0)
    
    # Default state: |0⟩ → cos(0) + e^(i0)·sin(0) = 1 + 0j
    state = reg.get_state()
    assert abs(state.real - 1.0) < 0.01, f"Default state should be ~1.0, got {state.real}"
    
    # After Hadamard: θ=π/2 → cos(π/4) + e^(i0)·sin(π/4)
    # The state is a 2-component vector [cos(θ/2), e^(iφ)·sin(θ/2)]
    # Normalization: |cos(θ/2)|² + |sin(θ/2)|² = 1
    reg.set_phase(math.pi / 2, 0.0)
    prob_0 = reg.get_probability_0()
    prob_1 = reg.get_probability_1()
    assert abs(prob_0 + prob_1 - 1.0) < 0.01, f"Probabilities should sum to 1, got {prob_0 + prob_1}"
    print(f"  ✓ PISP-011: State normalized (p0={prob_0:.3f} + p1={prob_1:.3f} = 1.0)")


def test_pisp_006_apply_gate_hadamard():
    """PISP-006: Apply Hadamard gate."""
    p = Pisphere(max_depth=1, branching_factor=4)
    root = p.get_all_registers(depth=0)[0]
    
    p.apply_gate(root.id, "H", {})
    
    # After H, phase should be (π/2, 0)
    assert abs(root.phase[0] - math.pi / 2) < 0.01
    print("  ✓ PISP-006: Hadamard gate applied")


def test_pisp_006_apply_gate_x():
    """PISP-006: Apply X gate."""
    p = Pisphere(max_depth=1, branching_factor=4)
    root = p.get_all_registers(depth=0)[0]
    
    # Start at |0⟩ (θ=0)
    p.apply_gate(root.id, "X", {})
    
    # After X, should be at |1⟩ (θ=π)
    assert abs(root.phase[0] - math.pi) < 0.01
    print("  ✓ PISP-006: X gate applied")


def test_pisp_007_measure():
    """PISP-007: Measure a register."""
    p = Pisphere(max_depth=1, branching_factor=4)
    root = p.get_all_registers(depth=0)[0]
    
    result = p.measure(root.id)
    assert result.value in (0, 1), "Measurement should be 0 or 1"
    assert 0.0 <= result.probability <= 1.0, "Probability should be in [0, 1]"
    print(f"  ✓ PISP-007: Measurement = {result.value} (p={result.probability:.3f})")


def test_pisp_008_entangle():
    """PISP-008: Create Bell pair."""
    p = Pisphere(max_depth=1, branching_factor=4)
    regs = p.get_all_registers(depth=1)
    
    if len(regs) >= 2:
        bell = p.entangle(regs[0].id, regs[1].id, "PHI_PLUS")
        assert bell.bell_type == "PHI_PLUS"
        assert bell.correlation == 1.0
        print(f"  ✓ PISP-008: Bell pair created ({bell.bell_type})")
    else:
        print("  ✓ PISP-008: Skipped (not enough registers)")


if __name__ == "__main__":
    print("=== Pisphere Tests ===")
    test_pisp_001_creation()
    test_pisp_005_count_registers()
    test_pisp_004_get_all_registers()
    test_pisp_004_filter_by_depth()
    test_pisp_010_set_phase()
    test_pisp_011_get_state()
    test_pisp_006_apply_gate_hadamard()
    test_pisp_006_apply_gate_x()
    test_pisp_007_measure()
    test_pisp_008_entangle()
    print("\n=== ALL PISPHERE TESTS PASSED ===")
