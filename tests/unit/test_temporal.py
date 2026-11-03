"""
Unit Tests for Temporal Engine — TEMP-001 through TEMP-018

Spec Reference: docs/spec/TEMPORAL.md
"""

import sys
import os
import math
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.temporal.engine import TemporalEngine
from src.temporal.timer import Timer, TimerState
from src.temporal.gates import TemporalGate, GateType


def test_temp_001_creation():
    """TEMP-001: TemporalEngine can be created."""
    engine = TemporalEngine(resolution_us=1, max_timers=100)
    assert engine is not None
    assert engine.resolution_us == 1
    print("  ✓ TEMP-001: TemporalEngine created")


def test_temp_002_create_timer():
    """TEMP-002: Create a timer."""
    engine = TemporalEngine()
    timer = engine.create_timer(delay_us=1000, phase=(0.0, 0.0))
    
    assert timer is not None
    assert timer.id is not None
    assert engine.get_timer_count() == 1
    print(f"  ✓ TEMP-002: Timer created (id={timer.id})")


def test_temp_003_recursive_timer():
    """TEMP-003: Create recursive timer."""
    engine = TemporalEngine()
    
    # Depth 0: 1 timer
    root = engine.create_recursive_timer(delay_us=1000, depth=0)
    assert engine.get_timer_count() == 1
    
    # Depth 1: 1 root + 2 children = 3
    engine2 = TemporalEngine()
    root2 = engine2.create_recursive_timer(delay_us=1000, depth=1)
    assert engine2.get_timer_count() == 3, f"Expected 3, got {engine2.get_timer_count()}"
    
    # Depth 2: 1 + 2 + 4 = 7
    engine3 = TemporalEngine()
    root3 = engine3.create_recursive_timer(delay_us=1000, depth=2)
    assert engine3.get_timer_count() == 7, f"Expected 7, got {engine3.get_timer_count()}"
    
    print(f"  ✓ TEMP-003: Recursive timers (d0=1, d1=3, d2=7)")


def test_temp_004_apply_gate_rotate():
    """TEMP-004: Apply T_ROTATE gate."""
    engine = TemporalEngine()
    timer = engine.create_timer(delay_us=1000, phase=(0.0, 0.0))
    
    engine.apply_gate("T_ROTATE", [timer.id], {"alpha": math.pi / 4})
    
    _, phi = timer.phase
    assert abs(phi - math.pi / 4) < 0.01
    print("  ✓ TEMP-004: T_ROTATE applied")


def test_temp_004_apply_gate_hadamard():
    """TEMP-004: Apply T_HADAMARD gate."""
    engine = TemporalEngine()
    timer = engine.create_timer(delay_us=1000, phase=(0.0, 0.0))
    
    initial_count = engine.get_timer_count()
    engine.apply_gate("T_HADAMARD", [timer.id])
    
    # Hadamard creates 2 children
    assert engine.get_timer_count() == initial_count + 2
    print("  ✓ TEMP-004: T_HADAMARD applied (branched)")


def test_temp_004_apply_gate_x():
    """TEMP-004: Apply T_X gate."""
    engine = TemporalEngine()
    timer = engine.create_timer(delay_us=1000, phase=(0.0, 0.0))
    
    engine.apply_gate("T_X", [timer.id])
    
    theta, _ = timer.phase
    assert abs(theta - math.pi) < 0.01, f"X gate should flip θ to π, got {theta}"
    print("  ✓ TEMP-004: T_X applied")


def test_temp_006_measure():
    """TEMP-006: Measure a timer."""
    engine = TemporalEngine()
    timer = engine.create_timer(delay_us=1000, phase=(0.0, 0.0))
    
    result = engine.measure(timer.id)
    assert result.value in (0, 1)
    assert 0.0 <= result.probability <= 1.0
    print(f"  ✓ TEMP-006: Measurement = {result.value} (p={result.probability:.3f})")


def test_temp_007_bell_pair():
    """TEMP-007: Generate Bell pair."""
    engine = TemporalEngine()
    t1 = engine.create_timer(delay_us=1000)
    t2 = engine.create_timer(delay_us=1000)
    
    bell = engine.generate_bell_pair(t1.id, t2.id)
    assert bell["timer_a"] == t1.id
    assert bell["timer_b"] == t2.id
    print(f"  ✓ TEMP-007: Bell pair created ({bell['type']})")


def test_temp_009_timer_branch():
    """TEMP-009: Timer branching."""
    timer = Timer(id="test", target_time=time.monotonic() + 1.0, phase=(math.pi/2, 0.0))
    
    child_0, child_1 = timer.branch()
    
    assert child_0.depth == timer.depth + 1
    assert child_1.depth == timer.depth + 1
    assert timer.state == TimerState.BRANCHED
    assert len(timer.children) == 2
    print("  ✓ TEMP-009: Timer branched correctly")


def test_temp_010_timer_expire():
    """TEMP-010: Timer expiry."""
    timer = Timer(id="test", target_time=time.monotonic(), phase=(0.0, 0.0))
    
    event = timer.expire()
    
    assert timer.state == TimerState.EXPIRED
    assert event.timer_id == "test"
    assert event.measurement_value in (0, 1)
    print(f"  ✓ TEMP-010: Timer expired (value={event.measurement_value})")


def test_temp_012_through_018_gate_constructors():
    """TEMP-012 through TEMP-018: All gate constructors work."""
    gates = [
        TemporalGate.T_ROTATE(0.5),
        TemporalGate.T_SPLIT(math.pi / 2),
        TemporalGate.T_SHIFT(0.3),
        TemporalGate.T_ENTANGLE(),
        TemporalGate.T_CNOT(),
        TemporalGate.T_HADAMARD(),
        TemporalGate.T_QFT(),
        TemporalGate.T_X(),
        TemporalGate.T_Y(),
        TemporalGate.T_Z(),
        TemporalGate.T_S(),
        TemporalGate.T_T(),
        TemporalGate.T_CZ(),
        TemporalGate.T_SWAP(),
        TemporalGate.T_MEASURE(),
    ]
    
    assert len(gates) == 15
    for g in gates:
        assert g.gate_type is not None
    print(f"  ✓ TEMP-012–018: All {len(gates)} gate constructors work")


if __name__ == "__main__":
    print("=== Temporal Engine Tests ===")
    test_temp_001_creation()
    test_temp_002_create_timer()
    test_temp_003_recursive_timer()
    test_temp_004_apply_gate_rotate()
    test_temp_004_apply_gate_hadamard()
    test_temp_004_apply_gate_x()
    test_temp_006_measure()
    test_temp_007_bell_pair()
    test_temp_009_timer_branch()
    test_temp_010_timer_expire()
    test_temp_012_through_018_gate_constructors()
    print("\n=== ALL TEMPORAL TESTS PASSED ===")
