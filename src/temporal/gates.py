"""
Temporal Quantum Gates — TEMP-011 through TEMP-018

All quantum gates map to temporal operations on timers.
The trigonometric temporal logic ensures sin²(θ) + cos²(θ) = 1.

Spec Reference: docs/spec/TEMPORAL.md
"""

import math
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple


class GateType(Enum):
    """Quantum gate types and their temporal equivalents."""
    # Single-qubit gates
    T_ROTATE = "T_ROTATE"      # Rz(α): Phase rotation
    T_SPLIT = "T_SPLIT"        # Rx(β): Amplitude splitting (Hadamard-like)
    T_SHIFT = "T_SHIFT"        # Ry(γ): Phase shift
    T_HADAMARD = "T_HADAMARD"  # H: Equal-probability temporal branch
    T_X = "T_X"                # X: Swap time windows
    T_Y = "T_Y"                # Y: Swap + phase flip π
    T_Z = "T_Z"                # Z: Apply π phase to t₁
    T_S = "T_S"                # S: Apply π/2 phase to t₁
    T_T = "T_T"                # T: Apply π/4 phase to t₁
    
    # Multi-qubit gates
    T_CNOT = "T_CNOT"          # CNOT: Conditional delay
    T_CZ = "T_CZ"              # CZ: Conditional phase
    T_SWAP = "T_SWAP"          # SWAP: Exchange timer parameters
    
    # Meta gates
    T_ENTANGLE = "T_ENTANGLE"  # Create Bell-like pair
    T_QFT = "T_QFT"            # Quantum Fourier Transform
    T_MEASURE = "T_MEASURE"    # Measurement


@dataclass
class TemporalGate:
    """
    TEMP-011: A temporal quantum gate.
    
    Each gate is defined by its type and parameters. When applied to timers,
    the gate modifies their phase, amplitude, or branching structure.
    
    Parameters:
        gate_type: Type of gate (GateType enum)
        params: Gate-specific parameters
    
    Spec: docs/spec/TEMPORAL.md #TEMP-011
    """
    gate_type: GateType
    params: Dict[str, Any]
    
    @staticmethod
    def T_ROTATE(alpha: float) -> 'TemporalGate':
        """
        TEMP-012: Phase rotation gate Rz(α).
        
        Rotates the phase of a timer by angle α.
        
        Parameters:
            alpha: Rotation angle in radians
        
        Returns:
            TemporalGate configured for Rz rotation
        
        Spec: docs/spec/TEMPORAL.md #TEMP-012
        
        Test Cases:
            - TC1: T_ROTATE(0) → no change
            - TC2: T_ROTATE(π) → phase flip
            - TC3: T_ROTATE(2π) → full rotation (identity)
        """
        return TemporalGate(
            gate_type=GateType.T_ROTATE,
            params={"alpha": alpha}
        )
    
    @staticmethod
    def T_SPLIT(beta: float) -> 'TemporalGate':
        """
        TEMP-013: Temporal beam splitter gate.
        
        Splits a timer into two branches with probabilities
        determined by angle β.
        
        Parameters:
            beta: Split angle in radians
        
        Returns:
            TemporalGate configured for splitting
        
        Spec: docs/spec/TEMPORAL.md #TEMP-013
        
        Test Cases:
            - TC1: T_SPLIT(π/2) → equal split (Hadamard-like)
            - TC2: T_SPLIT(0) → no split (all to |0⟩)
            - TC3: T_SPLIT(π) → no split (all to |1⟩)
        """
        return TemporalGate(
            gate_type=GateType.T_SPLIT,
            params={"beta": beta}
        )
    
    @staticmethod
    def T_SHIFT(gamma: float) -> 'TemporalGate':
        """
        TEMP-014: Phase shift gate Ry(γ).
        
        Shifts the azimuthal phase of a timer by angle γ.
        
        Parameters:
            gamma: Phase shift angle in radians
        
        Returns:
            TemporalGate configured for phase shift
        
        Spec: docs/spec/TEMPORAL.md #TEMP-014
        """
        return TemporalGate(
            gate_type=GateType.T_SHIFT,
            params={"gamma": gamma}
        )
    
    @staticmethod
    def T_ENTANGLE() -> 'TemporalGate':
        """
        TEMP-015: Entanglement gate.
        
        Creates a Bell-like temporal signature pair between two timers.
        
        Returns:
            TemporalGate configured for entanglement
        
        Spec: docs/spec/TEMPORAL.md #TEMP-015
        """
        return TemporalGate(
            gate_type=GateType.T_ENTANGLE,
            params={}
        )
    
    @staticmethod
    def T_CNOT() -> 'TemporalGate':
        """
        TEMP-016: Controlled-NOT gate.
        
        The control timer determines whether the target timer
        receives an additional delay (X rotation).
        
        Returns:
            TemporalGate configured for CNOT
        
        Spec: docs/spec/TEMPORAL.md #TEMP-016
        
        Test Cases:
            - TC1: Control=|0⟩ → target unchanged
            - TC2: Control=|1⟩ → target flipped
        """
        return TemporalGate(
            gate_type=GateType.T_CNOT,
            params={}
        )
    
    @staticmethod
    def T_HADAMARD() -> 'TemporalGate':
        """
        TEMP-017: Hadamard gate.
        
        Creates an equal-probability temporal branch.
        Equivalent to T_SPLIT(π/2).
        
        Returns:
            TemporalGate configured for Hadamard
        
        Spec: docs/spec/TEMPORAL.md #TEMP-017
        """
        return TemporalGate(
            gate_type=GateType.T_HADAMARD,
            params={}
        )
    
    @staticmethod
    def T_QFT() -> 'TemporalGate':
        """
        TEMP-018: Quantum Fourier Transform gate.
        
        Performs frequency harmonic analysis on all timers.
        
        Returns:
            TemporalGate configured for QFT
        
        Spec: docs/spec/TEMPORAL.md #TEMP-018
        """
        return TemporalGate(
            gate_type=GateType.T_QFT,
            params={}
        )
    
    @staticmethod
    def T_X() -> 'TemporalGate':
        """Pauli-X (NOT) gate: swap t₀ and t₁ time windows."""
        return TemporalGate(gate_type=GateType.T_X, params={})
    
    @staticmethod
    def T_Y() -> 'TemporalGate':
        """Pauli-Y gate: swap time windows + phase flip π."""
        return TemporalGate(gate_type=GateType.T_Y, params={})
    
    @staticmethod
    def T_Z() -> 'TemporalGate':
        """Pauli-Z gate: apply π phase to t₁."""
        return TemporalGate(gate_type=GateType.T_Z, params={})
    
    @staticmethod
    def T_S() -> 'TemporalGate':
        """S gate: apply π/2 phase to t₁."""
        return TemporalGate(gate_type=GateType.T_S, params={})
    
    @staticmethod
    def T_T() -> 'TemporalGate':
        """T gate: apply π/4 phase to t₁."""
        return TemporalGate(gate_type=GateType.T_T, params={})
    
    @staticmethod
    def T_CZ() -> 'TemporalGate':
        """Controlled-Z gate: conditional phase."""
        return TemporalGate(gate_type=GateType.T_CZ, params={})
    
    @staticmethod
    def T_SWAP() -> 'TemporalGate':
        """SWAP gate: exchange timer parameters."""
        return TemporalGate(gate_type=GateType.T_SWAP, params={})
    
    @staticmethod
    def T_MEASURE() -> 'TemporalGate':
        """Measurement gate."""
        return TemporalGate(gate_type=GateType.T_MEASURE, params={})
    
    def apply_to_phase(self, phase: Tuple[float, float]) -> Tuple[float, float]:
        """
        TEMP-011: Apply the gate to a timer phase.
        
        Parameters:
            phase: Current phase tuple (theta, phi)
            
        Returns:
            New phase tuple after applying gate
        """
        theta, phi = phase
        
        if self.gate_type == GateType.T_ROTATE:
            alpha = self.params.get("alpha", 0.0)
            return (theta + alpha, phi)
        elif self.gate_type == GateType.T_SPLIT:
            beta = self.params.get("beta", 0.0)
            return (theta, phi + beta)
        elif self.gate_type == GateType.T_SHIFT:
            gamma = self.params.get("gamma", 0.0)
            return (theta + gamma, phi)
        elif self.gate_type == GateType.T_HADAMARD:
            # Equal probability split
            return (math.pi/2, phi)
        elif self.gate_type == GateType.T_ENTANGLE:
            # Create entanglement
            return (theta, phi + math.pi/4)
        elif self.gate_type == GateType.T_CNOT:
            # Conditional phase
            return (theta, phi + math.pi)
        elif self.gate_type == GateType.T_SWAP:
            # Swap phases
            return (phi, theta)
        else:
            # Default: no change
            return (theta, phi)
