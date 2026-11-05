"""Temporal Module (REALTIME + ECHO HYPERFRACTAL PRECISION)"""

from .engine import TemporalEngine, SyncResult, TemporalMeasurement, TemporalBellPair, EchoResolutionResult
from .timer import Timer, TimerState, TimerExpiryEvent
from .gates import TemporalGate, GateType
from .signature import (forward_phasor, echo_comb, combined_signal,
                        recover_delta, dual_arm_delta, project, triangulate, signature_gate)
from .echo import (
    Echo, EchoDerivative, EchoCascade, EchoState,
    HyperfractalResolver,
)

__all__ = [
    "TemporalEngine", "SyncResult", "TemporalMeasurement", "TemporalBellPair",
    "recover_delta", "triangulate", "signature_gate",
    "EchoResolutionResult",
    "Timer", "TimerState", "TimerExpiryEvent",
    "TemporalGate", "GateType",
    "Echo", "EchoDerivative", "EchoCascade", "EchoState",
    "HyperfractalResolver",
]
