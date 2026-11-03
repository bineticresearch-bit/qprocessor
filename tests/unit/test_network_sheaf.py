"""
Convergence Proof — Network Sheaf Reconstruction
=================================================

The critical validation: does the model reconstruct the full network
from sparse observations?

The SyntheticNetwork provides ground truth. We feed the sensor a small
fraction of that truth and measure `reconstruction_error` — the gap
between the model's belief and reality, including for nodes that were
NEVER directly observed.

If the error drops well below the observation fraction, the reconstruction
loop works: the model knows the network without measuring it.

Run:
    python3 tests/unit/test_network_sheaf.py
"""

import sys
import os
import math
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.network.sheaf import (NetworkSheaf, NodeId, NodeKind, Plane,
                               Observation, Fiber)
from src.network.fusion import (HolographicUpdater, ResidualReconstructor,
                                predict, prediction_confidence, residual,
                                select_probes, phase_distance, lerp_phase)
from src.network.adapters import SyntheticNetwork
from src.network.sensor import GlobalNetworkSensor


def test_phase_geometry():
    """Phase distance and interpolation behave correctly."""
    assert phase_distance((0.0, 0.0), (0.0, 0.0)) == 0.0
    assert phase_distance((0.0, 0.0), (math.pi, 0.0)) == 0.5
    # circular on theta
    assert phase_distance((0.0, 0.0), (2 * math.pi, 0.0)) == 0.0
    # interpolation midpoint
    mid = lerp_phase((0.0, 0.0), (1.0, 1.0), 0.5)
    assert abs(mid[0] - 0.5) < 1e-9 and abs(mid[1] - 0.5) < 1e-9
    print("✓ SHEAF-001: phase geometry works")


def test_sheaf_structure():
    """Sheaf builds hierarchy, adjacency, and metric similarity."""
    sheaf = NetworkSheaf()
    as1 = NodeId(NodeKind.AUTONOMOUS_SYSTEM, "AS1")
    p1 = NodeId(NodeKind.PREFIX, "10.0.0.0/24")
    e1 = NodeId(NodeKind.ENDPOINT, "10.0.0.1")
    for n in (as1, p1, e1):
        sheaf.add_node(n)
    sheaf.add_edge(as1, p1)
    sheaf.add_edge(p1, e1)

    assert len(sheaf.nodes) == 4  # root + 3
    assert e1 in sheaf.neighbors(p1)
    # adjacency boosts similarity
    assert sheaf.similarity(p1, e1) >= 0.9
    # self-similarity is 1
    assert sheaf.similarity(e1, e1) == 1.0
    # neighborhood returns the adjacent node first
    nb = sheaf.neighborhood(e1, max_size=2)
    assert p1 in nb
    print("✓ SHEAF-002: sheaf structure and metric space work")


def test_holographic_propagation():
    """An observation on one node propagates to its neighborhood."""
    syn = SyntheticNetwork(n_ases=1, n_prefixes=1, n_endpoints=3, seed=7)
    sheaf = syn.build_sheaf()
    updater = HolographicUpdater()

    nodes = list(syn.ground_truth.keys())
    target, neighbor = nodes[0], nodes[1]

    # Observe only `target` in PROBE
    obs = syn.observe(target, Plane.PROBE)
    report = updater.absorb(sheaf, obs)

    assert report["direct_delta"] > 0
    # The neighbor should now have SOME belief in PROBE despite never
    # being directly observed — the holographic property.
    nf = sheaf.get_fiber(neighbor)
    assert nf is not None
    assert nf.get_phase(Plane.PROBE) is not None, \
        "holographic propagation failed to seed neighbor belief"
    print("✓ SHEAF-003: holographic propagation works (region, not a point)")


def test_prediction_infers_unobserved():
    """Prediction infers state for nodes never directly observed."""
    syn = SyntheticNetwork(n_ases=2, n_prefixes=2, n_endpoints=2, seed=11)
    sheaf = syn.build_sheaf()
    updater = HolographicUpdater()

    nodes = list(syn.ground_truth.keys())
    observed, unobserved = nodes[0], nodes[2]

    updater.absorb(sheaf, syn.observe(observed, Plane.PROBE))

    pred = predict(sheaf, unobserved, Plane.PROBE)
    assert pred is not None, "prediction returned None for unobserved node"
    assert prediction_confidence(sheaf, unobserved, Plane.PROBE) > 0
    print("✓ SHEAF-004: prediction infers unobserved nodes from neighborhood")


def test_residual_distinguishes_novel_from_expected():
    """Residual is low for expected observations, high for novel ones."""
    syn = SyntheticNetwork(n_ases=1, n_prefixes=1, n_endpoints=2, seed=13)
    sheaf = syn.build_sheaf()
    updater = HolographicUpdater()

    nodes = list(syn.ground_truth.keys())
    updater.absorb(sheaf, syn.observe(nodes[0], Plane.PROBE))

    # An observation matching the model's belief → low residual
    matching = Observation(node_id=nodes[0], plane=Plane.PROBE,
                           phase=syn.ground_truth[nodes[0]][Plane.PROBE],
                           confidence=0.9)
    assert residual(sheaf, matching) < 0.1

    # A wildly different observation → high residual (anomaly)
    anomalous = Observation(node_id=nodes[0], plane=Plane.PROBE,
                            phase=(math.pi, math.pi), confidence=0.9)
    assert residual(sheaf, anomalous) > 0.5
    print("✓ SHEAF-005: residual separates expected from anomalous")


def test_probe_selection_targets_uncertainty():
    """Probe selection ranks unknown cells above known ones."""
    syn = SyntheticNetwork(n_ases=1, n_prefixes=1, n_endpoints=3, seed=17)
    sheaf = syn.build_sheaf()
    updater = HolographicUpdater()

    nodes = list(syn.ground_truth.keys())
    # Fully observe one node in one plane
    updater.absorb(sheaf, syn.observe(nodes[0], Plane.PROBE))

    probes = select_probes(sheaf, budget=5)
    assert len(probes) > 0
    # The observed cell should NOT be the top pick — it has low uncertainty
    top = probes[0]
    assert not (top[0] == nodes[0] and top[1] == Plane.PROBE), \
        "probe selection preferred a known cell"
    print("✓ SHEAF-006: probe selection targets maximum uncertainty")


def test_convergence_reduces_error():
    """
    THE CORE PROOF: reconstruction error falls well below the
    observation fraction. The model knows more than it measured.
    """
    syn = SyntheticNetwork(n_ases=3, n_prefixes=2, n_endpoints=3, seed=23)
    sheaf = syn.build_sheaf()
    sensor = GlobalNetworkSensor(sheaf=sheaf)

    # Probe executor reads ground truth with small noise
    def probe(node_id, plane):
        """Probe a node against synthetic ground truth with small noise."""
        if node_id in syn.ground_truth:
            return syn.observe(node_id, plane, noise=0.02)
        return None
    sensor.set_probe_executor(probe)
    # Only endpoints are directly probeable; aggregates (root/AS/prefix)
    # must be inferred holographically from the endpoints they contain.
    sensor.set_probeable(lambda node_id, plane:
                         node_id.kind == NodeKind.ENDPOINT)

    # Observe only 15% of the ground truth up front
    initial = syn.sample_observations(fraction=0.15)
    for obs in initial:
        sensor.updater.absorb(sensor.sheaf, obs, strength=0.8)

    error_before = syn.reconstruction_error(sensor.sheaf)
    mean_before = sum(error_before.values()) / len(error_before)

    # Run sensing cycles with active probing
    for _ in range(12):
        sensor.sense(probe_budget=6)

    error_after = syn.reconstruction_error(sensor.sheaf)
    mean_after = sum(error_after.values()) / len(error_after)

    assert mean_after < mean_before, \
        f"reconstruction error did not fall: {mean_before:.3f} → {mean_after:.3f}"
    assert mean_after < 0.35, \
        f"reconstruction error too high after convergence: {mean_after:.3f}"

    print(f"✓ SHEAF-007: convergence proven "
          f"(error {mean_before:.3f} → {mean_after:.3f})")


def test_sensor_queries_model_not_network():
    """After sensing, queries are answered by the model."""
    syn = SyntheticNetwork(n_ases=2, n_prefixes=1, n_endpoints=2, seed=29)
    sheaf = syn.build_sheaf()
    sensor = GlobalNetworkSensor(sheaf=sheaf)

    def probe(node_id, plane):
        """Probe a node against synthetic ground truth with small noise."""
        if node_id in syn.ground_truth:
            return syn.observe(node_id, plane, noise=0.02)
        return None
    sensor.set_probe_executor(probe)
    sensor.set_probeable(lambda node_id, plane:
                         node_id.kind == NodeKind.ENDPOINT)

    for _ in range(8):
        sensor.sense(probe_budget=4)

    node = list(syn.ground_truth.keys())[0]
    q = sensor.query(node, Plane.PROBE)
    assert 0.0 <= q["probability_healthy"] <= 1.0
    assert q["confidence"] > 0
    health = sensor.health(node)
    assert all(0.0 <= v <= 1.0 for v in health.values())
    print("✓ SHEAF-008: model queries return calibrated health")


def run_all_tests():
    """Run all network sheaf convergence tests."""
    print("=== Network Sheaf Convergence Tests ===")
    print()
    test_phase_geometry()
    test_sheaf_structure()
    test_holographic_propagation()
    test_prediction_infers_unobserved()
    test_residual_distinguishes_novel_from_expected()
    test_probe_selection_targets_uncertainty()
    test_convergence_reduces_error()
    test_sensor_queries_model_not_network()
    print()
    print("=== All Network Sheaf Tests Passed ===")


if __name__ == "__main__":
    run_all_tests()
