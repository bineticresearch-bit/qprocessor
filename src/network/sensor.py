"""
GlobalNetworkSensor — Orchestrator
===================================

The meta-network sensor: ties the sheaf, fusion core, and public channel
adapters into a single living system.

    Public channels → observations → residual → absorb → probe select
                          ↑                              ↓
                          └──────── model update ←───────┘

The sensor runs a bounded number of sensing cycles, each time:
  1. Polling all registered channel adapters
  2. Absorbing their observations holographically
  3. Selecting the next probes by maximum expected information gain
  4. Tracking convergence

Once converged, every network task becomes a *query to the model* rather
than an interaction with the network.

Spec Reference: docs/architecture/SheafFusion.md §4, §6
"""

import math
import time
from typing import Dict, List, Optional, Callable

from .sheaf import Plane, NodeId, NodeKind, Observation, NetworkSheaf
from .fusion import (
    HolographicUpdater, ResidualReconstructor, select_probes,
    predict, prediction_confidence, residual,
)
from .adapters import ChannelAdapter


class GlobalNetworkSensor:
    """
    Orchestrates the reconstruction loop over the network sheaf.

    Adapters are registered per plane; the sensor polls them each cycle,
    absorbs what they report, and (optionally) executes selected probes
    through a probe callback. All probing is rate-limited by the adapters
    themselves.
    """

    def __init__(self, sheaf: Optional[NetworkSheaf] = None,
                 updater: Optional[HolographicUpdater] = None):
        self.sheaf = sheaf or NetworkSheaf()
        self.updater = updater or HolographicUpdater()
        self.reconstructor = ResidualReconstructor(self.sheaf, self.updater)

        self.adapters: List[ChannelAdapter] = []
        self.probe_executor: Optional[Callable[[NodeId, Plane], Optional[Observation]]] = None
        self.probeable: Optional[Callable[[NodeId, Plane], bool]] = None

        self.cycle: int = 0
        self.total_observations: int = 0
        self.anomaly_log: List[Dict] = []

    # ---- registration ------------------------------------------------

    def register_adapter(self, adapter: ChannelAdapter):
        """Register a public channel adapter."""
        self.adapters.append(adapter)

    def register_adapters(self, adapters: List[ChannelAdapter]):
        """Register several public channel adapters at once."""
        for a in adapters:
            self.register_adapter(a)

    def set_probe_executor(self, executor:
                           Optional[Callable[[NodeId, Plane], Optional[Observation]]]):
        """
        Provide a callback that executes a selected probe.

        The callback receives (node_id, plane) and returns an Observation
        or None. In production this routes to RIPE Atlas or another
        responsible active-measurement substrate. It may be None, in which
        case the sensor relies purely on passive channel polling.
        """
        self.probe_executor = executor

    def set_probeable(self, predicate: Optional[Callable[[NodeId, Plane], bool]]):
        """
        Declare which (node, plane) cells the probe substrate can measure.

        Aggregate nodes (root, AS) often carry the highest uncertainty but
        cannot be probed directly. Without this predicate, probe selection
        would rank them first and waste the entire budget. The predicate
        keeps selection honest about what the substrate can actually do.
        """
        self.probeable = predicate

    # ---- sensing -----------------------------------------------------

    def sense(self, probe_budget: int = 0) -> Dict:
        """
        Run one sensing cycle.

        1. Poll all adapters for observations
        2. Absorb them holographically (residuals measured en route)
        3. Select and execute up to `probe_budget` active probes
        4. Report convergence status
        """
        self.cycle += 1
        cycle_start = time.time()

        # 1. Poll passive channels
        observations: List[Observation] = []
        for adapter in self.adapters:
            observations.extend(adapter.poll(self.sheaf))

        # 2. Absorb (the reconstructor measures residuals internally)
        report = self.reconstructor.step(observations)

        # Log high-residual events as anomalies
        for obs in observations:
            r = residual(self.sheaf, obs)
            if r > 0.6:
                self.anomaly_log.append({
                    "cycle": self.cycle,
                    "node": str(obs.node_id),
                    "plane": obs.plane.value,
                    "residual": r,
                    "source": obs.source,
                    "timestamp": obs.timestamp,
                })

        # 3. Active probing
        probes_executed = 0
        if probe_budget > 0 and self.probe_executor is not None:
            for node_id, plane, gain in select_probes(
                    self.sheaf, probe_budget, probeable=self.probeable):
                result = self.probe_executor(node_id, plane)
                if result is not None:
                    self.updater.absorb(self.sheaf, result,
                                        strength=min(1.0, 0.5 + gain))
                    probes_executed += 1

        self.total_observations += len(observations) + probes_executed

        return {
            "cycle": self.cycle,
            "observations": len(observations),
            "probes_executed": probes_executed,
            "mean_residual": report["mean_residual"],
            "residual_energy": report["residual_energy"],
            "anomalies": report["anomalies"],
            "convergence": self.reconstructor.convergence(),
            "elapsed_s": time.time() - cycle_start,
        }

    def run(self, cycles: int, probe_budget: int = 0,
            on_cycle: Optional[Callable[[Dict], None]] = None) -> List[Dict]:
        """Run multiple sensing cycles, optionally reporting each one."""
        reports = []
        for _ in range(cycles):
            r = self.sense(probe_budget=probe_budget)
            reports.append(r)
            if on_cycle is not None:
                on_cycle(r)
        return reports

    # ---- querying the model ------------------------------------------

    def query(self, node_id: NodeId, plane: Plane) -> Dict:
        """
        Query the model for a node's state in a plane.

        This is the point of the whole system: after convergence, network
        questions are answered by the model, not by the network.
        """
        fiber = self.sheaf.get_fiber(node_id)
        predicted = predict(self.sheaf, node_id, plane)
        conf = prediction_confidence(self.sheaf, node_id, plane)

        return {
            "node": str(node_id),
            "plane": plane.value,
            "phase": predicted,
            "confidence": conf,
            "observed": fiber is not None and fiber.get_phase(plane) is not None,
            "probability_healthy": (
                math.cos(predicted[0] / 2) ** 2 if predicted else 0.5
            ),
        }

    def health(self, node_id: NodeId) -> Dict[str, float]:
        """Aggregate health across all planes for a node."""
        out: Dict[str, float] = {}
        for plane in Plane:
            q = self.query(node_id, plane)
            out[plane.value] = q["probability_healthy"]
        return out

    def status(self) -> Dict:
        """System-level status."""
        conv = self.reconstructor.convergence()
        cov = self.sheaf.coverage()
        return {
            "cycle": self.cycle,
            "nodes": len(self.sheaf.nodes),
            "total_observations": self.total_observations,
            "adapters": len(self.adapters),
            "coverage": cov,
            "convergence": conv,
            "anomalies": len(self.anomaly_log),
        }

    def __repr__(self) -> str:
        s = self.status()
        return (f"GlobalNetworkSensor(cycle={s['cycle']}, "
                f"nodes={s['nodes']}, obs={s['total_observations']}, "
                f"convergence={s['convergence'].get('status', 'warming_up')})")
