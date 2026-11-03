"""
Fusion Core — Holographic Updater + Residual Reconstructor
============================================================

The four algorithms that make the network knowable without exhaustive
scanning:

    PREDICT    infer a node's phase in a plane from its neighborhood
    RESIDUAL   how much an observation fails to be explained
    ABSORB     update the model holographically (region, not a point)
    SELECT     choose the measurements that most reduce uncertainty

Together they form the reconstruction loop:

    Model → Predict → Probe where uncertainty is highest
      ↑                              ↓
      └──── Absorb residual ←────────┘

Because the network is sparse and structured, the residual converges to
noise and the model *becomes* the observable network.

Spec Reference: docs/architecture/SheafFusion.md §3, §4
"""

import math
import time
from typing import Dict, List, Optional, Tuple, Callable

from .sheaf import Plane, NodeId, NodeKind, Fiber, Observation, NetworkSheaf


# ============================================================
# Phase geometry helpers
# ============================================================

def phase_distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """
    Distance between two phases in [0, 1].

    θ is circular on [0, 2π) so we take the shorter arc; φ is treated
    linearly. The result is normalized so 1.0 = maximally different.
    """
    d_theta = abs(a[0] - b[0]) % (2 * math.pi)
    d_theta = min(d_theta, 2 * math.pi - d_theta)
    d_phi = abs(a[1] - b[1]) % (2 * math.pi)
    d_phi = min(d_phi, 2 * math.pi - d_phi)
    # normalize: max possible is π (theta) + π (phi) = 2π
    return min(1.0, (d_theta + d_phi) / (2 * math.pi))


def lerp_phase(a: Tuple[float, float], b: Tuple[float, float],
               t: float) -> Tuple[float, float]:
    """Linear interpolation between two phases, t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ============================================================
# PREDICT
# ============================================================

def predict(sheaf: NetworkSheaf, node_id: NodeId, plane: Plane,
            now: Optional[float] = None) -> Optional[Tuple[float, float]]:
    """
    Predict a node's phase in a plane from its neighborhood.

    Weighted interpolation over neighbors that have real observations in
    this plane. Weights come from non-avalanche similarity — close in the
    lattice means behaviorally similar.

    This is the mechanism that makes the network knowable *without*
    measurement: an endpoint never probed still has a predicted state,
    inferred from its AS, its prefix, and its behavioral neighbors.

    Returns None if no neighbor has been observed in this plane.
    """
    fiber = sheaf.get_fiber(node_id)
    if fiber is None:
        return None

    # If we have a direct observation, that IS the prediction
    direct = fiber.get_phase(plane)
    if direct is not None:
        return direct

    now = now if now is not None else time.time()

    # Gather neighbor observations in this plane
    weighted_sum_theta = 0.0
    weighted_sum_phi = 0.0
    total_weight = 0.0

    for neighbor in sheaf.neighborhood(node_id, max_size=8):
        nf = sheaf.get_fiber(neighbor)
        if nf is None:
            continue
        nphase = nf.get_phase(plane)
        if nphase is None:
            continue

        # Weight = similarity × neighbor confidence × freshness
        sim = sheaf.similarity(node_id, neighbor)
        conf = nf.get_confidence(plane)
        stal = nf.staleness(plane, now)
        freshness = 1.0 if stal == float("inf") else 1.0 / (1.0 + stal / 3600.0)

        w = sim * conf * freshness
        if w <= 0:
            continue

        weighted_sum_theta += w * nphase[0]
        weighted_sum_phi += w * nphase[1]
        total_weight += w

    if total_weight <= 0:
        return None

    return (weighted_sum_theta / total_weight, weighted_sum_phi / total_weight)


def prediction_confidence(sheaf: NetworkSheaf, node_id: NodeId, plane: Plane,
                          now: Optional[float] = None) -> float:
    """
    Confidence in the prediction for (node, plane), in [0, 1].

    Combines the node's own uncertainty with the strength of the
    neighborhood evidence supporting the prediction.
    """
    fiber = sheaf.get_fiber(node_id)
    if fiber is None:
        return 0.0

    now = now if now is not None else time.time()

    # Direct observation → high confidence, decayed by staleness
    if fiber.get_phase(plane) is not None:
        stal = fiber.staleness(plane, now)
        conf = fiber.get_confidence(plane)
        freshness = 1.0 if stal == float("inf") else 1.0 / (1.0 + stal / 3600.0)
        return conf * (0.5 + 0.5 * freshness)

    # Neighborhood prediction → confidence from evidence weight
    evidence = 0.0
    for neighbor in sheaf.neighborhood(node_id, max_size=8):
        nf = sheaf.get_fiber(neighbor)
        if nf is None or nf.get_phase(plane) is None:
            continue
        sim = sheaf.similarity(node_id, neighbor)
        conf = nf.get_confidence(plane)
        stal = nf.staleness(plane, now)
        freshness = 1.0 if stal == float("inf") else 1.0 / (1.0 + stal / 3600.0)
        evidence += sim * conf * freshness

    # Saturating evidence → confidence
    return min(1.0, evidence / 2.0)


# ============================================================
# RESIDUAL
# ============================================================

def residual(sheaf: NetworkSheaf, obs: Observation,
             now: Optional[float] = None) -> float:
    """
    How much an observation fails to be explained by the model.

    r = |observed_phase − predicted_phase|, normalized to [0, 1] and
    weighted by the observation's own confidence.

    The residual is simultaneously:
      - the INFORMATION GAIN of the measurement (how much the model learns)
      - the ANOMALY SCORE of the measurement (how surprising the event is)
    """
    predicted = predict(sheaf, obs.node_id, obs.plane, now)
    if predicted is None:
        # Model knows nothing here — the observation is entirely novel
        return 1.0

    return phase_distance(obs.phase, predicted) * obs.confidence


# ============================================================
# ABSORB — the holographic updater
# ============================================================

class HolographicUpdater:
    """
    Updates the model from observations, holographically.

    When an observation arrives:
      1. DIRECT UPDATE — the node's fiber in that plane moves toward the
         observed phase, scaled by strength and observation confidence.
      2. HOLOGRAPHIC PROPAGATION — the update radiates to the node's
         lattice neighborhood with strength decaying in non-avalanche
         similarity. Neighbors learn "something near you changed" without
         being measured.

    This is the "a part reconstructs the whole" property: one measurement
    updates a region, not a point.
    """

    def __init__(self, propagation_radius: int = 8,
                 decay_rate: float = 0.35,
                 max_phase_step: float = 0.5):
        self.propagation_radius = propagation_radius
        self.decay_rate = decay_rate      # how fast influence fades with similarity
        self.max_phase_step = max_phase_step

    def absorb(self, sheaf: NetworkSheaf, obs: Observation,
               strength: float = 1.0) -> Dict[str, float]:
        """
        Absorb one observation into the model.

        Returns a report of what changed (useful for logging/convergence
        tracking).
        """
        now = obs.timestamp
        report = {"direct_delta": 0.0, "propagated": 0, "propagated_delta": 0.0}

        # 1. Direct update
        fiber = sheaf.add_node(obs.node_id)
        report["direct_delta"] = self._update_fiber(
            fiber, obs.plane, obs.phase, obs.confidence, strength, now
        )

        # 2. Holographic propagation
        for neighbor in sheaf.neighborhood(obs.node_id,
                                           max_size=self.propagation_radius):
            nf = sheaf.get_fiber(neighbor)
            if nf is None:
                continue

            sim = sheaf.similarity(obs.node_id, neighbor)
            if sim <= 0.0:
                continue

            # Influence decays with similarity distance
            influence = strength * obs.confidence * math.exp(
                -(1.0 - sim) / self.decay_rate
            )
            if influence < 0.01:
                continue

            delta = self._update_fiber(
                nf, obs.plane, obs.phase, influence * 0.5, influence, now
            )
            if delta > 0:
                report["propagated"] += 1
                report["propagated_delta"] += delta

        return report

    def _update_fiber(self, fiber: Fiber, plane: Plane,
                      target_phase: Tuple[float, float],
                      confidence: float, strength: float,
                      now: float) -> float:
        """
        Move a fiber's phase toward an observed phase.

        The step is capped so a single observation can never rewrite a
        well-established belief — learning is incremental, and the cap
        scales with how confident we already are.
        """
        current = fiber.get_phase(plane)
        current_conf = fiber.get_confidence(plane)

        if current is None:
            # No prior belief — adopt the observation directly
            fiber.observe(plane, target_phase,
                          max(0.0, min(1.0, confidence * strength)), now)
            return 1.0

        # Blend: how far we move depends on strength and how established
        # the current belief is. Established beliefs move slowly.
        mobility = strength * (1.0 - 0.5 * current_conf)
        step = min(self.max_phase_step, mobility)

        new_phase = lerp_phase(current, target_phase, step)

        # Confidence grows with each absorption, saturating at 1.0
        new_conf = min(1.0, current_conf + 0.1 * strength * confidence)

        delta = phase_distance(current, new_phase)
        fiber.observe(plane, new_phase, new_conf, now)
        return delta


# ============================================================
# SELECT — active inference probe selection
# ============================================================

def select_probes(sheaf: NetworkSheaf, budget: int,
                  planes: Optional[List[Plane]] = None,
                  now: Optional[float] = None,
                  probeable: Optional[Callable[[NodeId, Plane], bool]] = None
                  ) -> List[Tuple[NodeId, Plane, float]]:
    """
    Choose the measurements that will most reduce model uncertainty.

    Ranks candidate (node, plane) cells by expected information gain:

        gain = uncertainty × (1 − prediction_confidence) × staleness

    and returns the top `budget`. This is active inference / Bayesian
    experimental design: the system chooses what to look at next rather
    than scanning blindly.

    `probeable` is an optional predicate (node_id, plane) → bool. When
    given, only cells the probe substrate can actually measure are
    ranked. This matters: aggregate nodes (root, AS) often carry the
    highest uncertainty but cannot be probed directly — ranking them
    first would waste every probe budget. The predicate keeps selection
    honest about what the substrate can do.

    As the model converges, selected probes naturally migrate from broad
    exploration to the shrinking set of genuinely unknown regions and to
    the frontiers of active change.
    """
    now = now if now is not None else time.time()
    planes = planes or list(Plane)

    candidates: List[Tuple[NodeId, Plane, float]] = []

    for node_id, fiber in sheaf.nodes.items():
        for plane in planes:
            if probeable is not None and not probeable(node_id, plane):
                continue
            uncertainty = fiber.uncertainty(plane, now)
            if uncertainty <= 0.01:
                continue  # already known

            pred_conf = prediction_confidence(sheaf, node_id, plane, now)
            # If the neighborhood already predicts this well, probing adds less
            novelty = 1.0 - pred_conf

            stal = fiber.staleness(plane, now)
            staleness = 1.0 if stal == float("inf") else min(1.0, stal / 3600.0)

            gain = uncertainty * novelty * (0.25 + 0.75 * staleness)
            if gain > 0.01:
                candidates.append((node_id, plane, gain))

    candidates.sort(key=lambda c: c[2], reverse=True)
    return candidates[:budget]


# ============================================================
# The reconstruction loop
# ============================================================

class ResidualReconstructor:
    """
    Drives the model toward convergence.

    Each step:
      1. Receive observations from public channels (or probes)
      2. Measure residuals — what does the model fail to explain?
      3. Absorb the residuals holographically
      4. Select the next probes by maximum expected information gain

    Convergence is tracked as total residual energy over the lattice.
    """

    def __init__(self, sheaf: NetworkSheaf, updater: Optional[HolographicUpdater] = None):
        self.sheaf = sheaf
        self.updater = updater or HolographicUpdater()
        self.history: List[Dict[str, float]] = []

    def step(self, observations: List[Observation]) -> Dict[str, float]:
        """
        Absorb a batch of observations; return a convergence report.
        """
        now = time.time()
        total_residual = 0.0
        absorbed = 0
        anomalies: List[Tuple[Observation, float]] = []

        for obs in observations:
            r = residual(self.sheaf, obs, now)
            total_residual += r
            if r > 0.5:
                anomalies.append((obs, r))
            self.updater.absorb(self.sheaf, obs, strength=min(1.0, 0.5 + r))
            absorbed += 1

        energy = self.sheaf.total_residual_energy()
        report = {
            "absorbed": float(absorbed),
            "mean_residual": (total_residual / absorbed) if absorbed else 0.0,
            "anomalies": float(len(anomalies)),
            "residual_energy": energy,
        }
        self.history.append(report)
        return report

    def convergence(self) -> Dict[str, float]:
        """
        Is the model converging?

        Compares recent residual energy against earlier history. A
        converging model shows decreasing energy; a converged model shows
        energy that has plateaued at a low value.
        """
        if len(self.history) < 4:
            return {"status": "warming_up", "trend": 0.0}

        n = len(self.history)
        early = self.history[: max(1, n // 3)]
        late = self.history[-max(1, n // 3):]

        early_e = sum(h["residual_energy"] for h in early) / len(early)
        late_e = sum(h["residual_energy"] for h in late) / len(late)

        if early_e > 0:
            trend = (early_e - late_e) / early_e   # positive = converging
        else:
            trend = 0.0

        if late_e < 0.05 * max(1.0, early_e) or late_e < 1.0:
            status = "converged"
        elif trend > 0.05:
            status = "converging"
        elif trend < -0.05:
            status = "diverging"
        else:
            status = "plateaued"

        return {
            "status": status,
            "trend": trend,
            "early_energy": early_e,
            "late_energy": late_e,
        }

    def __repr__(self) -> str:
        c = self.convergence()
        return (f"ResidualReconstructor(steps={len(self.history)}, "
                f"status={c.get('status', 'warming_up')}, "
                f"energy={self.sheaf.total_residual_energy():.2f})")
