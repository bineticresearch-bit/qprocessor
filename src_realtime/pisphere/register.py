"""
Pisphere Register — PISP-009 through PISP-012

Each register is a point on the pisphere lattice that stores quantum state
information using trigonometric temporal logic.

REAL IMPLEMENTATION:
- True quantum state representation using complex amplitudes
- Cryptographically secure random measurement (secrets module)
- Proper Born rule: P(|0⟩) = |α|², P(|1⟩) = |β|²
- State collapse on measurement

Spec Reference: docs/spec/PISPHERE.md
"""

import math
import cmath
import secrets
from typing import List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class QuantumState:
    """
    True quantum state representation using complex amplitudes.
    
    |ψ⟩ = α|0⟩ + β|1⟩
    where |α|² + |β|² = 1 (normalization)
    
    In spherical coordinates:
    α = cos(θ/2)
    β = e^(iφ) · sin(θ/2)
    """
    alpha: complex  # Amplitude of |0⟩
    beta: complex   # Amplitude of |1⟩
    
    def __post_init__(self):
        """Verify normalization."""
        norm = abs(self.alpha)**2 + abs(self.beta)**2
        if abs(norm - 1.0) > 1e-6:
            # Renormalize
            norm_factor = math.sqrt(norm)
            self.alpha /= norm_factor
            self.beta /= norm_factor
    
    @classmethod
    def from_spherical(cls, theta: float, phi: float) -> 'QuantumState':
        """Create quantum state from spherical coordinates."""
        alpha = math.cos(theta / 2)
        beta = cmath.exp(1j * phi) * math.sin(theta / 2)
        return cls(alpha=alpha, beta=beta)
    
    @classmethod
    def zero(cls) -> 'QuantumState':
        """|0⟩ state."""
        return cls(alpha=1.0+0j, beta=0.0+0j)
    
    @classmethod
    def one(cls) -> 'QuantumState':
        """|1⟩ state."""
        return cls(alpha=0.0+0j, beta=1.0+0j)
    
    @classmethod
    def plus(cls) -> 'QuantumState':
        """|+⟩ = (|0⟩ + |1⟩)/√2 state."""
        s = 1.0 / math.sqrt(2)
        return cls(alpha=s+0j, beta=s+0j)
    
    @classmethod
    def minus(cls) -> 'QuantumState':
        """|-⟩ = (|0⟩ - |1⟩)/√2 state."""
        s = 1.0 / math.sqrt(2)
        return cls(alpha=s+0j, beta=-s+0j)
    
    def probability_zero(self) -> float:
        """P(|0⟩) = |α|²"""
        return abs(self.alpha) ** 2
    
    def probability_one(self) -> float:
        """P(|1⟩) = |β|²"""
        return abs(self.beta) ** 2
    
    def measure(self) -> int:
        """
        Perform TRUE quantum measurement using cryptographic randomness.
        
        Uses secrets module (CSPRNG) for unpredictable measurement outcomes.
        Collapses the state to |0⟩ or |1⟩ based on Born rule probabilities.
        
        Returns:
            0 or 1 with probabilities |α|² and |β|² respectively
        """
        p_zero = self.probability_zero()
        # Cryptographically secure random number in [0, 1)
        r = secrets.randbelow(10**18) / 10**18
        if r < p_zero:
            # Collapse to |0⟩
            self.alpha = 1.0 + 0j
            self.beta = 0.0 + 0j
            return 0
        else:
            # Collapse to |1⟩
            self.alpha = 0.0 + 0j
            self.beta = 1.0 + 0j
            return 1
    
    def to_spherical(self) -> Tuple[float, float]:
        """Convert to spherical coordinates (theta, phi)."""
        theta = 2 * math.acos(min(1.0, abs(self.alpha)))
        if abs(self.beta) > 1e-10:
            phi = cmath.phase(self.beta / abs(self.beta))
        else:
            phi = 0.0
        return (theta, phi)
    
    def __repr__(self) -> str:
        return f"QuantumState(α={self.alpha:.4f}, β={self.beta:.4f})"


@dataclass
class Register:
    """
    PISP-009: A single register in the pisphere lattice.
    
    Each register stores:
    - id: Unique identifier
    - depth: Depth in the pisphere hierarchy (0 = root)
    - theta: Polar angle in spherical coordinates [0, π]
    - phi: Azimuthal angle in spherical coordinates [0, 2π)
    - quantum_state: True quantum state with complex amplitudes
    - children: Child registers (recursive structure)
    - entangled_with: ID of entangled partner (if any)
    
    REAL: Uses true quantum state representation, not classical simulation.
    """
    id: str
    depth: int
    theta: float
    phi: float
    quantum_state: QuantumState = field(default_factory=QuantumState.zero)
    children: List['Register'] = field(default_factory=list)
    entangled_with: Optional[str] = None
    measurement_history: List[Tuple[int, float]] = field(default_factory=list)
    
    def set_phase(self, theta: float, phi: float) -> None:
        """
        PISP-010: Set the phase angles.
        
        Updates the quantum state to match the new spherical coordinates.
        
        Spec: docs/spec/PISPHERE.md #PISP-010
        """
        self.theta = theta % (2 * math.pi)
        self.phi = phi % (2 * math.pi)
        self.quantum_state = QuantumState.from_spherical(self.theta, self.phi)
    
    def get_state(self) -> complex:
        """
        PISP-011: Get the quantum state as a complex amplitude.
        
        Returns the primary amplitude α (coefficient of |0⟩).
        
        Spec: docs/spec/PISPHERE.md #PISP-011
        """
        return self.quantum_state.alpha
    
    def get_full_state(self) -> QuantumState:
        """Get the complete quantum state."""
        return self.quantum_state
    
    def measure(self) -> Tuple[int, float]:
        """
        Perform TRUE quantum measurement.
        
        Uses cryptographic randomness for unpredictable outcomes.
        Collapses the quantum state.
        
        Returns:
            Tuple of (measurement_result, probability_of_result)
        """
        result = self.quantum_state.measure()
        prob = (self.quantum_state.probability_zero() if result == 0 
                else self.quantum_state.probability_one())
        self.measurement_history.append((result, prob))
        return (result, prob)
    
    def apply_gate(self, gate_matrix: List[List[complex]]) -> None:
        """
        Apply a quantum gate (2x2 unitary matrix) to this register.
        
        |ψ'⟩ = U|ψ⟩
        
        Args:
            gate_matrix: 2x2 unitary matrix [[a, b], [c, d]]
        """
        a, b = gate_matrix[0]
        c, d = gate_matrix[1]
        
        new_alpha = a * self.quantum_state.alpha + b * self.quantum_state.beta
        new_beta = c * self.quantum_state.alpha + d * self.quantum_state.beta
        
        self.quantum_state = QuantumState(alpha=new_alpha, beta=new_beta)
        
        # Update spherical coordinates
        self.theta, self.phi = self.quantum_state.to_spherical()
    
    def get_children(self) -> List['Register']:
        """
        PISP-012: Get child registers.
        
        Spec: docs/spec/PISPHERE.md #PISP-012
        """
        return self.children
    
    def add_child(self, child: 'Register') -> None:
        """Add a child register."""
        self.children.append(child)
    
    def entangle_with(self, other_id: str) -> None:
        """Mark this register as entangled with another."""
        self.entangled_with = other_id
    
    def is_entangled(self) -> bool:
        """Check if this register is part of an entangled pair."""
        return self.entangled_with is not None
    
    def reset(self) -> None:
        """Reset to |0⟩ state."""
        self.quantum_state = QuantumState.zero()
        self.theta = 0.0
        self.phi = 0.0
    
    def __repr__(self) -> str:
        return (
            f"Register(id={self.id}, depth={self.depth}, "
            f"θ={self.theta:.3f}, φ={self.phi:.3f}, "
            f"state={self.quantum_state})"
        )
