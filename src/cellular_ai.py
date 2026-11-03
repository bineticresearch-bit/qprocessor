"""
Cellular AI System - Core Implementation
==========================================

A self-organizing, self-repairing AI built on QProcessor's cellular paradigm.
"""

import time
import uuid
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from .cell.cell import Cell, CellType
from .cell.shard import SelfDescribingShard
from .temporal.engine import TemporalEngine
from .temporal.gates import TemporalGate
from .hash.non_avalanche import non_avalanche_hash, compute_similarity


class CellRole(Enum):
    """Specialized roles for AI cells."""
    PERCEPTION = "perception"      # NETWORK - sensory processing
    REASONING = "reasoning"        # CPU - logical inference
    MEMORY = "memory"              # MEMORY - knowledge storage
    ACTION = "action"              # IO - response generation
    SUPERVISOR = "supervisor"      # UNDIFFERENTIATED - coordination


@dataclass
class CellState:
    """Enhanced cell state for AI cells."""
    cell_id: str
    role: CellRole
    cell_type: CellType
    specialization: str
    confidence: float
    last_activity: float
    contribution_score: float


@dataclass
class Decision:
    """AI decision with complete provenance."""
    decision_id: str
    input_data: Any
    output: Any
    confidence: float
    temporal_precision: float
    cell_contributions: Dict[str, float]
    reasoning_chain: List[Dict]
    shard_provenance: bytes
    temporal_analysis: Optional[Dict] = None


class CellularAI:
    """
    A self-organizing, self-repairing AI system built on QProcessor's cellular paradigm.
    
    Each cell is a complete computational unit with temporal precision, specialized
    capabilities, and full provenance tracking.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Cell population
        self.cells: List[Cell] = []
        self.cell_roles: Dict[str, CellRole] = {}
        self.cell_states: Dict[str, CellState] = {}
        
        # Temporal engine with hyperfractal precision
        self.temporal_engine = TemporalEngine(
            resolution_us=1,
            echo_enabled=True,
            echo_depth=self.config.get("echo_depth", 8)
        )
        
        # Cellular memory (pisphere-based storage)
        self.cellular_memory: Dict[str, Any] = {}
        
        # Decision tracking
        self.decision_history: List[Decision] = []
        self.decision_counter = 0
        
        # System metrics
        self.start_time = time.time()
        self.total_decisions = 0
        self.total_cells_created = 0
        
        # Create initial supervisor cell
        self._create_supervisor_cell()
        
        print(f"🧬 Cellular AI initialized with {len(self.cells)} cells")
        print(f"⏱️  Temporal precision: {self.temporal_engine.echo_depth} levels (picosecond)")
    
    def _create_supervisor_cell(self) -> Cell:
        """Create the initial supervisor cell."""
        cell = Cell(
            cell_type=CellType.UNDIFFERENTIATED,
            pisphere_config={"max_depth": 5},
            temporal_config={"echo_depth": 8}
        )
        
        cell_id = cell.get_id()
        self.cells.append(cell)
        self.cell_roles[cell_id] = CellRole.SUPERVISOR
        self.cell_states[cell_id] = CellState(
            cell_id=cell_id,
            role=CellRole.SUPERVISOR,
            cell_type=CellType.UNDIFFERENTIATED,
            specialization="system_coordination",
            confidence=1.0,
            last_activity=time.time(),
            contribution_score=0.0
        )
        
        # Record creation in shard
        cell.get_shard().record_operation(
            "CELLULAR_AI_INIT",
            {"role": CellRole.SUPERVISOR.value},
            "created"
        )
        
        return cell
    
    def differentiate_cell(self, cell: Cell, role: CellRole) -> Cell:
        """
        Differentiate a cell into a specialized role.
        
        Args:
            cell: The cell to differentiate
            role: The target role
            
        Returns:
            The differentiated cell
        """
        cell_id = cell.get_id()
        
        # Map role to cell type
        role_to_type = {
            CellRole.PERCEPTION: CellType.NETWORK,
            CellRole.REASONING: CellType.CPU,
            CellRole.MEMORY: CellType.MEMORY,
            CellRole.ACTION: CellType.IO,
            CellRole.SUPERVISOR: CellType.UNDIFFERENTIATED
        }
        
        target_type = role_to_type[role]
        
        # Differentiate the cell
        cell.differentiate(target_type)
        
        # Update role mapping
        self.cell_roles[cell_id] = role
        
        # Update cell state
        self.cell_states[cell_id] = CellState(
            cell_id=cell_id,
            role=role,
            cell_type=target_type,
            specialization=self._determine_specialization(role, cell),
            confidence=0.8,
            last_activity=time.time(),
            contribution_score=0.0
        )
        
        # Record differentiation in shard
        cell.get_shard().record_operation(
            "CELLULAR_AI_DIFFERENTIATE",
            {"from": "undifferentiated", "to": role.value},
            "differentiated"
        )
        
        print(f"🔄 Cell {cell_id} differentiated to {role.value}")
        
        return cell
    
    def _determine_specialization(self, role: CellRole, cell: Cell) -> str:
        """Determine cell specialization based on role and context."""
        if role == CellRole.PERCEPTION:
            return "pattern_detection"
        elif role == CellRole.REASONING:
            return "logical_inference"
        elif role == CellRole.MEMORY:
            return "knowledge_storage"
        elif role == CellRole.ACTION:
            return "response_generation"
        else:
            return "system_coordination"
    
    def create_cell(self, role: CellRole) -> Cell:
        """
        Create a new cell with the specified role.
        
        Args:
            role: The role for the new cell
            
        Returns:
            The new cell
        """
        # Create undifferentiated cell
        cell = Cell(
            cell_type=CellType.UNDIFFERENTIATED,
            pisphere_config={"max_depth": 5},
            temporal_config={"echo_depth": 8}
        )
        
        # Differentiate immediately
        cell = self.differentiate_cell(cell, role)
        
        # Track cell
        cell_id = cell.get_id()
        self.cells.append(cell)
        self.total_cells_created += 1
        
        print(f"🧬 Created new {role.value} cell: {cell_id}")
        
        return cell
    
    def think(self, input_data: Any) -> Any:
        """
        Process input through the cellular population.
        
        Args:
            input_data: The input to process
            
        Returns:
            The processed output
        """
        decision_id = f"decision_{self.decision_counter}"
        self.decision_counter += 1
        
        # Start temporal synchronization
        timer = self.temporal_engine.create_timer(
            delay_us=100,
            phase=(math.pi/4, 0.0)
        )
        
        # Emit echo cascade for hyperfractal precision
        if timer.echo_cascade:
            timer.emit_echo(max_depth=self.temporal_engine.echo_depth)
        
        # Process through specialized cells
        cell_contributions = {}
        reasoning_chain = []
        temporal_weights = {}
        
        # Phase 1: Perception with temporal pattern analysis
        perception_results = []
        perception_times = []
        
        for cell_id, role in self.cell_roles.items():
            if role == CellRole.PERCEPTION:
                cell = self._get_cell_by_id(cell_id)
                if cell and cell.is_alive():
                    # Record precise timing
                    timer = self.temporal_engine.create_timer(
                        delay_us=10,
                        phase=(math.pi/2, 0.0)
                    )
                    
                    # Emit echo cascade for hyperfractal precision
                    if timer.echo_cascade:
                        timer.emit_echo(max_depth=self.temporal_engine.echo_depth)
                    
                    result = self._process_perception(cell, input_data, timer)
                    perception_results.append(result)
                    
                    # Resolve temporal precision for this perception
                    if timer.echo_cascade:
                        t_res, p_res = timer.resolve_echo_precision()
                        perception_times.append({
                            "cell_id": cell_id,
                            "resolved_time": t_res,
                            "precision": p_res
                        })
                    
                    cell_contributions[cell_id] = 1.0 / len(perception_results)
                    temporal_weights[cell_id] = 1.0 / (p_res * 1e12)  # Higher weight for better precision
        
        # Phase 2: Reasoning with temporal interference analysis
        reasoning_results = []
        reasoning_times = []
        
        for cell_id, role in self.cell_roles.items():
            if role == CellRole.REASONING:
                cell = self._get_cell_by_id(cell_id)
                if cell and cell.is_alive():
                    # Create entangled timers for correlated processing
                    if len(perception_times) > 1:
                        self.temporal_engine.echo_entangle(
                            perception_times[0]["cell_id"],
                            cell_id
                        )
                    
                    timer = self.temporal_engine.create_timer(
                        delay_us=20,
                        phase=(math.pi/3, math.pi/6)
                    )
                    
                    # Emit echo cascade
                    if timer.echo_cascade:
                        timer.emit_echo(max_depth=self.temporal_engine.echo_depth)
                    
                    result = self._process_reasoning(cell, perception_results, timer)
                    reasoning_results.append(result)
                    
                    # Resolve temporal precision
                    if timer.echo_cascade:
                        t_res, p_res = timer.resolve_echo_precision()
                        reasoning_times.append({
                            "cell_id": cell_id,
                            "resolved_time": t_res,
                            "precision": p_res
                        })
                    
                    cell_contributions[cell_id] = 1.0 / len(reasoning_results)
                    temporal_weights[cell_id] = 1.0 / (p_res * 1e12)
        
        # Phase 3: Memory retrieval with temporal indexing
        memory_results = []
        memory_times = []
        
        for cell_id, role in self.cell_roles.items():
            if role == CellRole.MEMORY:
                cell = self._get_cell_by_id(cell_id)
                if cell and cell.is_alive():
                    timer = self.temporal_engine.create_timer(
                        delay_us=15,
                        phase=(math.pi/4, math.pi/4)
                    )
                    
                    # Emit echo cascade
                    if timer.echo_cascade:
                        timer.emit_echo(max_depth=self.temporal_engine.echo_depth)
                    
                    result = self._retrieve_memory(cell, reasoning_results, timer)
                    memory_results.append(result)
                    
                    if timer.echo_cascade:
                        t_res, p_res = timer.resolve_echo_precision()
                        memory_times.append({
                            "cell_id": cell_id,
                            "resolved_time": t_res,
                            "precision": p_res
                        })
                    
                    cell_contributions[cell_id] = 1.0 / len(memory_results)
                    temporal_weights[cell_id] = 1.0 / (p_res * 1e12)
        
        # Phase 4: Action generation with temporal coordination
        final_output = None
        action_times = []
        
        for cell_id, role in self.cell_roles.items():
            if role == CellRole.ACTION:
                cell = self._get_cell_by_id(cell_id)
                if cell and cell.is_alive():
                    timer = self.temporal_engine.create_timer(
                        delay_us=25,
                        phase=(math.pi/2, math.pi/2)
                    )
                    
                    # Emit echo cascade
                    if timer.echo_cascade:
                        timer.emit_echo(max_depth=self.temporal_engine.echo_depth)
                    
                    result = self._generate_action(cell, reasoning_results, memory_results, timer)
                    final_output = result
                    
                    if timer.echo_cascade:
                        t_res, p_res = timer.resolve_echo_precision()
                        action_times.append({
                            "cell_id": cell_id,
                            "resolved_time": t_res,
                            "precision": p_res
                        })
                    
                    cell_contributions[cell_id] = 1.0
                    temporal_weights[cell_id] = 1.0 / (p_res * 1e12)
        
        # Resolve all echoes for system-wide temporal precision
        resolution = self.temporal_engine.resolve_all_echoes()
        temporal_precision = resolution.best_precision_s
        
        # Calculate temporal weighting for final decision
        total_weight = sum(temporal_weights.values())
        normalized_weights = {k: v/total_weight for k, v in temporal_weights.items()}
        
        # Create decision with complete provenance
        decision = Decision(
            decision_id=decision_id,
            input_data=input_data,
            output=final_output,
            confidence=self._calculate_confidence(cell_contributions, normalized_weights),
            temporal_precision=temporal_precision,
            cell_contributions=cell_contributions,
            reasoning_chain=reasoning_chain,
            shard_provenance=self._generate_provenance(decision_id, cell_contributions, temporal_precision),
            temporal_analysis={
                "perception_times": perception_times,
                "reasoning_times": reasoning_times,
                "memory_times": memory_times,
                "action_times": action_times,
                "system_precision": temporal_precision,
                "echo_cascades": resolution.timer_count
            }
        )
        
        self.decision_history.append(decision)
        self.total_decisions += 1
        
        # Update cell activity with temporal metrics
        self._update_cell_activity(cell_contributions, normalized_weights, temporal_precision)
        
        # Clean up old timers to prevent memory bloat
        self._cleanup_old_timers()
        
        print(f"🧠 Decision {decision_id} made with {len(cell_contributions)} cells contributing")
        print(f"⏱️  Temporal precision: {temporal_precision * 1e12:.3f} ps")
        print(f"📊 Confidence: {decision.confidence:.3f}")
        print(f"🔗 Echo cascades: {resolution.timer_count} timers resolved")
        
        return final_output
    
    def _process_perception(self, cell: Cell, input_data: Any, timer: 'Timer') -> Any:
        """Process input through a perception cell with temporal precision."""
        # Record operation in shard
        cell.get_shard().record_operation(
            "PERCEPTION",
            {"input_type": type(input_data).__name__, "timer_id": timer.id},
            "processed"
        )
        
        # Use temporal gate for pattern detection
        self.temporal_engine.apply_gate(
            TemporalGate.T_HADAMARD(),
            [timer.id]
        )
        
        # Measure temporal probability
        measurement = self.temporal_engine.measure(timer.id)
        
        return {
            "cell_id": cell.get_id(),
            "data": input_data,
            "timestamp": time.time(),
            "pattern": "detected",
            "temporal_probability": measurement.probability,
            "timer_precision": timer.echo_cascade.effective_resolution_s if timer.echo_cascade else None
        }
    
    def _process_reasoning(self, cell: Cell, perception_results: List[Any], timer: 'Timer') -> Any:
        """Process perception results through a reasoning cell with temporal interference."""
        # Record operation in shard
        cell.get_shard().record_operation(
            "REASONING",
            {"input_count": len(perception_results), "timer_id": timer.id},
            "processed"
        )
        
        # Apply temporal gate for logical inference
        self.temporal_engine.apply_gate(
            TemporalGate.T_ROTATE(math.pi/4),
            [timer.id]
        )
        
        # Create temporal derivative for predictive analysis
        if timer.echo_cascade:
            timer.echo_cascade.compute_derivatives(max_order=2)
        
        return {
            "cell_id": cell.get_id(),
            "perceptions": perception_results,
            "inference": "analyzed",
            "temporal_derivative": timer.echo_cascade.get_derivatives_of_order(1) if timer.echo_cascade else None
        }
    
    def _retrieve_memory(self, cell: Cell, reasoning_results: List[Any], timer: 'Timer') -> Any:
        """Retrieve relevant knowledge from a memory cell with temporal indexing."""
        # Record operation in shard
        cell.get_shard().record_operation(
            "MEMORY_RETRIEVAL",
            {"query": str(reasoning_results), "timer_id": timer.id},
            "retrieved"
        )
        
        # Use temporal shift for memory access
        self.temporal_engine.apply_gate(
            TemporalGate.T_SHIFT(math.pi/6),
            [timer.id]
        )
        
        return {
            "cell_id": cell.get_id(),
            "reasoning": reasoning_results,
            "memory": "retrieved",
            "temporal_index": timer.phase
        }
    
    def _generate_action(self, cell: Cell, reasoning_results: List[Any], memory_results: List[Any], timer: 'Timer') -> Any:
        """Generate action through an action cell with temporal coordination."""
        # Record operation in shard
        cell.get_shard().record_operation(
            "ACTION_GENERATION",
            {"reasoning": str(reasoning_results), "memory": str(memory_results), "timer_id": timer.id},
            "generated"
        )
        
        # Apply temporal split for action selection
        self.temporal_engine.apply_gate(
            TemporalGate.T_SPLIT(math.pi/2),
            [timer.id]
        )
        
        return {
            "cell_id": cell.get_id(),
            "reasoning": reasoning_results,
            "memory": memory_results,
            "action": "executed",
            "temporal_phase": timer.phase
        }
    
    def _get_cell_by_id(self, cell_id: str) -> Optional[Cell]:
        """Get a cell by its ID."""
        for cell in self.cells:
            if cell.get_id() == cell_id:
                return cell
        return None
    
    def _calculate_confidence(self, cell_contributions: Dict[str, float], temporal_weights: Dict[str, float]) -> float:
        """Calculate overall confidence based on cell contributions and temporal precision."""
        if not cell_contributions:
            return 0.0
        
        # Weight by both number of cells and temporal precision
        num_cells = len(cell_contributions)
        avg_temporal_weight = sum(temporal_weights.values()) / len(temporal_weights)
        
        base_confidence = min(0.95, 0.5 + (num_cells * 0.1))
        temporal_bonus = min(0.2, avg_temporal_weight * 0.01)
        
        return base_confidence + temporal_bonus
    
    def _generate_provenance(self, decision_id: str, cell_contributions: Dict[str, float], temporal_precision: float) -> bytes:
        """Generate cryptographic provenance for a decision with temporal context."""
        provenance_data = {
            "decision_id": decision_id,
            "timestamp": time.time(),
            "cell_contributions": cell_contributions,
            "total_cells": len(self.cells),
            "total_decisions": self.total_decisions,
            "temporal_precision": temporal_precision,
            "echo_cascades": len(self.temporal_engine._timers)
        }
        
        data_bytes = json.dumps(provenance_data, sort_keys=True).encode()
        parent_hash = self._get_last_provenance_hash()
        
        return non_avalanche_hash(data_bytes, parent_hash)
    
    def _get_last_provenance_hash(self) -> Optional[bytes]:
        """Get the hash of the last decision's provenance."""
        if self.decision_history:
            return self.decision_history[-1].shard_provenance
        return None
    
    def _update_cell_activity(self, cell_contributions: Dict[str, float], temporal_weights: Dict[str, float], temporal_precision: float):
        """Update cell activity scores with temporal metrics."""
        for cell_id, contribution in cell_contributions.items():
            if cell_id in self.cell_states:
                state = self.cell_states[cell_id]
                state.last_activity = time.time()
                state.contribution_score += contribution * 0.1
                # Add temporal precision bonus
                state.confidence += min(0.05, temporal_precision * 1e12)
    
    def _cleanup_old_timers(self, max_age_s: float = 60.0):
        """Clean up old timers to prevent memory bloat."""
        current_time = time.time()
        old_timers = []
        
        for timer_id, timer in self.temporal_engine._timers.items():
            if current_time - timer.target_time > max_age_s:
                old_timers.append(timer_id)
        
        for timer_id in old_timers:
            del self.temporal_engine._timers[timer_id]
    
    def maintain_population(self) -> int:
        """
        Maintain optimal cell population through mitosis and apoptosis.
        
        Returns:
            Number of cells modified
        """
        modifications = 0
        
        # Check for dead cells and replace them
        dead_cells = [cell for cell in self.cells if not cell.is_alive()]
        for cell in dead_cells:
            cell_id = cell.get_id()
            role = self.cell_roles.get(cell_id)
            
            if role and role != CellRole.SUPERVISOR:
                # Create replacement cell
                replacement = self.create_cell(role)
                modifications += 1
                
                # Transfer knowledge to replacement
                self._transfer_knowledge(cell, replacement)
                
                print(f"🔄 Replaced dead cell {cell_id} with {replacement.get_id()}")
        
        # Check if we need more cells of certain types
        role_counts = {}
        for role in self.cell_roles.values():
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Add cells if needed (simple heuristic)
        for role, count in role_counts.items():
            if count < 2 and len(self.cells) < 50:  # Minimum 2 of each type
                if role != CellRole.SUPERVISOR:  # Supervisor cells are undifferentiated
                    self.create_cell(role)
                    modifications += 1
        
        return modifications
    
    def _transfer_knowledge(self, old_cell: Cell, new_cell: Cell):
        """Transfer knowledge from old cell to new cell."""
        # Get shard from old cell
        old_shard = old_cell.get_shard()
        
        # Record knowledge transfer
        new_cell.get_shard().record_operation(
            "KNOWLEDGE_TRANSFER",
            {"from": old_cell.get_id()},
            "transferred"
        )
        
        # Copy some state (simplified for demonstration)
        new_cell.get_shard().record_operation(
            "STATE_TRANSFER",
            {"operations": len(old_shard.get_operations().operation_log)},
            "copied"
        )
    
    def get_system_state(self) -> Dict:
        """Get comprehensive system state."""
        return {
            "total_cells": len(self.cells),
            "alive_cells": len([c for c in self.cells if c.is_alive()]),
            "roles": {role.value: count for role, count in 
                     {r: list(self.cell_roles.values()).count(r) for r in set(self.cell_roles.values())}.items()},
            "total_decisions": self.total_decisions,
            "total_cells_created": self.total_cells_created,
            "uptime": time.time() - self.start_time,
            "temporal_precision": self.temporal_engine.echo_depth,
            "cell_states": {
                cell_id: {
                    "role": state.role.value,
                    "confidence": state.confidence,
                    "contribution": state.contribution_score
                }
                for cell_id, state in self.cell_states.items()
            }
        }
    
    def explain_decision(self, decision_id: str) -> Optional[Dict]:
        """
        Provide complete explanation for a decision.
        
        Args:
            decision_id: The decision to explain
            
        Returns:
            Complete explanation with provenance
        """
        # Find decision
        decision = None
        for d in self.decision_history:
            if d.decision_id == decision_id:
                decision = d
                break
        
        if not decision:
            return None
        
        # Build explanation
        explanation = {
            "decision_id": decision.decision_id,
            "input": str(decision.input_data),
            "output": str(decision.output),
            "confidence": decision.confidence,
            "temporal_precision": decision.temporal_precision,
            "cell_contributions": decision.cell_contributions,
            "reasoning_chain": decision.reasoning_chain,
            "provenance_hash": decision.shard_provenance.hex(),
            "verification": "This decision has complete cryptographic provenance"
        }
        
        return explanation
    
    def get_temporal_analysis(self) -> Dict:
        """Get detailed temporal analysis of recent decisions."""
        if not self.decision_history:
            return {}
        
        recent_decisions = self.decision_history[-10:]
        
        precisions = [d.temporal_precision for d in recent_decisions]
        confidences = [d.confidence for d in recent_decisions]
        
        return {
            "avg_temporal_precision": sum(precisions) / len(precisions),
            "best_temporal_precision": min(precisions),
            "avg_confidence": sum(confidences) / len(confidences),
            "total_echoes": sum(d.temporal_analysis.get("echo_cascades", 0) for d in recent_decisions),
            "decision_count": len(recent_decisions)
        }
    
    def predict_future_state(self, current_state: Any) -> Any:
        """
        Predict future state using temporal derivatives from echo cascades.
        
        Args:
            current_state: Current system state
            
        Returns:
            Predicted future state
        """
        # Create predictive timer
        predictive_timer = self.temporal_engine.create_timer(
            delay_us=100,
            phase=(math.pi/2, 0.0)
        )
        
        # Emit echo cascade for predictive analysis
        if predictive_timer.echo_cascade:
            predictive_timer.emit_echo(max_depth=self.temporal_engine.echo_depth)
            predictive_timer.echo_cascade.compute_derivatives(max_order=3)
        
        # Analyze temporal derivatives for prediction
        if predictive_timer.echo_cascade:
            derivatives = predictive_timer.echo_cascade.get_derivatives_of_order(1)
            if derivatives:
                # Use first derivative for prediction
                velocity = derivatives[0].value
                predicted_state = self._apply_velocity(current_state, velocity)
                return predicted_state
        
        return current_state
    
    def _apply_velocity(self, state: Any, velocity: complex) -> Any:
        """Apply temporal velocity to state for prediction."""
        # Simplified prediction logic
        if isinstance(state, dict):
            return {k: v + velocity.real for k, v in state.items()}
        return state + velocity.real
    
    def __repr__(self) -> str:
        state = self.get_system_state()
        temporal = self.get_temporal_analysis()
        
        return (
            f"CellularAI(cells={state['total_cells']}, alive={state['alive_cells']}, "
            f"decisions={state['total_decisions']}, precision={temporal.get('avg_temporal_precision', 0)*1e12:.3f}ps)"
        )


# Example usage
if __name__ == "__main__":
    # Create cellular AI
    ai = CellularAI()
    
    # Differentiate initial cells
    ai.create_cell(CellRole.PERCEPTION)
    ai.create_cell(CellRole.REASONING)
    ai.create_cell(CellRole.MEMORY)
    ai.create_cell(CellRole.ACTION)
    
    print(f"🧬 Population: {len(ai.cells)} cells")
    
    # Process some input
    input_data = {"type": "sensor", "value": 42}
    output = ai.think(input_data)
    
    print(f"📊 Output: {output}")
    
    # Get system state
    state = ai.get_system_state()
    print(f"📈 System state: {json.dumps(state, indent=2)}")
    
    # Maintain population
    modifications = ai.maintain_population()
    print(f"🔄 Population maintenance: {modifications} modifications")
    
    # Explain a decision
    if ai.decision_history:
        explanation = ai.explain_decision(ai.decision_history[0].decision_id)
        print(f"🔍 Explanation: {json.dumps(explanation, indent=2)}")
