"""
Temporal Engine — TEMP-001 through TEMP-007 + ECHO OPERATIONS (REALTIME)

The temporal engine manages recursive timers and applies quantum gates
as temporal operations. Time IS the computation.

REAL IMPLEMENTATION:
- Uses time.perf_counter_ns() for nanosecond precision
- Real-time timer scheduling with heapq
- Echo cascade integration for HYPERFRACTAL PICOSECOND PRECISION
- Cross-cascade interference for enhanced temporal resolution

Spec Reference: docs/spec/TEMPORAL.md, docs/spec/ECHO.md
"""

import time
import math
import heapq
import secrets
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
    actual_times: Dict[str, int]
    max_deviation_ns: int


@dataclass
class TemporalMeasurement:
    """Result of temporal measurement."""
    timer_id: str
    value: int
    probability: float
    expiry_time_ns: int
    phase_at_measurement: Tuple[float, float]
    echo_precision_s: Optional[float] = None


@dataclass
class TemporalBellPair:
    """Entangled pair of timers."""
    timer_a: Timer
    timer_b: Timer
    correlation: float


@dataclass
class EchoResolutionResult:
    """Result of resolving all timers via echo cascades."""
    timer_count: int
    resolutions: Dict[str, Tuple[int, float]]  # timer_id → (time_ns, precision_s)
    best_precision_s: float
    mean_precision_s: float


class TemporalEngine:
    """
    TEMP-001: Temporal computation engine (REALTIME).
    
    REAL: Uses perf_counter_ns for nanosecond precision.
    ECHO: Hyperfractal picosecond precision via echo cascades.
    
    Parameters:
        resolution_us: Timer resolution in microseconds (default: 1)
        max_timers: Maximum concurrent timers (default: 10000)
        echo_enabled: Enable echo cascade by default (default: True)
        echo_depth: Default echo depth (default: 6 → 1ps from 1ns)
    
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
        self._timer_queue: List[Tuple[int, str]] = []
        self._timer_counter = 0
        self._bell_pairs: List[TemporalBellPair] = []
        self._echo_resolver = HyperfractalResolver(
            base_resolution_ns=1,  # 1 nanosecond
            max_depth=echo_depth,
        )
    
    def create_timer(
        self,
        delay_us: int,
        phase: Tuple[float, float] = (0.0, 0.0),
        callback: Optional[Callable] = None
    ) -> Timer:
        """TEMP-002: Create a new timer (REALTIME + ECHO)."""
        if len(self._timers) >= self.max_timers:
            raise RuntimeError(f"Maximum timer limit ({self.max_timers}) reached")
        
        timer_id = f"timer_{self._timer_counter}"
        self._timer_counter += 1
        
        now_ns = time.perf_counter_ns()
        delay_ns = delay_us * 1000
        target_time_ns = now_ns + delay_ns
        
        timer = Timer(
            id=timer_id,
            target_time_ns=target_time_ns,
            phase=phase,
            callback=callback
        )
        
        # Auto-attach echo cascade
        if self.echo_enabled:
            timer.emit_echo(max_depth=self.echo_depth)
        
        self._timers[timer_id] = timer
        heapq.heappush(self._timer_queue, (target_time_ns, timer_id))
        
        return timer
    
    def create_recursive_timer(
        self,
        delay_us: int,
        depth: int,
        branch_fn: Optional[Callable] = None
    ) -> Timer:
        """TEMP-003: Create a recursive timer tree with echo cascades."""
        root = self.create_timer(delay_us)
        root.start()
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
        
        child_a.start()
        child_b.start()
        
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
        """TEMP-004: Apply a temporal gate to timers."""
        params = params or {}
        gate = TemporalGate(gate_type=gate_type, params=params)
        
        for timer_id in target_timer_ids:
            if timer_id not in self._timers:
                raise ValueError(f"Timer {timer_id} not found")
            
            timer = self._timers[timer_id]
            new_phase = gate.apply_to_phase(timer.phase)
            timer.set_phase(new_phase[0], new_phase[1])
            timer.amplitude = gate.apply_to_amplitude(timer.amplitude)
            
            # Re-emit echo with updated phase
            if self.echo_enabled:
                timer.emit_echo(max_depth=self.echo_depth)
    
    def sync_timers(
        self,
        timer_ids: List[str],
        target_time_ns: int
    ) -> SyncResult:
        """TEMP-005: Synchronize multiple timers."""
        actual_times = {}
        max_deviation = 0
        
        for timer_id in timer_ids:
            if timer_id not in self._timers:
                raise ValueError(f"Timer {timer_id} not found")
            
            timer = self._timers[timer_id]
            old_target = timer.target_time_ns
            timer.target_time_ns = target_time_ns
            actual_times[timer_id] = target_time_ns
            
            deviation = abs(target_time_ns - old_target)
            max_deviation = max(max_deviation, deviation)
        
        return SyncResult(
            timer_ids=timer_ids,
            target_time_ns=target_time_ns,
            actual_times=actual_times,
            max_deviation_ns=max_deviation
        )
    
    def measure(self, timer_id: str) -> TemporalMeasurement:
        """TEMP-006: Measure a timer (with echo precision if available)."""
        if timer_id not in self._timers:
            raise ValueError(f"Timer {timer_id} not found")
        
        timer = self._timers[timer_id]
        
        if timer.echo_cascade is not None:
            value = timer.echo_measurement()
            theta = timer.phase[0]
            prob = math.cos(theta / 2) ** 2 if value == 0 else math.sin(theta / 2) ** 2
            precision = timer.echo_cascade.effective_resolution_s
        else:
            value = timer.measure()
            theta = timer.phase[0]
            prob = math.cos(theta / 2) ** 2 if value == 0 else math.sin(theta / 2) ** 2
            precision = None
        
        return TemporalMeasurement(
            timer_id=timer_id,
            value=value,
            probability=prob,
            expiry_time_ns=timer.target_time_ns,
            phase_at_measurement=timer.phase,
            echo_precision_s=precision,
        )
    
    def generate_bell_pair(
        self,
        timer_a_id: str,
        timer_b_id: str
    ) -> TemporalBellPair:
        """TEMP-007: Create a Bell pair with echo-entangled cascades."""
        if timer_a_id not in self._timers:
            raise ValueError(f"Timer {timer_a_id} not found")
        if timer_b_id not in self._timers:
            raise ValueError(f"Timer {timer_b_id} not found")
        
        timer_a = self._timers[timer_a_id]
        timer_b = self._timers[timer_b_id]
        
        h_gate = TemporalGate.T_HADAMARD()
        new_phase = h_gate.apply_to_phase(timer_a.phase)
        timer_a.set_phase(new_phase[0], new_phase[1])
        timer_b.set_phase(timer_a.phase[0], timer_a.phase[1])
        
        if self.echo_enabled:
            timer_a.emit_echo(max_depth=self.echo_depth)
            timer_b.emit_echo(max_depth=self.echo_depth)
        
        bell_pair = TemporalBellPair(
            timer_a=timer_a,
            timer_b=timer_b,
            correlation=1.0
        )
        
        self._bell_pairs.append(bell_pair)
        return bell_pair
    
    # === ECHO OPERATIONS ===
    
    def emit_echo_on_timer(
        self,
        timer_id: str,
        scaling_factor: float = 0.1,
        max_depth: int = 6,
    ) -> EchoCascade:
        """ECHO-ENGINE-001: Attach echo cascade to timer."""
        if timer_id not in self._timers:
            raise ValueError(f"Timer {timer_id} not found")
        timer = self._timers[timer_id]
        return timer.emit_echo(scaling_factor=scaling_factor, max_depth=max_depth)
    
    def resolve_all_echoes(self) -> EchoResolutionResult:
        """ECHO-ENGINE-002: Resolve ALL timers to hyperfractal precision."""
        resolutions = {}
        precisions = []
        
        for timer_id, timer in self._timers.items():
            if timer.echo_cascade is not None:
                t_ns, p_s = timer.resolve_echo_precision()
                resolutions[timer_id] = (t_ns, p_s)
                precisions.append(p_s)
        
        best = min(precisions) if precisions else 1e-9
        mean = sum(precisions) / len(precisions) if precisions else 1e-9
        
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
        """ECHO-ENGINE-003: Create echo-entangled timer pair."""
        if timer_a_id not in self._timers:
            raise ValueError(f"Timer {timer_a_id} not found")
        if timer_b_id not in self._timers:
            raise ValueError(f"Timer {timer_b_id} not found")
        
        timer_a = self._timers[timer_a_id]
        timer_b = self._timers[timer_b_id]
        
        if timer_a.echo_cascade is None:
            timer_a.emit_echo(max_depth=self.echo_depth)
        if timer_b.echo_cascade is None:
            timer_b.emit_echo(max_depth=self.echo_depth)
        
        return self._echo_resolver.resolve_cross_cascade(
            timer_a.echo_cascade,
            timer_b.echo_cascade,
        )
    
    def tick(self) -> List[TimerExpiryEvent]:
        """Process expired timers."""
        now_ns = time.perf_counter_ns()
        expired_events = []
        
        while self._timer_queue and self._timer_queue[0][0] <= now_ns:
            _, timer_id = heapq.heappop(self._timer_queue)
            
            if timer_id in self._timers:
                timer = self._timers[timer_id]
                if not timer.is_expired():
                    event = timer.expire()
                    expired_events.append(event)
        
        return expired_events
    
    def get_timer(self, timer_id: str) -> Optional[Timer]:
        return self._timers.get(timer_id)
    
    def get_all_timers(self) -> List[Timer]:
        return list(self._timers.values())
    
    def get_expired_timers(self) -> List[Timer]:
        return [t for t in self._timers.values() if t.is_expired()]
    
    def get_active_timers(self) -> List[Timer]:
        return [t for t in self._timers.values() if not t.is_expired()]
    
    def precision_report(self) -> Dict:
        """Generate comprehensive precision report."""
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
