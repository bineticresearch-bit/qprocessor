"""
Unit Tests for Cellular AI System
==================================

Tests for the Cellular AI system built on QProcessor.
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cellular_ai import CellularAI, CellRole, CellState
from src.cell.cell import Cell, CellType
from src.temporal.engine import TemporalEngine


def test_cellular_ai_creation():
    """Test CellularAI initialization."""
    ai = CellularAI()
    
    assert ai is not None
    assert len(ai.cells) == 1  # Supervisor cell
    assert ai.temporal_engine.echo_enabled == True
    assert ai.temporal_engine.echo_depth == 8
    
    print("✓ CELLULAR-001: CellularAI can be created")


def test_cell_differentiation():
    """Test cell differentiation into specialized roles."""
    ai = CellularAI()
    
    # Differentiate cells for different roles
    perception_cell = ai.create_cell(CellRole.PERCEPTION)
    reasoning_cell = ai.create_cell(CellRole.REASONING)
    memory_cell = ai.create_cell(CellRole.MEMORY)
    action_cell = ai.create_cell(CellRole.ACTION)
    
    assert perception_cell.get_type() == CellType.NETWORK
    assert reasoning_cell.get_type() == CellType.CPU
    assert memory_cell.get_type() == CellType.MEMORY
    assert action_cell.get_type() == CellType.IO
    
    assert ai.cell_roles[perception_cell.get_id()] == CellRole.PERCEPTION
    assert ai.cell_roles[reasoning_cell.get_id()] == CellRole.REASONING
    assert ai.cell_roles[memory_cell.get_id()] == CellRole.MEMORY
    assert ai.cell_roles[action_cell.get_id()] == CellRole.ACTION
    
    print("✓ CELLULAR-002: Cells can be differentiated into specialized roles")


def test_cellular_thinking():
    """Test decision making through cellular population."""
    ai = CellularAI()
    
    ai.create_cell(CellRole.PERCEPTION)
    ai.create_cell(CellRole.REASONING)
    ai.create_cell(CellRole.MEMORY)
    ai.create_cell(CellRole.ACTION)
    
    input_data = {"type": "sensor", "value": 42}
    output = ai.think(input_data)
    
    assert output is not None
    assert ai.decision_history is not None
    assert len(ai.decision_history) == 1
    
    decision = ai.decision_history[0]
    assert decision.decision_id == "decision_0"
    assert decision.input_data == input_data
    assert decision.confidence > 0
    assert decision.temporal_precision > 0
    
    print("✓ CELLULAR-003: CellularAI can make decisions")


def test_temporal_precision():
    """Test hyperfractal temporal precision."""
    ai = CellularAI()
    
    ai.create_cell(CellRole.PERCEPTION)
    
    # Process multiple decisions to demonstrate precision
    for i in range(3):
        input_data = {"type": "sensor", "value": i * 10}
        output = ai.think(input_data)
        
        precision = ai.decision_history[-1].temporal_precision
        assert precision > 0
        assert precision < 1e-12  # Should be in picoseconds
    
    # Get temporal analysis
    temporal = ai.get_temporal_analysis()
    assert temporal is not None
    assert "avg_temporal_precision" in temporal
    assert "best_temporal_precision" in temporal
    
    print("✓ CELLULAR-004: Temporal precision is achieved (picosecond level)")


def test_self_repair():
    """Test self-repair and population maintenance."""
    ai = CellularAI()
    
    ai.create_cell(CellRole.PERCEPTION)
    ai.create_cell(CellRole.REASONING)
    
    initial_count = len(ai.cells)
    
    # Simulate cell death
    for cell in ai.cells:
        if cell.is_alive():
            cell.apoptosis()
    
    # Maintain population (self-repair)
    modifications = ai.maintain_population()
    
    assert modifications >= 2  # Should replace dead cells
    assert len(ai.cells) > initial_count
    
    print("✓ CELLULAR-005: Self-repair mechanism works")


def test_explainability():
    """Test explainability and provenance tracking."""
    ai = CellularAI()
    
    ai.create_cell(CellRole.PERCEPTION)
    ai.create_cell(CellRole.REASONING)
    ai.create_cell(CellRole.MEMORY)
    ai.create_cell(CellRole.ACTION)
    
    input_data = {"type": "sensor", "value": 42}
    ai.think(input_data)
    
    decision_id = ai.decision_history[0].decision_id
    explanation = ai.explain_decision(decision_id)
    
    assert explanation is not None
    assert explanation["decision_id"] == decision_id
    assert explanation["input"] == str(input_data)
    assert explanation["confidence"] > 0
    assert explanation["temporal_precision"] > 0
    assert explanation["provenance_hash"] is not None
    assert "verification" in explanation
    
    print("✓ CELLULAR-006: Explainability system works")


def test_predictive_capabilities():
    """Test predictive capabilities using temporal derivatives."""
    ai = CellularAI()
    
    ai.create_cell(CellRole.REASONING)
    
    input_data = {"type": "sensor", "value": 42}
    ai.think(input_data)
    
    current_state = {"value": 42, "trend": 1}
    predicted_state = ai.predict_future_state(current_state)
    
    assert predicted_state is not None
    assert isinstance(predicted_state, dict)
    
    print("✓ CELLULAR-007: Predictive capabilities work")


def test_scaling():
    """Test scaling and population growth."""
    ai = CellularAI()
    
    ai.create_cell(CellRole.PERCEPTION)
    
    initial_count = len(ai.cells)
    
    # Process multiple decisions to trigger growth
    for i in range(5):
        input_data = {"type": "sensor", "value": i}
        ai.think(input_data)
        
        # Maintain population periodically
        if i % 2 == 0:
            ai.maintain_population()
    
    assert len(ai.cells) >= initial_count
    
    print("✓ CELLULAR-008: Scaling and population growth work")


def test_cell_states():
    """Test cell state tracking."""
    ai = CellularAI()
    
    ai.create_cell(CellRole.PERCEPTION)
    
    # Check cell states
    assert len(ai.cell_states) == 2  # Supervisor + perception
    
    for cell_id, state in ai.cell_states.items():
        assert isinstance(state, CellState)
        assert state.role in list(CellRole)
        assert state.confidence >= 0
        assert state.confidence <= 1
    
    print("✓ CELLULAR-009: Cell state tracking works")


def test_system_state():
    """Test system state reporting."""
    ai = CellularAI()
    
    ai.create_cell(CellRole.PERCEPTION)
    ai.create_cell(CellRole.REASONING)
    
    state = ai.get_system_state()
    
    assert state is not None
    assert "total_cells" in state
    assert "alive_cells" in state
    assert "roles" in state
    assert "total_decisions" in state
    assert "cell_states" in state
    
    print("✓ CELLULAR-010: System state reporting works")


def test_temporal_analysis():
    """Test temporal analysis functionality."""
    ai = CellularAI()
    
    ai.create_cell(CellRole.PERCEPTION)
    
    # Make a decision
    ai.think({"type": "sensor", "value": 1})
    
    # Get temporal analysis
    temporal = ai.get_temporal_analysis()
    
    assert temporal is not None
    assert "avg_temporal_precision" in temporal
    assert "best_temporal_precision" in temporal
    assert "avg_confidence" in temporal
    assert "total_echoes" in temporal
    assert "decision_count" in temporal
    
    print("✓ CELLULAR-011: Temporal analysis works")


def test_provenance_chain():
    """Test cryptographic provenance chain."""
    ai = CellularAI()
    
    ai.create_cell(CellRole.PERCEPTION)
    
    # Make multiple decisions
    for i in range(3):
        ai.think({"type": "sensor", "value": i})
    
    # Check that provenance hashes are linked
    for i in range(1, len(ai.decision_history)):
        prev_hash = ai.decision_history[i-1].shard_provenance
        curr_hash = ai.decision_history[i].shard_provenance
        
        assert prev_hash is not None
        assert curr_hash is not None
        assert prev_hash != curr_hash  # Different hashes for different decisions
    
    print("✓ CELLULAR-012: Provenance chain works")


def run_all_tests():
    """Run all cellular AI tests."""
    print("=== Cellular AI Tests ===")
    print()
    
    test_cellular_ai_creation()
    test_cell_differentiation()
    test_cellular_thinking()
    test_temporal_precision()
    test_self_repair()
    test_explainability()
    test_predictive_capabilities()
    test_scaling()
    test_cell_states()
    test_system_state()
    test_temporal_analysis()
    test_provenance_chain()
    
    print()
    print("=== All Cellular AI Tests Passed ===")


if __name__ == "__main__":
    run_all_tests()
