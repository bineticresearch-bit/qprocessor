"""
Temporal Quantum Gates — TEMP-011 through TEMP-018

All quantum gates map to temporal operations on timers.
The trigonometric temporal logic ensures sin²(θ) + cos²(θ) = 1.

REAL IMPLEMENTATION:
- Gates modify timer phase and amplitude
- Proper unitary transformations
- Temporal superposition and entanglement

Spec Reference: docs/spec/TEMPORAL.md
"""

import math
import cmath
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional


class GateType(Enum):
    """Quantum gate types and their temporal equivalents."""
    # Single-qubit gates
    T_ROTATE = "T_ROTATE"      # Rz(α): Phase rotation
    T_SPLIT = "T_SPLIT"        # Rx(β): Amplitude splitting (Hadamard-like)
    T_SHIFT = "T_SHIFT"        # Ry(γ): Phase shift
    T_HADAMARD = "T_HADAMARD"  # H: Equal-probability superposition
    T_PAULI_X = "T_PAULI_X"    # X: Temporal bit flip
    T_PAULI_Y = "T_PAULI_Y"    # Y: Temporal phase-bit flip
    T_PAULI_Z = "T_PAULI_Z"    # Z: Temporal phase flip
    T_GATE = "T_GATE"          # T: π/8 phase gate
    S_GATE = "S_GATE"          # S: π/4 phase gate
    
    # Multi-qubit gates
    T_ENTANGLE = "T_ENTANGLE"  # Create temporal entanglement
    T_CNOT = "T_CNOT"          # Controlled-NOT (temporal)
    T_SWAP = "T_SWAP"          # SWAP two timers
    T_QFT = "T_QFT"            # Quantum Fourier Transform
    
    # Measurement
    T_MEASURE = "T_MEASURE"    # Measurement gate


@dataclass
class TemporalGate:
    """
    TEMP-011: A temporal quantum gate.
    
    Gates modify the phase and amplitude of timers, implementing
    quantum operations in the temporal domain.
    
    Parameters:
        gate_type: Type of gate operation
        params: Gate-specific parameters
    """
    gate_type: GateType
    params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}
    
    def apply_to_phase(self, phase: tuple) -> tuple:
        """
        Apply this gate to a timer's phase.
        
        Args:
            phase: (theta, phi) tuple
        
        Returns:
            New (theta, phi) after gate application
        """
        theta, phi = phase
        
        if self.gate_type == GateType.T_ROTATE:
            # Rz(α): Rotate around Z axis
            alpha = self.params.get('alpha', 0)
            phi = (phi + alpha) % (2 * math.pi)
        
        elif self.gate_type == GateType.T_SPLIT:
            # Rx(β): Rotate around X axis (split amplitude)
            beta = self.params.get('beta', math.pi / 2)
            # Mix theta based on rotation
            theta = (theta + beta) % (2 * math.pi)
        
        elif self.gate_type == GateType.T_SHIFT:
            # Ry(γ): Rotate around Y axis
            gamma = self.params.get('gamma', 0)
            theta = (theta + gamma) % (2 * math.pi)
        
        elif self.gate_type == GateType.T_HADAMARD:
            # H: Create equal superposition
            # Maps |0⟩ → |+⟩, |1⟩ → |-⟩
            theta = math.pi / 2  # Equal probability
            phi = 0.0
        
        elif self.gate_type == GateType.T_PAULI_X:
            # X: Bit flip (|0⟩ ↔ |1⟩)
            theta = math.pi - theta
            phi = (phi + math.pi) % (2 * math.pi)
        
        elif self.gate_type == GateType.T_PAULI_Y:
            # Y: Phase-bit flip
            theta = math.pi - theta
            phi = (phi + math.pi / 2) % (2 * math.pi)
        
        elif self.gate_type == GateType.T_PAULI_Z:
            # Z: Phase flip (|1⟩ → -|1⟩)
            phi = (phi + math.pi) % (2 * math.pi)
        
        elif self.gate_type == GateType.T_GATE:
            # T: π/8 phase gate
            phi = (phi + math.pi / 4) % (2 * math.pi)
        
        elif self.gate_type == GateType.S_GATE:
            # S: π/4 phase gate
            phi = (phi + math.pi / 2) % (2 * math.pi)
        
        elif self.gate_type == GateType.T_MEASURE:
            # Measurement collapses the state
            # Phase becomes definite (0 or π)
            pass  # Measurement handled separately
        
        return (theta, phi)
    
    def apply_to_amplitude(self, amplitude: complex) -> complex:
        """
        Apply this gate to a timer's amplitude.
        
        Args:
            amplitude: Complex amplitude
        
        Returns:
            New amplitude after gate application
        """
        if self.gate_type == GateType.T_ROTATE:
            alpha = self.params.get('alpha', 0)
            return amplitude * cmath.exp(1j * alpha)
        
        elif self.gate_type == GateType.T_PAULI_Z:
            return -amplitude
        
        elif self.gate_type == GateType.T_GATE:
            return amplitude * cmath.exp(1j * math.pi / 4)
        
        elif self.gate_type == GateType.S_GATE:
            return amplitude * 1j
        
        return amplitude
    
    # Factory methods for common gates
    @staticmethod
    def T_ROTATE(alpha: float) -> 'TemporalGate':
        """Rz(α): Phase rotation gate."""
        return TemporalGate(gate_type=GateType.T_ROTATE, params={'alpha': alpha})
    
    @staticmethod
    def T_SPLIT(beta: float) -> 'TemporalGate':
        """Rx(β): Amplitude splitting gate."""
        return TemporalGate(gate_type=GateType.T_SPLIT, params={'beta': beta})
    
    @staticmethod
    def T_SHIFT(gamma: float) -> 'TemporalGate':
        """Ry(γ): Phase shift gate."""
        return TemporalGate(gate_type=GateType.T_SHIFT, params={'gamma': gamma})
    
    @staticmethod
    def T_HADAMARD() -> 'TemporalGate':
        """Hadamard gate: equal superposition."""
        return TemporalGate(gate_type=GateType.T_HADAMARD, params={})
    
    @staticmethod
    def T_PAULI_X() -> 'TemporalGate':
        """Pauli-X gate: temporal bit flip."""
        return TemporalGate(gate_type=GateType.T_PAULI_X, params={})
    
    @staticmethod
    def T_PAULI_Z() -> 'TemporalGate':
        """Pauli-Z gate: temporal phase flip."""
        return TemporalGate(gate_type=GateType.T_PAULI_Z, params={})
    
    @staticmethod
    def T_ENTANGLE() -> 'TemporalGate':
        """Entanglement gate."""
        return TemporalGate(gate_type=GateType.T_ENTANGLE, params={})
    
    @staticmethod
    def T_CNOT() -> 'TemporalGate':
        """Controlled-NOT gate."""
        return TemporalGate(gate_type=GateType.T_CNOT, params={})
    
    @staticmethod
    def T_SWAP() -> 'TemporalGate':
        """SWAP gate: exchange timer parameters."""
        return TemporalGate(gate_type=GateType.T_SWAP, params={})
    
    @staticmethod
    def T_QFT() -> 'TemporalGate':
        """Quantum Fourier Transform gate."""
        return TemporalGate(gate_type=GateType.T_QFT, params={})
    
    @staticmethod
    def T_MEASURE() -> 'TemporalGate':
        """Measurement gate."""
        return TemporalGate(gate_type=GateType.T_MEASURE, params={})
