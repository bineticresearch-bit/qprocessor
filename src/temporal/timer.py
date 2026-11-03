"""
Temporal Timer — TEMP-008 through TEMP-010 + ECHO INTEGRATION

A recursive timer that can branch into child timers, forming a computation tree.
Each timer represents a temporal qubit — its state is defined by when it expires.

ECHO INTEGRATION:
    Each timer can emit an echo cascade upon branching or expiry,
    enabling hyperfractal picosecond precision through self-similar
    temporal echo patterns.

Spec Reference: docs/spec/TEMPORAL.md, docs/spec/ECHO.md
"""

import time
import math
from typing import List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .echo import EchoCascade, HyperfractalResolver


class TimerState(Enum):
    """Timer lifecycle states."""
    PENDING = "pending"
    RUNNING = "running"
    BRANCHED = "branched"
    EXPIRED = "expired"


@dataclass
class TimerExpiryEvent:
    """Event produced when a timer expires."""
    timer_id: str
    expiry_time: float
    phase: tuple
    measurement_value: int  # 0 or 1
    probability: float


class Timer:
    """
    TEMP-008: A recursive temporal timer.
    
    Each timer represents a temporal qubit. Its state is defined by:
    - target_time: When it expires (measurement event)
    - phase: (theta, phi) defining quantum state
    - amplitude: Complex amplitude cos(θ/2) + e^(iφ)·sin(θ/2)
    - depth: Recursion depth (0 = root)
    - children: Child timers created by branching
    - echo_cascade: Hyperfractal echo cascade for picosecond precision
    
    Spec: docs/spec/TEMPORAL.md #TEMP-008
    """
    
    def __init__(
        self,
        id: str,
        target_time: float,
        phase: tuple = (0.0, 0.0),
        amplitude: complex = complex(1.0, 0.0),
        depth: int = 0,
        children: Optional[List['Timer']] = None,
        callback: Optional[Callable] = None
    ):
        self.id = id
        self.target_time = target_time
        self.phase = phase  # (theta, phi)
        self.amplitude = amplitude
        self.depth = depth
        self.children = children or []
        self.callback = callback
        self.state = TimerState.PENDING
        self.created_at = time.monotonic()
        self.echo_cascade: Optional[EchoCascade] = None  # Hyperfractal echo cascade
    
    def branch(self) -> Tuple['Timer', 'Timer']:
        """
        TEMP-009: Branch this timer into two child timers.
        
        Creates two child timers representing |0⟩ and |1⟩ paths.
        The branching is controlled by the timer's phase:
        - cos²(θ/2) → probability of |0⟩ path
        - sin²(θ/2) → probability of |1⟩ path
        
        Returns:
            Tuple of (child_0, child_1) timers
        
        Spec: docs/spec/TEMPORAL.md #TEMP-009
        """
        theta, phi = self.phase
        
        # Resolution: 1 microsecond separation between branches
        resolution = 1e-6
        
        # Child 0: |0⟩ path — phase based on cos²(θ/2)
        child_0 = Timer(
            id=f"{self.id}_0",
            target_time=self.target_time,
            phase=(theta, phi),
            amplitude=complex(math.cos(theta / 2), 0),
            depth=self.depth + 1,
            callback=self.callback
        )
        
        # Child 1: |1⟩ path — phase shifted by π/2
        child_1 = Timer(
            id=f"{self.id}_1",
            target_time=self.target_time + resolution,
            phase=(theta, phi + math.pi / 2),
            amplitude=complex(0, math.sin(theta / 2)),
            depth=self.depth + 1,
            callback=self.callback
        )
        
        self.children = [child_0, child_1]
        self.state = TimerState.BRANCHED
        
        return child_0, child_1
    
    def expire(self) -> TimerExpiryEvent:
        """
        TEMP-010: Expire this timer, producing a measurement event.
        
        The measurement result is determined by the timer's phase:
        - Arrival in t₀ window → measurement result 0
        - Arrival in t₁ window → measurement result 1
        
        Returns:
            TimerExpiryEvent with measurement result
        
        Spec: docs/spec/TEMPORAL.md #TEMP-010
        """
        theta, phi = self.phase
        
        # Probability of measuring |0⟩ = cos²(θ/2)
        prob_0 = math.cos(theta / 2) ** 2
        
        # Deterministic measurement based on phase threshold
        value = 0 if prob_0 >= 0.5 else 1
        probability = prob_0 if value == 0 else (1 - prob_0)
        
        self.state = TimerState.EXPIRED
        
        event = TimerExpiryEvent(
            timer_id=self.id,
            expiry_time=time.monotonic(),
            phase=self.phase,
            measurement_value=value,
            probability=probability
        )
        
        # Call callback if provided
        if self.callback:
            self.callback(event)
        
        return event
    
    def get_probability_0(self) -> float:
        """Get probability of measuring |0⟩: cos²(θ/2)."""
        theta, _ = self.phase
        return math.cos(theta / 2) ** 2
    
    def get_probability_1(self) -> float:
        """Get probability of measuring |1⟩: sin²(θ/2)."""
        theta, _ = self.phase
        return math.sin(theta / 2) ** 2
    
    def is_expired(self) -> bool:
        """Check if this timer has expired."""
        return self.state == TimerState.EXPIRED
    
    def is_branched(self) -> bool:
        """Check if this timer has been branched."""
        return self.state == TimerState.BRANCHED
    
    def time_remaining(self) -> float:
        """Get time remaining until expiry (seconds)."""
        return max(0.0, self.target_time - time.monotonic())
    
    def emit_echo(self, scaling_factor: float = 0.1, max_depth: int = 6) -> EchoCascade:
        """
        ECHO-TIMER: Emit hyperfractal echo cascade from this timer.
        
        Creates a self-similar echo cascade anchored to this timer's
        creation time. The cascade enables picosecond precision by
        analyzing interference patterns across recursion depths.
        
        Precision table:
            depth=3: 1μs → 1ns
            depth=6: 1μs → 1ps  ← default
            depth=9: 1μs → 1fs
        
        Args:
            scaling_factor: Geometric decay α (default: 0.1)
            max_depth: Max echo depth (default: 6)
        
        Returns:
            EchoCascade instance
        """
        cascade = EchoCascade(
            origin_time_s=self.created_at,
            base_resolution_s=1e-6,  # 1 microsecond base
            scaling_factor=scaling_factor,
            max_depth=max_depth,
        )
        cascade.emit(initial_phase=self.phase, initial_amplitude=self.amplitude)
        cascade.compute_derivatives(max_order=min(4, max_depth - 1))
        self.echo_cascade = cascade
        return cascade
    
    def resolve_echo_precision(self) -> Tuple[float, float]:
        """
        Resolve expiry time to hyperfractal precision.
        
        Uses Richardson extrapolation on the echo cascade to determine
        the expiry time at picosecond (or better) precision.
        
        Returns:
            (resolved_time_s, precision_s) tuple
        """
        if self.echo_cascade is None:
            self.emit_echo()
        return self.echo_cascade.resolve_hyperfractal()
    
    def echo_measurement(self) -> int:
        """
        Measure using echo cascade interference.
        
        The measurement outcome is determined by the collective
        interference of all echoes in the cascade, not just the
        single timer phase. This provides more robust measurement.
        
        Returns:
            0 or 1
        """
        if self.echo_cascade is None:
            self.emit_echo()
        return self.echo_cascade.measure()
    
    def __repr__(self) -> str:
        echo_str = f", echo={'yes' if self.echo_cascade else 'no'}"
        return (
            f"Timer(id={self.id}, depth={self.depth}, "
            f"phase=({self.phase[0]:.3f}, {self.phase[1]:.3f}), "
            f"state={self.state.value}{echo_str})"
        )
