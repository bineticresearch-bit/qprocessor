#!/usr/bin/env python3
"""
Cellular AI Demonstration
==========================

Demonstrates the capabilities of the Cellular AI system built on QProcessor.
"""

import sys
import os
import time
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cellular_ai import CellularAI, CellRole
from src.temporal.echo import EchoCascade


def section(title: str):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_basic_operation():
    """Demo 1: Basic Cellular AI operation."""
    section("DEMO 1: Basic Cellular AI Operation")
    
    # Create cellular AI
    ai = CellularAI()
    
    # Differentiate cells for different roles
    ai.create_cell(CellRole.PERCEPTION)
    ai.create_cell(CellRole.REASONING)
    ai.create_cell(CellRole.MEMORY)
    ai.create_cell(CellRole.ACTION)
    
    print(f"🧬 Population: {len(ai.cells)} cells")
    print(f"📊 Roles: {list(ai.cell_roles.values())}")
    
    # Process some input
    input_data = {"type": "sensor", "value": 42}
    output = ai.think(input_data)
    
    print(f"📊 Output: {output['action']}")
    print(f"⏱️  Temporal precision: {ai.decision_history[0].temporal_precision * 1e12:.3f} ps")
    print(f"📈 Confidence: {ai.decision_history[0].confidence:.3f}")


def demo_temporal_precision():
    """Demo 2: Temporal precision capabilities."""
    section("DEMO 2: Temporal Precision Capabilities")
    
    ai = CellularAI()
    
    # Create perception cell
    ai.create_cell(CellRole.PERCEPTION)
    
    # Process multiple inputs to demonstrate precision
    for i in range(3):
        input_data = {"type": "sensor", "value": i * 10}
        output = ai.think(input_data)
        
        precision = ai.decision_history[-1].temporal_precision
        print(f"  Decision {i}: precision = {precision * 1e12:.3f} ps")
    
    # Get temporal analysis
    temporal = ai.get_temporal_analysis()
    print(f"\n📈 Temporal Analysis:")
    print(f"  Average precision: {temporal['avg_temporal_precision'] * 1e12:.3f} ps")
    print(f"  Best precision: {temporal['best_temporal_precision'] * 1e12:.3f} ps")
    print(f"  Total echoes: {temporal['total_echoes']}")


def demo_self_repair():
    """Demo 3: Self-repair and population maintenance."""
    section("DEMO 3: Self-Repair and Population Maintenance")
    
    ai = CellularAI()
    
    # Create initial population
    ai.create_cell(CellRole.PERCEPTION)
    ai.create_cell(CellRole.REASONING)
    
    print(f"🧬 Initial population: {len(ai.cells)} cells")
    
    # Simulate cell death
    for cell in ai.cells:
        if cell.is_alive():
            cell.apoptosis()
    
    print(f"💀 Simulated cell death")
    print(f"🧬 Alive cells: {len([c for c in ai.cells if c.is_alive()])}")
    
    # Maintain population (self-repair)
    modifications = ai.maintain_population()
    print(f"🔄 Population maintenance: {modifications} modifications")
    print(f"🧬 New population: {len(ai.cells)} cells")
    print(f"🧬 Alive cells: {len([c for c in ai.cells if c.is_alive()])}")


def demo_explainability():
    """Demo 4: Explainability and provenance."""
    section("DEMO 4: Explainability and Provenance")
    
    ai = CellularAI()
    
    # Create cells and make decisions
    ai.create_cell(CellRole.PERCEPTION)
    ai.create_cell(CellRole.REASONING)
    ai.create_cell(CellRole.MEMORY)
    ai.create_cell(CellRole.ACTION)
    
    # Make a decision
    input_data = {"type": "sensor", "value": 42}
    ai.think(input_data)
    
    # Get explanation
    decision_id = ai.decision_history[0].decision_id
    explanation = ai.explain_decision(decision_id)
    
    print(f"🔍 Decision Explanation:")
    print(f"  Decision ID: {explanation['decision_id']}")
    print(f"  Input: {explanation['input']}")
    print(f"  Confidence: {explanation['confidence']:.3f}")
    print(f"  Temporal Precision: {explanation['temporal_precision'] * 1e12:.3f} ps")
    print(f"  Cell Contributions: {list(explanation['cell_contributions'].keys())}")
    print(f"  Provenance Hash: {explanation['provenance_hash'][:16]}...")
    print(f"  Verification: {explanation['verification']}")


def demo_predictive_capabilities():
    """Demo 5: Predictive capabilities using temporal derivatives."""
    section("DEMO 5: Predictive Capabilities")
    
    ai = CellularAI()
    
    # Create reasoning cell
    ai.create_cell(CellRole.REASONING)
    
    # Process some input
    input_data = {"type": "sensor", "value": 42}
    ai.think(input_data)
    
    # Predict future state
    current_state = {"value": 42, "trend": 1}
    predicted_state = ai.predict_future_state(current_state)
    
    print(f"🔮 Current State: {current_state}")
    print(f"🔮 Predicted State: {predicted_state}")
    print(f"📈 Prediction shows {predicted_state['value'] - current_state['value']} unit increase")


def demo_scaling():
    """Demo 6: Scaling and population growth."""
    section("DEMO 6: Scaling and Population Growth")
    
    ai = CellularAI()
    
    # Start with minimal population
    ai.create_cell(CellRole.PERCEPTION)
    
    print(f"🧬 Initial population: {len(ai.cells)} cells")
    
    # Process multiple decisions to trigger growth
    for i in range(5):
        input_data = {"type": "sensor", "value": i}
        ai.think(input_data)
        
        # Maintain population periodically
        if i % 2 == 0:
            ai.maintain_population()
    
    print(f"🧬 Final population: {len(ai.cells)} cells")
    print(f"📊 Roles: {list(ai.cell_roles.values())}")
    print(f"📈 Total decisions: {ai.total_decisions}")


def main():
    """Run all demos."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + "  Cellular AI Demonstration".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    
    demo_basic_operation()
    demo_temporal_precision()
    demo_self_repair()
    demo_explainability()
    demo_predictive_capabilities()
    demo_scaling()
    
    print("\n" + "="*70)
    print("  All demonstrations completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
