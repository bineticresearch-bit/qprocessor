"""
Pisphere Register Lattice — PISP-001 through PISP-008

The pisphere is a recursive spherical register architecture where each
register is itself a complete sphere containing smaller spheres at every
surface point.

Spec Reference: docs/spec/PISPHERE.md
"""

import math
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

from .register import Register
from ..hash.non_avalanche import non_avalanche_hash, hash_with_position


@dataclass
class MeasurementResult:
    """Result of a register measurement."""
    register_id: str
    value: int  # 0 or 1
    probability: float
    actual_phase: tuple


@dataclass
class BellPair:
    """A Bell-like temporal signature pair."""
    reg_a: str
    reg_b: str
    bell_type: str  # "PHI_PLUS", "PHI_MINUS", "PSI_PLUS", "PSI_MINUS"
    correlation: float


class Pisphere:
    """
    PISP-001: The Pisphere Register Lattice.
    
    A recursive spherical architecture where each register is itself a
    complete sphere (pisphere) containing smaller spheres at every surface point.
    
    Parameters:
        base_radius: Base radius of the sphere (default: 1.0)
        max_depth: Maximum recursion depth (default: 10)
        branching_factor: Number of children per register (default: 4)
    
    Spec: docs/spec/PISPHERE.md #PISP-001
    
    Key Properties:
        - Depth D has (B^(D+1) - 1) / (B - 1) total registers
        - Default: B=4, depth=10 → 1,398,101 registers
        - Each register stores quantum state as trigonometric temporal logic
    """
    
    def __init__(
        self,
        base_radius: float = 1.0,
        max_depth: int = 10,
        branching_factor: int = 4
    ):
        self.base_radius = base_radius
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        
        # Register storage
        self._registers: Dict[str, Register] = {}
        
        # Create root register
        self._root = self._create_root()
    
    def _create_root(self) -> Register:
        """Create the root register at depth 0."""
        root = Register(
            id="root",
            depth=0,
            theta=0.0,
            phi=0.0
        )
        self._registers["root"] = root
        
        # Recursively create children up to max_depth
        self._create_children(root, depth=0)
        
        return root
    
    def _create_children(self, parent: Register, depth: int) -> None:
        """Recursively create child registers."""
        if depth >= self.max_depth:
            return
        
        for i in range(self.branching_factor):
            # Distribute children on sphere surface using Fibonacci spiral
            theta, phi = self._fibonacci_point(i, self.branching_factor)
            
            child_id = f"{parent.id}_d{depth+1}_c{i}"
            child = Register(
                id=child_id,
                depth=depth + 1,
                theta=theta,
                phi=phi
            )
            
            parent.add_child(child)
            self._registers[child_id] = child
            
            # Recurse
            self._create_children(child, depth + 1)
    
    def _fibonacci_point(self, index: int, total: int) -> Tuple[float, float]:
        """
        Compute a point on a sphere using Fibonacci spiral distribution.
        
        Returns (theta, phi) in spherical coordinates.
        """
        # Golden angle
        golden_angle = math.pi * (3 - math.sqrt(5))
        
        # Theta: polar angle [0, π]
        theta = math.acos(1 - 2 * (index + 0.5) / total)
        
        # Phi: azimuthal angle [0, 2π)
        phi = (golden_angle * index) % (2 * math.pi)
        
        return theta, phi
    
    def create_register(self, depth: int, theta: float, phi: float) -> Register:
        """
        PISP-002: Create a register at specific coordinates.
        
        Parameters:
            depth: Depth in the hierarchy
            theta: Polar angle [0, π]
            phi: Azimuthal angle [0, 2π)
        
        Returns:
            The created Register
        
        Spec: docs/spec/PISPHERE.md #PISP-002
        """
        # Find closest existing register or create new one
        reg_id = f"custom_d{depth}_t{theta:.4f}_p{phi:.4f}"
        
        if reg_id in self._registers:
            return self._registers[reg_id]
        
        register = Register(
            id=reg_id,
            depth=depth,
            theta=theta,
            phi=phi
        )
        self._registers[reg_id] = register
        return register
    
    def get_register(self, depth: int, theta: float, phi: float) -> Register:
        """
        PISP-003: Get a register at specific coordinates.
        
        Parameters:
            depth: Depth in the hierarchy
            theta: Polar angle [0, π]
            phi: Azimuthal angle [0, 2π)
        
        Returns:
            The Register at those coordinates
        
        Spec: docs/spec/PISPHERE.md #PISP-003
        """
        # Find closest register
        best_match = None
        best_distance = float('inf')
        
        for reg in self._registers.values():
            if reg.depth == depth:
                # Spherical distance
                d_theta = abs(reg.theta - theta)
                d_phi = abs(reg.phi - phi)
                distance = math.sqrt(d_theta**2 + d_phi**2)
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = reg
        
        return best_match
    
    def get_all_registers(self, depth: Optional[int] = None) -> List[Register]:
        """
        PISP-004: Get all registers, optionally filtered by depth.
        
        Parameters:
            depth: Optional depth filter
        
        Returns:
            List of Register objects
        
        Spec: docs/spec/PISPHERE.md #PISP-004
        """
        if depth is None:
            return list(self._registers.values())
        return [r for r in self._registers.values() if r.depth == depth]
    
    def count_registers(self, depth: Optional[int] = None) -> int:
        """
        PISP-005: Count registers, optionally at a specific depth.
        
        Parameters:
            depth: Optional depth filter
        
        Returns:
            Number of registers
        
        Spec: docs/spec/PISPHERE.md #PISP-005
        
        Expected:
            Total = (B^(D+1) - 1) / (B - 1) where B=branching_factor, D=max_depth
        """
        if depth is None:
            return len(self._registers)
        return len([r for r in self._registers.values() if r.depth == depth])
    
    def apply_gate(self, register_id: str, gate_type: str, params: dict) -> None:
        """
        PISP-006: Apply a quantum gate to a register.
        
        Parameters:
            register_id: ID of the target register
            gate_type: Type of gate (e.g., "H", "X", "T", "RZ")
            params: Gate parameters
        
        Spec: docs/spec/PISPHERE.md #PISP-006
        """
        if register_id not in self._registers:
            raise ValueError(f"Register {register_id} not found")
        
        register = self._registers[register_id]
        theta_phase, phi_phase = register.phase
        
        if gate_type == "H":  # Hadamard
            # H|0⟩ = (|0⟩ + |1⟩)/√2 → θ = π/2
            register.set_phase(math.pi / 2, phi_phase)
        
        elif gate_type == "X":  # Pauli-X (NOT)
            # X|0⟩ = |1⟩ → θ → π - θ
            register.set_phase(math.pi - theta_phase, phi_phase)
        
        elif gate_type == "Z":  # Pauli-Z
            # Z|ψ⟩ → phase flip on |1⟩
            register.set_phase(theta_phase, phi_phase + math.pi)
        
        elif gate_type == "T":  # T gate (π/8)
            # T|ψ⟩ → π/4 phase on |1⟩
            register.set_phase(theta_phase, phi_phase + math.pi / 4)
        
        elif gate_type == "S":  # S gate (π/4)
            # S|ψ⟩ → π/2 phase on |1⟩
            register.set_phase(theta_phase, phi_phase + math.pi / 2)
        
        elif gate_type == "RZ":  # Rotation around Z
            alpha = params.get("alpha", 0.0)
            register.set_phase(theta_phase, phi_phase + alpha)
        
        elif gate_type == "RX":  # Rotation around X
            alpha = params.get("alpha", 0.0)
            register.set_phase(theta_phase + alpha, phi_phase)
    
    def measure(self, register_id: str) -> MeasurementResult:
        """
        PISP-007: Measure a register, collapsing its state.
        
        Parameters:
            register_id: ID of the register to measure
        
        Returns:
            MeasurementResult with value (0 or 1) and probability
        
        Spec: docs/spec/PISPHERE.md #PISP-007
        """
        if register_id not in self._registers:
            raise ValueError(f"Register {register_id} not found")
        
        register = self._registers[register_id]
        
        # Probability of measuring |0⟩ = cos²(θ/2)
        prob_0 = register.get_probability_0()
        
        # Simulate measurement (deterministic based on phase for reproducibility)
        # In a real system, this would be probabilistic
        value = 0 if prob_0 > 0.5 else 1
        probability = prob_0 if value == 0 else (1 - prob_0)
        
        return MeasurementResult(
            register_id=register_id,
            value=value,
            probability=probability,
            actual_phase=register.phase
        )
    
    def entangle(self, reg_a: str, reg_b: str, bell_type: str) -> BellPair:
        """
        PISP-008: Create a Bell-like entangled pair between two registers.
        
        Parameters:
            reg_a: First register ID
            reg_b: Second register ID
            bell_type: Type of Bell state ("PHI_PLUS", "PHI_MINUS", "PSI_PLUS", "PSI_MINUS")
        
        Returns:
            BellPair object
        
        Spec: docs/spec/PISPHERE.md #PISP-008
        """
        if reg_a not in self._registers or reg_b not in self._registers:
            raise ValueError("Both registers must exist")
        
        # Set up entangled phases based on Bell type
        reg_obj_a = self._registers[reg_a]
        reg_obj_b = self._registers[reg_b]
        
        if bell_type == "PHI_PLUS":
            # |Φ⁺⟩ = (|00⟩ + |11⟩)/√2
            reg_obj_a.set_phase(math.pi / 2, 0.0)
            reg_obj_b.set_phase(math.pi / 2, 0.0)
            correlation = 1.0
        elif bell_type == "PHI_MINUS":
            # |Φ⁻⟩ = (|00⟩ - |11⟩)/√2
            reg_obj_a.set_phase(math.pi / 2, 0.0)
            reg_obj_b.set_phase(math.pi / 2, math.pi)
            correlation = -1.0
        elif bell_type == "PSI_PLUS":
            # |Ψ⁺⟩ = (|01⟩ + |10⟩)/√2
            reg_obj_a.set_phase(math.pi / 2, 0.0)
            reg_obj_b.set_phase(math.pi / 2, math.pi / 2)
            correlation = 0.5
        elif bell_type == "PSI_MINUS":
            # |Ψ⁻⟩ = (|01⟩ - |10⟩)/√2
            reg_obj_a.set_phase(math.pi / 2, 0.0)
            reg_obj_b.set_phase(math.pi / 2, 3 * math.pi / 2)
            correlation = -0.5
        else:
            raise ValueError(f"Unknown Bell type: {bell_type}")
        
        return BellPair(
            reg_a=reg_a,
            reg_b=reg_b,
            bell_type=bell_type,
            correlation=correlation
        )
