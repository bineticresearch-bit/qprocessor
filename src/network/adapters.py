"""
Public Channel Adapters
=======================

Each adapter is a **plane projection**: it converts a public channel's raw
output into `Observation` records in a single plane. All adapters are
read-only, rate-limited, and use only public data.

Adapters are pluggable and optional — the core never depends on any single
channel. Losing one plane degrades gracefully because the others constrain
it. This is the resilience property of the sheaf.

A `SyntheticNetwork` provides a ground-truth model so convergence can be
*proven* against a known answer — the critical validation step.

Spec Reference: docs/architecture/SheafFusion.md §5
"""

import math
import time
import random
import socket
import hashlib
from typing import Dict, List, Optional, Tuple, Callable

from .sheaf import Plane, NodeId, NodeKind, Observation, NetworkSheaf


# ============================================================
# Adapter interface
# ============================================================

class ChannelAdapter:
    """
    Base class for public channel adapters.

    A plane projection: raw public channel data → Observation records.
    Subclasses implement `poll()` which yields observations for the sheaf.
    """

    plane: Plane = Plane.PROBE

    def __init__(self, rate_limit_s: float = 1.0):
        self.rate_limit_s = rate_limit_s
        self._last_poll = 0.0
        self.observations_emitted = 0

    def poll(self, sheaf: NetworkSheaf) -> List[Observation]:
        """Collect observations from the channel. Rate-limited."""
        now = time.time()
        if now - self._last_poll < self.rate_limit_s:
            return []
        self._last_poll = now
        obs = self._collect(sheaf)
        self.observations_emitted += len(obs)
        return obs

    def _collect(self, sheaf: NetworkSheaf) -> List[Observation]:
        raise NotImplementedError

    def _phase_from(self, value: float, variance: float = 0.0) -> Tuple[float, float]:
        """
        Encode a measurement as a phase.

        θ encodes the primary measurement (normalized to [0, π]),
        φ encodes a secondary dimension (variance / spread).
        P(healthy) = cos²(θ/2), so θ=0 → healthy, θ=π → unhealthy.
        """
        theta = max(0.0, min(math.pi, value * math.pi))
        phi = max(0.0, min(2 * math.pi, variance * 2 * math.pi))
        return (theta, phi)


# ============================================================
# DNS Adapter — NAMING plane
# ============================================================

class DNSAdapter(ChannelAdapter):
    """
    NAMING plane: resolve hostnames and observe A/AAAA superposition.

    A dual-stack endpoint exists in superposition |IPv4⟩ + |IPv6⟩; the
    measurement collapses it. The phase encodes resolution health and
    the address-family balance.
    """

    plane = Plane.NAMING

    def __init__(self, hosts: List[str], rate_limit_s: float = 1.0,
                 resolver: Optional[Callable[[str], Dict]] = None):
        super().__init__(rate_limit_s)
        self.hosts = hosts
        # Injectable resolver for testing; defaults to real getaddrinfo
        self._resolver = resolver or self._default_resolve

    def _default_resolve(self, host: str) -> Dict:
        try:
            infos = socket.getaddrinfo(host, None, socket.AF_UNSPEC,
                                       socket.SOCK_STREAM)
            v4 = any(i[0] == socket.AF_INET for i in infos)
            v6 = any(i[0] == socket.AF_INET6 for i in infos)
            return {"ok": True, "v4": v4, "v6": v6, "count": len(infos)}
        except Exception:
            return {"ok": False, "v4": False, "v6": False, "count": 0}

    def _collect(self, sheaf: NetworkSheaf) -> List[Observation]:
        obs = []
        for host in self.hosts:
            result = self._resolver(host)
            node_id = NodeId(NodeKind.ENDPOINT, host)

            if not result["ok"]:
                phase = self._phase_from(1.0, 1.0)   # fully unhealthy
            else:
                # health from address-family coverage
                coverage = (int(result["v4"]) + int(result["v6"])) / 2.0
                health = 1.0 - coverage
                phase = self._phase_from(health, 1.0 / max(1, result["count"]))

            obs.append(Observation(
                node_id=node_id, plane=self.plane, phase=phase,
                confidence=0.8, source="dns", timestamp=time.time()
            ))
        return obs


# ============================================================
# Certificate Transparency Adapter — IDENTITY plane
# ============================================================

class CTAdapter(ChannelAdapter):
    """
    IDENTITY plane: observe certificate issuance activity.

    New certificates reveal new deployments before they are announced.
    The phase encodes issuance recency; a burst of new certs is a strong
    signal of new infrastructure.
    """

    plane = Plane.IDENTITY

    def __init__(self, domains: List[str], rate_limit_s: float = 1.0,
                 cert_feed: Optional[Callable[[str], Dict]] = None):
        super().__init__(rate_limit_s)
        self.domains = domains
        self._cert_feed = cert_feed

    def _collect(self, sheaf: NetworkSheaf) -> List[Observation]:
        obs = []
        for domain in self.domains:
            if self._cert_feed:
                info = self._cert_feed(domain)
            else:
                # Without a live CT log endpoint, emit no observation rather
                # than fabricate one. Real deployment wires this to a CT log.
                continue

            node_id = NodeId(NodeKind.ENDPOINT, domain)
            # recency: 0 = brand new, 1 = long-established
            recency = info.get("age_days", 365) / 365.0
            phase = self._phase_from(1.0 - min(1.0, recency),
                                     min(1.0, info.get("cert_count", 1) / 10.0))
            obs.append(Observation(
                node_id=node_id, plane=self.plane, phase=phase,
                confidence=0.9, source="ct", timestamp=time.time()
            ))
        return obs


# ============================================================
# RIPE Atlas Adapter — PROBE plane
# ============================================================

class AtlasAdapter(ChannelAdapter):
    """
    PROBE plane: active measurements from global vantage points.

    RIPE Atlas is the preferred active substrate — thousands of probes
    worldwide, with a public API and well-defined usage policies. The
    phase encodes latency and loss.
    """

    plane = Plane.PROBE

    def __init__(self, targets: List[str], rate_limit_s: float = 1.0,
                 measurement_fn: Optional[Callable[[str], Dict]] = None):
        super().__init__(rate_limit_s)
        self.targets = targets
        self._measurement_fn = measurement_fn

    def _collect(self, sheaf: NetworkSheaf) -> List[Observation]:
        obs = []
        for target in self.targets:
            if self._measurement_fn:
                m = self._measurement_fn(target)
            else:
                continue   # no live substrate; emit nothing

            node_id = NodeId(NodeKind.ENDPOINT, target)
            # latency normalized: 500ms+ = saturated unhealthy
            latency_norm = min(1.0, m.get("latency_ms", 500) / 500.0)
            loss = m.get("loss", 0.0)
            phase = self._phase_from(latency_norm, loss)
            obs.append(Observation(
                node_id=node_id, plane=self.plane, phase=phase,
                confidence=0.9, source="atlas", timestamp=time.time()
            ))
        return obs


# ============================================================
# BGP Adapter — CONTROL plane
# ============================================================

class BGPAdapter(ChannelAdapter):
    """
    CONTROL plane: routing state from public route collectors
    (RouteViews / RIPE RIS MRT dumps).

    The phase encodes route stability; withdrawals and instability map
    to unhealthy phases.
    """

    plane = Plane.CONTROL

    def __init__(self, prefixes: List[str], rate_limit_s: float = 1.0,
                 route_state_fn: Optional[Callable[[str], Dict]] = None):
        super().__init__(rate_limit_s)
        self.prefixes = prefixes
        self._route_state_fn = route_state_fn

    def _collect(self, sheaf: NetworkSheaf) -> List[Observation]:
        obs = []
        for prefix in self.prefixes:
            if self._route_state_fn:
                state = self._route_state_fn(prefix)
            else:
                continue

            node_id = NodeId(NodeKind.PREFIX, prefix)
            # stability: 1.0 = stable, 0.0 = heavy churn/withdrawn
            stability = state.get("stability", 1.0)
            announced = state.get("announced", True)
            health = stability if announced else 1.0
            phase = self._phase_from(1.0 - health, 1.0 - stability)
            obs.append(Observation(
                node_id=node_id, plane=self.plane, phase=phase,
                confidence=0.9, source="bgp", timestamp=time.time()
            ))
        return obs


# ============================================================
# GPS / GNSS Adapter — TIMING plane
# ============================================================

class GPSAdapter(ChannelAdapter):
    """
    TIMING plane: clock offsets from GNSS / NTP.

    Global clock synchronization reveals ionospheric events and
    infrastructure degradation. The phase encodes clock offset magnitude.
    """

    plane = Plane.TIMING

    def __init__(self, references: List[str], rate_limit_s: float = 1.0,
                 offset_fn: Optional[Callable[[str], Dict]] = None):
        super().__init__(rate_limit_s)
        self.references = references
        self._offset_fn = offset_fn

    def _collect(self, sheaf: NetworkSheaf) -> List[Observation]:
        obs = []
        for ref in self.references:
            if self._offset_fn:
                m = self._offset_fn(ref)
            else:
                continue

            node_id = NodeId(NodeKind.AUTONOMOUS_SYSTEM, ref)
            # offset normalized: 100ms+ = saturated
            offset_norm = min(1.0, abs(m.get("offset_ms", 0.0)) / 100.0)
            jitter = min(1.0, m.get("jitter_ms", 0.0) / 50.0)
            phase = self._phase_from(offset_norm, jitter)
            obs.append(Observation(
                node_id=node_id, plane=self.plane, phase=phase,
                confidence=0.85, source="gps", timestamp=time.time()
            ))
        return obs


# ============================================================
# Consensus Adapter — CONSENSUS plane
# ============================================================

class ConsensusAdapter(ChannelAdapter):
    """
    CONSENSUS plane: public blockchain header propagation.

    Block propagation delays are a tamper-evident global heartbeat —
    congestion and partition show up as propagation anomalies.
    """

    plane = Plane.CONSENSUS

    def __init__(self, chains: List[str], rate_limit_s: float = 1.0,
                 chain_fn: Optional[Callable[[str], Dict]] = None):
        super().__init__(rate_limit_s)
        self.chains = chains
        self._chain_fn = chain_fn

    def _collect(self, sheaf: NetworkSheaf) -> List[Observation]:
        obs = []
        for chain in self.chains:
            if self._chain_fn:
                m = self._chain_fn(chain)
            else:
                continue

            node_id = NodeId(NodeKind.ROOT, f"consensus:{chain}")
            # propagation delay normalized: 10s+ = saturated
            prop_norm = min(1.0, m.get("propagation_s", 0.0) / 10.0)
            phase = self._phase_from(prop_norm, m.get("miss_rate", 0.0))
            obs.append(Observation(
                node_id=node_id, plane=self.plane, phase=phase,
                confidence=0.9, source="consensus", timestamp=time.time()
            ))
        return obs


# ============================================================
# Synthetic ground-truth network — for proving convergence
# ============================================================

class SyntheticNetwork:
    """
    A ground-truth network with known structure and state.

    This is the validation substrate: the reconstructor must recover
    this network's state from sparse observations. If the model
    converges to the synthetic truth, the reconstruction loop works.

    Structure:
        root
        └── ASes (n_ases)
            └── prefixes (n_prefixes each)
                └── endpoints (n_endpoints each)
    """

    def __init__(self, n_ases: int = 4, n_prefixes: int = 3,
                 n_endpoints: int = 4, seed: int = 42):
        self.rng = random.Random(seed)
        self.ground_truth: Dict[NodeId, Dict[Plane, Tuple[float, float]]] = {}
        self.structure: Dict[NodeId, List[NodeId]] = {}

        root = NodeId(NodeKind.ROOT, "root")
        self.structure[root] = []

        for a in range(n_ases):
            asn = f"AS{10000 + a * 137}"
            as_node = NodeId(NodeKind.AUTONOMOUS_SYSTEM, asn)
            self.structure[root].append(as_node)
            self.structure[as_node] = []

            # Each AS has a characteristic health profile
            as_health = self.rng.uniform(0.1, 0.5)

            for p in range(n_prefixes):
                prefix = f"10.{a}.{p}.0/24"
                p_node = NodeId(NodeKind.PREFIX, prefix)
                self.structure[as_node].append(p_node)
                self.structure[p_node] = []

                for e in range(n_endpoints):
                    ip = f"10.{a}.{p}.{e + 1}"
                    e_node = NodeId(NodeKind.ENDPOINT, ip)
                    self.structure[p_node].append(e_node)

                    # Endpoint health clusters around its AS health
                    base = as_health + self.rng.gauss(0, 0.12)
                    base = max(0.0, min(1.0, base))

                    # Each plane observes the same truth with different noise
                    phases = {}
                    for plane in Plane:
                        noise = self.rng.gauss(0, 0.05)
                        val = max(0.0, min(1.0, base + noise))
                        phases[plane] = (val * math.pi, self.rng.random() * 0.3)
                    self.ground_truth[e_node] = phases

    def nodes(self) -> List[NodeId]:
        """All nodes in the synthetic network."""
        return list(self.ground_truth.keys())

    def observe(self, node_id: NodeId, plane: Plane,
                noise: float = 0.0) -> Observation:
        """Produce a (possibly noisy) observation of a node's true state."""
        truth = self.ground_truth[node_id][plane]
        if noise > 0:
            theta = truth[0] + self.rng.gauss(0, noise * math.pi)
            phi = truth[1] + self.rng.gauss(0, noise)
            theta = max(0.0, min(math.pi, theta))
            phi = max(0.0, min(2 * math.pi, phi))
        else:
            theta, phi = truth
        return Observation(
            node_id=node_id, plane=plane, phase=(theta, phi),
            confidence=0.9, source="synthetic", timestamp=time.time()
        )

    def sample_observations(self, fraction: float,
                            planes: Optional[List[Plane]] = None) -> List[Observation]:
        """
        Sample a fraction of the ground truth as observations.

        `fraction` = 1.0 observes everything; 0.1 observes 10%. This is
        the sparsity knob: the whole point is that the model should
        reconstruct the full network from a small fraction.
        """
        planes = planes or list(Plane)
        obs = []
        for node_id, phases in self.ground_truth.items():
            for plane in planes:
                if self.rng.random() < fraction:
                    obs.append(self.observe(node_id, plane))
        return obs

    def build_sheaf(self) -> NetworkSheaf:
        """Create a sheaf with the synthetic topology (no observations)."""
        sheaf = NetworkSheaf()
        for parent, children in self.structure.items():
            sheaf.add_node(parent)
            for child in children:
                sheaf.add_edge(parent, child)
        return sheaf

    def reconstruction_error(self, sheaf: NetworkSheaf) -> Dict[str, float]:
        """
        Mean error between the model and ground truth, per plane.

        This is the real proof: does the model's belief match the truth
        for nodes that were never directly observed?
        """
        errors: Dict[str, List[float]] = {p.value: [] for p in Plane}
        for node_id, truth in self.ground_truth.items():
            fiber = sheaf.get_fiber(node_id)
            if fiber is None:
                for p in Plane:
                    errors[p.value].append(1.0)
                continue
            for plane in Plane:
                predicted = fiber.get_phase(plane)
                if predicted is None:
                    errors[plane.value].append(1.0)
                else:
                    t = truth[plane]
                    d = abs(predicted[0] - t[0]) / math.pi
                    errors[plane.value].append(min(1.0, d))
        return {k: sum(v) / len(v) for k, v in errors.items() if v}
