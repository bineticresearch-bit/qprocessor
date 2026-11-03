"""
Pisphere Register — PISP-009 through PISP-012

Each register is a point on the pisphere lattice that stores quantum state
information using trigonometric temporal logic.

Spec Reference: docs/spec/PISP.md
"""

import math
import cmath
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class Register:
    """
    PISP-009: A single register in the pisphere lattice.
    
    Each register stores:
    - id: Unique identifier
    - depth: Depth in the pisphere hierarchy (0 = root)
    - theta: Polar angle in spherical coordinates [0, π]
    - phi: Azimuthal angle in spherical coordinates [0, 2π)
    - value: Current quantum state value (complex amplitude)
    - phase: Current phase (θ, φ) as tuple
    
    Spec: docs/spec/PISPHERE.md #PISP-009
    """
    id: str
    depth: int
    theta: float  # Polar angle [0, π]
    phi: float    # Azimuthal angle [0, 2π)
    value: complex = complex(1.0, 0.0)
    phase: tuple = (0.0, 0.0)  # (theta_phase, phi_phase)
    children: List['Register'] = field(default_factory=list)
    parent: Optional['Register'] = None
    
    def set_phase(self, theta: float, phi: float) -> None:
        """
        PISP-010: Set the phase of this register.
        
        Parameters:
            theta: Polar phase angle [0, π]
            phi: Azimuthal phase angle [0, 2π)
        
        Spec: docs/spec/PISPHERE.md #PISP-010
        
        Test Cases:
            - TC1: Valid angles → phase updated
            - TC2: theta out of range → clamp to [0, π]
            - TC3: phi out of range → wrap to [0, 2π)
        """
        # Clamp theta to [0, π]
        self.phase = (
            max(0.0, min(math.pi, theta)),
            phi % (2 * math.pi)
        )
        
        # Update value based on phase
        self.value = self.get_state()
    
    def get_state(self) -> complex:
        """
        PISP-011: Get the current quantum state of this register.
        
        Returns the complex amplitude: cos(θ/2) + e^(iφ) · sin(θ/2)
        
        Returns:
            Complex amplitude representing the quantum state
        
        Spec: docs/spec/PISPHERE.md #PISP-011
        
        Test Cases:
            - TC1: Default state → 1.0 + 0j
            - TC2: After phase change → correct amplitude
            - TC3: |state|² = 1 (normalization)
        """
        theta_phase, phi_phase = self.phase
        
        # Trigonometric temporal logic:
        # |ψ⟩ = cos(θ/2)|0⟩ + e^(iφ) · sin(θ/2)|1⟩
        cos_component = math.cos(theta_phase / 2)
        sin_component = math.sin(theta_phase / 2)
        phase_factor = cmath.exp(1j * phi_phase)
        
        return complex(cos_component + phase_factor * sin_component)
    
    def get_children(self) -> List['Register']:
        """
        PISP-012: Get child registers.
        
        Returns:
            List of child Register objects
        
        Spec: docs/spec/PISPHERE.md #PISP-012
        
        Test Cases:
            - TC1: Leaf node → empty list
            - TC2: Internal node → list of children
        """
        return self.children
    
    def add_child(self, child: 'Register') -> None:
        """Add a child register."""
        child.parent = self
        self.children.append(child)
    
    def get_probability_0(self) -> float:
        """Get probability of measuring |0⟩: cos²(θ/2)."""
        theta_phase, _ = self.phase
        return math.cos(theta_phase / 2) ** 2
    
    def get_probability_1(self) -> float:
        """Get probability of measuring |1⟩: sin²(θ/2)."""
        theta_phase, _ = self.phase
        return math.sin(theta_phase / 2) ** 2
    
    def __repr__(self) -> str:
        return (
            f"Register(id={self.id}, depth={self.depth}, "
            f"θ={self.theta:.3f}, φ={self.phi:.3f}, "
            f"state={self.get_state():.3f})"
        )
