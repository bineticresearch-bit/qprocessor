"""
Network Sheaf — Core Data Model
================================

The network modeled as a sheaf (fiber bundle) rather than a flat graph.

Mathematical structure:
    (E, π, X) where
        X  = base space  = set of network nodes (endpoints, ASes, prefixes)
        F  = fiber       = space of states, one dimension per observation plane
        E  = total space = union of all fibers; where the model lives
        π  = projection  = retrieves the state of a node

The pisphere register lattice provides the geometric substrate: each register
at (depth, θ, φ) is one network node, and the non-avalanche hash makes the
lattice a metric space (similar network states → similar hashes), so geometric
neighborhood = behavioral similarity. This is what enables holographic
propagation: one measurement updates a region, not a point.

Spec Reference: docs/architecture/SheafFusion.md
"""

import math
import time
import hashlib
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..hash.non_avalanche import non_avalanche_hash, compute_similarity


# ============================================================
# Observation Planes
# ============================================================

class Plane(Enum):
    """
    A public observation channel.

    Each plane projects the same underlying network truth in a different
    form. Planes are independent but consistent: they all observe the same
    network, so cross-plane agreement is trust and cross-plane disagreement
    is exactly the anomaly signal.
    """
    CONTROL = "control"          # BGP — topology, outages, hijacks
    NAMING = "naming"            # DNS — intent, infrastructure change
    IDENTITY = "identity"        # Certificate Transparency — new deployments
    PROBE = "probe"              # RIPE Atlas — latency, loss, health
    TIMING = "timing"            # GPS/GNSS — clock offsets, ionospheric events
    CONSENSUS = "consensus"      # Blockchain — propagation, tamper-evident state
    BACKSCATTER = "backscatter"  # own sensors — retry storms, misdirection


# ============================================================
# Node Identity (Base Space X)
# ============================================================

class NodeKind(Enum):
    """Hierarchy level of a network node."""
    ROOT = "root"                        # the whole network
    AUTONOMOUS_SYSTEM = "autonomous_system"
    PREFIX = "prefix"
    ENDPOINT = "endpoint"


@dataclass(frozen=True)
class NodeId:
    """
    A network node in the base space X.

    Nodes form a hierarchy: ROOT → AUTONOMOUS_SYSTEM → PREFIX → ENDPOINT.
    This gives the model its coarse-to-fine structure, mirroring the
    pisphere's depth dimension.
    """
    kind: NodeKind
    key: str

    def __repr__(self) -> str:
        return f"{self.kind.value}:{self.key}"


# ============================================================
# The Fiber
# ============================================================

@dataclass
class Fiber:
    """
    The state of one node across all observation planes.

    The phase (θ, φ) is the quantum-inspired encoding of a plane's
    measurement:
        θ  encodes the primary measurement  (e.g. normalized latency)
        φ  encodes a secondary dimension    (e.g. variance)
        P(healthy) = cos²(θ/2)

    Confidence is per-plane certainty in [0, 1]; it decays with staleness
    and rises with each absorbed observation.
    """
    node_id: NodeId
    phase: Dict[Plane, Tuple[float, float]] = field(default_factory=dict)
    confidence: Dict[Plane, float] = field(default_factory=dict)
    last_observed: Dict[Plane, float] = field(default_factory=dict)
    observations: int = 0

    # ---- accessors ------------------------------------------------

    def get_phase(self, plane: Plane) -> Optional[Tuple[float, float]]:
        return self.phase.get(plane)

    def get_confidence(self, plane: Plane) -> float:
        return self.confidence.get(plane, 0.0)

    def staleness(self, plane: Plane, now: Optional[float] = None) -> float:
        """Seconds since last observation in this plane (0 if never)."""
        t = self.last_observed.get(plane)
        if t is None:
            return float("inf")
        return (now if now is not None else time.time()) - t

    def probability_healthy(self, plane: Plane) -> float:
        """P(healthy) = cos²(θ/2) — natural probability reading."""
        ph = self.phase.get(plane)
        if ph is None:
            return 0.5
        return math.cos(ph[0] / 2.0) ** 2

    def uncertainty(self, plane: Plane, now: Optional[float] = None) -> float:
        """
        How little the model knows about (node, plane), in [0, 1].

        Combines low confidence with staleness. 1.0 = total ignorance.
        """
        conf = self.get_confidence(plane)
        stal = self.staleness(plane, now)
        # staleness half-life of 3600s: an hour-old observation is worth half
        staleness_factor = 1.0 if stal == float("inf") else (stal / (stal + 3600.0))
        return (1.0 - conf) * (0.5 + 0.5 * staleness_factor)

    def observe(self, plane: Plane, phase: Tuple[float, float],
                confidence: float, now: Optional[float] = None):
        """Record a direct observation in one plane."""
        now = now if now is not None else time.time()
        self.phase[plane] = phase
        self.confidence[plane] = max(0.0, min(1.0, confidence))
        self.last_observed[plane] = now
        self.observations += 1


# ============================================================
# Observations
# ============================================================

@dataclass
class Observation:
    """
    A single measurement of one node in one plane.

    This is the atom of the whole system: every public channel adapter
    converts its raw output into Observation records.
    """
    node_id: NodeId
    plane: Plane
    phase: Tuple[float, float]       # observed (θ, φ)
    confidence: float = 1.0          # reliability of the channel reading
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"          # which adapter produced it

    def __repr__(self) -> str:
        return (f"Obs({self.node_id}, {self.plane.value}, "
                f"θ={self.phase[0]:.3f}, φ={self.phase[1]:.3f}, "
                f"conf={self.confidence:.2f})")


# ============================================================
# The Sheaf (Total Space E)
# ============================================================

class NetworkSheaf:
    """
    The total space E — the living model of the network.

    Holds the current best section: the model's belief about every node
    in every plane. Provides:

      - node identity and hierarchy
      - base-space topology (adjacency)
      - the metric structure (via non-avalanche similarity) that makes
        geometric neighborhood mean behavioral similarity
    """

    def __init__(self):
        self.nodes: Dict[NodeId, Fiber] = {}
        self.adjacency: Dict[NodeId, Set[NodeId]] = {}

        # Node hash cache — the metric-space embedding
        self._hash_cache: Dict[NodeId, bytes] = {}

        # Root node always exists
        self._root = NodeId(NodeKind.ROOT, "root")
        self.add_node(self._root)

    # ---- structure --------------------------------------------------

    @property
    def root(self) -> NodeId:
        return self._root

    def add_node(self, node_id: NodeId) -> Fiber:
        """Register a node; return its fiber."""
        if node_id not in self.nodes:
            self.nodes[node_id] = Fiber(node_id=node_id)
            self.adjacency[node_id] = set()
            self._hash_cache[node_id] = self._node_hash(node_id)
        return self.nodes[node_id]

    def add_edge(self, a: NodeId, b: NodeId):
        """Declare two nodes adjacent in the base space."""
        self.add_node(a)
        self.add_node(b)
        self.adjacency[a].add(b)
        self.adjacency[b].add(a)

    def get_fiber(self, node_id: NodeId) -> Optional[Fiber]:
        return self.nodes.get(node_id)

    def neighbors(self, node_id: NodeId) -> Set[NodeId]:
        return self.adjacency.get(node_id, set())

    # ---- the metric structure ---------------------------------------

    def _node_hash(self, node_id: NodeId) -> bytes:
        """
        Embed a node into the metric space.

        The hash is built from the node's identity *and its topological
        context*, so nodes that share context land close together in the
        metric space. This is what makes neighborhood inference work.
        """
        h = hashlib.sha256(f"{node_id.kind.value}|{node_id.key}".encode()).digest()
        return h

    def similarity(self, a: NodeId, b: NodeId) -> float:
        """
        Behavioral similarity between two nodes in [0, 1].

        Combines the non-avalanche hash similarity (identity/context
        closeness) with base-space adjacency. Adjacent nodes are always
        highly similar; non-adjacent nodes are similar to the degree their
        identities resemble each other.
        """
        if a == b:
            return 1.0
        ha = self._hash_cache.get(a) or self._node_hash(a)
        hb = self._hash_cache.get(b) or self._node_hash(b)
        sim = compute_similarity(ha, hb)
        if b in self.adjacency.get(a, set()):
            sim = max(sim, 0.9)
        return sim

    def neighborhood(self, node_id: NodeId, max_size: int = 8) -> List[NodeId]:
        """
        The most behaviorally-similar nodes to `node_id`.

        Adjacency first (topological locality), then metric-space closeness.
        """
        candidates = [n for n in self.nodes if n != node_id]
        if not candidates:
            return []
        candidates.sort(key=lambda n: self.similarity(node_id, n), reverse=True)
        return candidates[:max_size]

    # ---- model-level queries ----------------------------------------

    def total_residual_energy(self) -> float:
        """
        Sum of per-node ignorance across the sheaf.

        This is the convergence metric: as the model absorbs measurements,
        it shrinks toward zero. When it stops decreasing, the model *is*
        the (observable) network.
        """
        energy = 0.0
        for fiber in self.nodes.values():
            for plane in Plane:
                energy += fiber.uncertainty(plane)
        return energy

    def coverage(self) -> Dict[str, float]:
        """Fraction of (node, plane) cells with real observations."""
        total = len(self.nodes) * len(Plane)
        if total == 0:
            return {"coverage": 0.0}
        observed = sum(
            1 for f in self.nodes.values()
            for p in Plane
            if f.get_confidence(p) > 0.0
        )
        return {"coverage": observed / total, "cells": total, "observed": observed}

    def __repr__(self) -> str:
        return (f"NetworkSheaf(nodes={len(self.nodes)}, "
                f"edges={sum(len(v) for v in self.adjacency.values()) // 2}, "
                f"residual_energy={self.total_residual_energy():.2f})")
