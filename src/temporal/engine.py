"""
Temporal Engine — TEMP-001 through TEMP-007 + ECHO OPERATIONS

The temporal engine manages recursive timers and applies quantum gates
as temporal operations. Time IS the computation.

ECHO OPERATIONS:
    The engine now supports hyperfractal echo-based precision:
    - emit_echo_on_timer(): Attach echo cascade to any timer
    - resolve_all_echoes(): Resolve all timers to picosecond precision
    - echo_entangle(): Create echo-entangled timer pairs
    
    The echo cascade achieves picosecond precision from microsecond
    hardware through self-similar temporal interference patterns.

Spec Reference: docs/spec/TEMPORAL.md, docs/spec/ECHO.md
"""

import time
import math
import heapq
from typing import List, Dict, Optional, Callable, Tuple
from dataclasses import dataclass

from .timer import Timer, TimerState, TimerExpiryEvent
from .gates import TemporalGate, GateType
from .echo import EchoCascade, HyperfractalResolver


@dataclass
class SyncResult:
    """Result of timer synchronization."""
    timer_ids: List[str]
    target_time_ns: int
    actual_times: Dict[str, float]
    max_deviation: float


@dataclass
class TemporalMeasurement:
    """Result of temporal measurement."""
    timer_id: str
    value: int
    probability: float
    expiry_time: float
    phase_at_measurement: tuple
    echo_precision_s: Optional[float] = None  # Hyperfractal precision if available


@dataclass
class EchoResolutionResult:
    """Result of resolving all timers via echo cascades."""
    timer_count: int
    resolutions: Dict[str, Tuple[float, float]]  # timer_id → (time_s, precision_s)
    best_precision_s: float
    mean_precision_s: float


class TemporalEngine:
    """
    TEMP-001: Temporal computation engine.
    
    Manages a collection of timers and provides quantum gate operations
    in the temporal domain. Time IS the computation.
    
    Now with ECHO INTEGRATION for hyperfractal picosecond precision.
    
    Parameters:
        resolution_us: Timer resolution in microseconds (default: 1)
        max_timers: Maximum number of concurrent timers (default: 10000)
        echo_enabled: Enable echo cascade by default (default: True)
        echo_depth: Default echo cascade depth (default: 6 → 1ps)
    
    Spec: docs/spec/TEMPORAL.md #TEMP-001
    """
    
    def __init__(
        self,
        resolution_us: int = 1,
        max_timers: int = 10000,
        echo_enabled: bool = True,
        echo_depth: int = 6,
    ):
        self.resolution_us = resolution_us
        self.max_timers = max_timers
        self.echo_enabled = echo_enabled
        self.echo_depth = echo_depth
        self._timers: Dict[str, Timer] = {}
        self._timer_queue: List[Tuple[float, str]] = []
        self._timer_counter = 0
        self._echo_resolver = HyperfractalResolver(
            base_resolution_s=resolution_us * 1e-6,
            max_depth=echo_depth,
        )
    
    def create_timer(
        self,
        delay_us: int,
        phase: Tuple[float, float] = (0.0, 0.0),
        callback: Optional[Callable] = None
    ) -> Timer:
        """
        TEMP-002: Create a new timer.
        
        If echo_enabled, automatically attaches an echo cascade
        for hyperfractal precision.
        """
        if len(self._timers) >= self.max_timers:
            raise RuntimeError(f"Maximum timer limit ({self.max_timers}) reached")
        
        timer_id = f"timer_{self._timer_counter}"
        self._timer_counter += 1
        
        now = time.monotonic()
        delay_s = delay_us * 1e-6
        target_time = now + delay_s
        
        timer = Timer(
            id=timer_id,
            target_time=target_time,
            phase=phase,
            callback=callback
        )
        
        # Auto-attach echo cascade if enabled
        if self.echo_enabled:
            timer.emit_echo(max_depth=self.echo_depth)
        
        self._timers[timer_id] = timer
        heapq.heappush(self._timer_queue, (target_time, timer_id))
        
        return timer
    
    def create_recursive_timer(
        self,
        delay_us: int,
        depth: int,
        branch_fn: Optional[Callable] = None
    ) -> Timer:
        """
        TEMP-003: Create a recursive timer tree.
        
        Creates a timer that branches at each level, producing 2^d
        leaf timers for depth d. Each leaf gets its own echo cascade.
        """
        root = self.create_timer(delay_us)
        
        self._branch_recursive(root, depth, 0)
        
        return root
    
    def _branch_recursive(
        self,
        timer: Timer,
        max_depth: int,
        current_depth: int
    ) -> None:
        """Recursively branch a timer."""
        if current_depth >= max_depth:
            return
        
        child_a, child_b = timer.branch()
        self._timers[child_a.id] = child_a
        self._timers[child_b.id] = child_b
        
        # Attach echo cascades to children
        if self.echo_enabled:
            child_a.emit_echo(max_depth=self.echo_depth)
            child_b.emit_echo(max_depth=self.echo_depth)
        
        self._branch_recursive(child_a, max_depth, current_depth + 1)
        self._branch_recursive(child_b, max_depth, current_depth + 1)
    
    def apply_gate(
        self,
        gate_type: GateType,
        target_timer_ids: List[str],
        params: Optional[Dict] = None
    ) -> None:
        """
        TEMP-004: Apply a temporal gate to timers.

        Accepts either a GateType enum or its string name (e.g. "T_ROTATE").
        Branching gates (T_HADAMARD, T_SPLIT) create child timers, which
        is how the gate population grows.
        """
        params = params or {}

        # Normalize string gate names to GateType
        if isinstance(gate_type, str):
            try:
                gate_type = GateType(gate_type)
            except ValueError:
                raise ValueError(
                    f"Unknown gate type: {gate_type}. "
                    f"Valid: {[g.value for g in GateType]}"
                )

        gate = TemporalGate(gate_type=gate_type, params=params)

        for timer_id in target_timer_ids:
            if timer_id not in self._timers:
                raise ValueError(f"Timer {timer_id} not found")

            timer = self._timers[timer_id]

            # Branching gates create children rather than just shifting phase
            if gate_type in (GateType.T_HADAMARD, GateType.T_SPLIT):
                child_0, child_1 = timer.branch()
                self._timers[child_0.id] = child_0
                self._timers[child_1.id] = child_1
                if self.echo_enabled:
                    child_0.emit_echo(max_depth=self.echo_depth)
                    child_1.emit_echo(max_depth=self.echo_depth)
                continue

            new_phase = gate.apply_to_phase(timer.phase)
            timer.phase = new_phase

            # Re-emit echo with updated phase
            if self.echo_enabled:
                timer.emit_echo(max_depth=self.echo_depth)
    
    def sync_timers(
        self,
        timer_ids: List[str],
        target_time_ns: int
    ) -> SyncResult:
        """TEMP-005: Synchronize multiple timers to a common target time."""
        actual_times = {}
        max_deviation = 0.0
        
        target_time = target_time_ns * 1e-9
        
        for timer_id in timer_ids:
            if timer_id not in self._timers:
                raise ValueError(f"Timer {timer_id} not found")
            
            timer = self._timers[timer_id]
            old_target = timer.target_time
            
            timer.target_time = target_time
            actual_times[timer_id] = target_time
            
            deviation = abs(target_time - old_target)
            max_deviation = max(max_deviation, deviation)
        
        return SyncResult(
            timer_ids=timer_ids,
            target_time_ns=target_time_ns,
            actual_times=actual_times,
            max_deviation=max_deviation
        )
    
    def measure(self, timer_id: str) -> TemporalMeasurement:
        """
        TEMP-006: Measure a timer's temporal state.
        
        If echo cascade is attached, uses echo-based measurement
        and reports hyperfractal precision.
        """
        if timer_id not in self._timers:
            raise ValueError(f"Timer {timer_id} not found")
        
        timer = self._timers[timer_id]
        
        # Use echo measurement if available
        if timer.echo_cascade is not None:
            value = timer.echo_measurement()
            theta = timer.phase[0]
            prob = math.cos(theta / 2) ** 2 if value == 0 else math.sin(theta / 2) ** 2
            precision = timer.echo_cascade.effective_resolution_s
        else:
            # Fall back to standard measurement
            event = timer.expire()
            value = event.measurement_value
            prob = event.probability
            precision = None
        
        return TemporalMeasurement(
            timer_id=timer_id,
            value=value,
            probability=prob,
            expiry_time=timer.target_time,
            phase_at_measurement=timer.phase,
            echo_precision_s=precision,
        )
    
    def generate_bell_pair(
        self,
        timer_a_id: str,
        timer_b_id: str
    ) -> Tuple[Timer, Timer]:
        """
        TEMP-007: Create a Bell pair between two timers.
        
        With echo integration, the entanglement extends to the
        echo cascades, creating correlated temporal fractals.
        """
        if timer_a_id not in self._timers:
            raise ValueError(f"Timer {timer_a_id} not found")
        if timer_b_id not in self._timers:
            raise ValueError(f"Timer {timer_b_id} not found")
        
        timer_a = self._timers[timer_a_id]
        timer_b = self._timers[timer_b_id]
        
        # Apply Hadamard to timer_a
        h_gate = TemporalGate.T_HADAMARD()
        new_phase = h_gate.apply_to_phase(timer_a.phase)
        timer_a.phase = new_phase
        
        # Correlate timer_b with timer_a
        timer_b.phase = timer_a.phase
        
        # Re-emit echoes with correlated phases
        if self.echo_enabled:
            cascade_a = timer_a.emit_echo(max_depth=self.echo_depth)
            cascade_b = timer_b.emit_echo(max_depth=self.echo_depth)

        return {
            "timer_a": timer_a.id,
            "timer_b": timer_b.id,
            "type": "PHI_PLUS",
        }
    
    # === ECHO OPERATIONS ===
    
    def emit_echo_on_timer(
        self,
        timer_id: str,
        scaling_factor: float = 0.1,
        max_depth: int = 6,
    ) -> EchoCascade:
        """
        ECHO-ENGINE-001: Attach an echo cascade to an existing timer.
        
        Args:
            timer_id: Timer to attach echo to
            scaling_factor: Geometric decay α
            max_depth: Echo recursion depth
        
        Returns:
            The emitted EchoCascade
        """
        if timer_id not in self._timers:
            raise ValueError(f"Timer {timer_id} not found")
        
        timer = self._timers[timer_id]
        return timer.emit_echo(scaling_factor=scaling_factor, max_depth=max_depth)
    
    def resolve_all_echoes(self) -> EchoResolutionResult:
        """
        ECHO-ENGINE-002: Resolve ALL timers to hyperfractal precision.
        
        Iterates over all timers with echo cascades and resolves
        each one to picosecond (or better) precision.
        
        Returns:
            EchoResolutionResult with per-timer resolutions
        """
        resolutions = {}
        precisions = []
        
        for timer_id, timer in self._timers.items():
            if timer.echo_cascade is not None:
                t_s, p_s = timer.resolve_echo_precision()
                resolutions[timer_id] = (t_s, p_s)
                precisions.append(p_s)
        
        best = min(precisions) if precisions else self.resolution_us * 1e-6
        mean = sum(precisions) / len(precisions) if precisions else self.resolution_us * 1e-6
        
        return EchoResolutionResult(
            timer_count=len(resolutions),
            resolutions=resolutions,
            best_precision_s=best,
            mean_precision_s=mean,
        )
    
    def echo_entangle(
        self,
        timer_a_id: str,
        timer_b_id: str,
    ) -> Dict:
        """
        ECHO-ENGINE-003: Create echo-entangled timer pair.
        
        The echo cascades of both timers become correlated,
        enabling cross-cascade interference for enhanced precision.
        
        Returns:
            Dict with cross-cascade resolution results
        """
        if timer_a_id not in self._timers:
            raise ValueError(f"Timer {timer_a_id} not found")
        if timer_b_id not in self._timers:
            raise ValueError(f"Timer {timer_b_id} not found")
        
        timer_a = self._timers[timer_a_id]
        timer_b = self._timers[timer_b_id]
        
        # Ensure both have echo cascades
        if timer_a.echo_cascade is None:
            timer_a.emit_echo(max_depth=self.echo_depth)
        if timer_b.echo_cascade is None:
            timer_b.emit_echo(max_depth=self.echo_depth)
        
        # Cross-cascade analysis
        result = self._echo_resolver.resolve_cross_cascade(
            timer_a.echo_cascade,
            timer_b.echo_cascade,
        )
        
        return result
    
    def tick(self) -> List[TimerExpiryEvent]:
        """Process expired timers."""
        now = time.monotonic()
        expired_events = []
        
        while self._timer_queue and self._timer_queue[0][0] <= now:
            _, timer_id = heapq.heappop(self._timer_queue)
            
            if timer_id in self._timers:
                timer = self._timers[timer_id]
                if not timer.is_expired():
                    event = timer.expire()
                    expired_events.append(event)
        
        return expired_events
    
    def get_timer_count(self) -> int:
        """TEMP-019: Get the number of timers currently managed."""
        return len(self._timers)

    def get_timer(self, timer_id: str) -> Optional[Timer]:
        """Get a timer by ID."""
        return self._timers.get(timer_id)
    
    def get_all_timers(self) -> List[Timer]:
        """Get all timers."""
        return list(self._timers.values())
    
    def get_expired_timers(self) -> List[Timer]:
        """Get all expired timers."""
        return [t for t in self._timers.values() if t.is_expired()]
    
    def get_active_timers(self) -> List[Timer]:
        """Get all active (non-expired) timers."""
        return [t for t in self._timers.values() if not t.is_expired()]
    
    def precision_report(self) -> Dict:
        """Generate a comprehensive precision report."""
        report = self._echo_resolver.precision_report()
        report['total_timers'] = len(self._timers)
        report['timers_with_echo'] = sum(
            1 for t in self._timers.values() if t.echo_cascade is not None
        )
        return report
    
    def __repr__(self) -> str:
        echo_count = sum(1 for t in self._timers.values() if t.echo_cascade is not None)
        return (
            f"TemporalEngine(timers={len(self._timers)}, "
            f"active={len(self.get_active_timers())}, "
            f"echo_cascades={echo_count}, "
            f"precision={self._echo_resolver.theoretical_precision_s:.2e}s)"
        )
