"""
Network Sheaf — meta-network modeling from public observation planes.
"""

from .sheaf import (
    Plane, NodeKind, NodeId, Fiber, Observation, NetworkSheaf,
)
from .fusion import (
    phase_distance, lerp_phase, predict, prediction_confidence, residual,
    HolographicUpdater, select_probes, ResidualReconstructor,
)

__all__ = [
    "Plane", "NodeKind", "NodeId", "Fiber", "Observation", "NetworkSheaf",
    "phase_distance", "lerp_phase", "predict", "prediction_confidence",
    "residual", "HolographicUpdater", "select_probes",
    "ResidualReconstructor",
]
