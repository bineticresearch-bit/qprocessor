# Sheaf-Theoretic Network Fusion — Design Document

## Overview

A **meta-network** model: a live, converged representation of the global network built entirely from public observation planes. The network is not modeled as a flat graph but as a **sheaf** (fiber bundle) — each node carries a *fiber* of simultaneously-observed states across independent public channels, and measurements in any plane constrain predictions in every other plane.

The system reconstructs the global network from the **residual** — the part the current model fails to explain — using compressed-sensing style iterative absorption. Because the network is sparse and structured, the model converges to the full observable network without exhaustive scanning.

---

## 1. Mathematical Foundation

### 1.1 The Network as a Sheaf

Classical network modeling: a graph `G = (V, E)` — flat, discrete, single-plane.

Sheaf modeling: a **fiber bundle** `(E, π, X)` where:
- **Base space `X`** — the set of network nodes (endpoints, ASes, prefixes)
- **Fiber `F_x`** — the space of possible states of node `x`, one dimension per observation plane
- **Total space `E`** — the union of all fibers; where the model actually lives
- **Projection `π`** — retrieves the state of a node

A **section** `s: X → E` assigns a concrete state to every node. The model *is* a section; sensing *is* refining the section.

### 1.2 The Pisphere as Total Space

The pisphere register lattice is the natural instantiation of `E`:

- Each register at spherical coordinates `(depth, θ, φ)` = one network node
- **Depth** = hierarchy level (core → transit → edge → endpoint)
- **(θ, φ)** = position within the level (spatial/ topological embedding)
- **Register phase** = the fiber state, encoded as temporal phase

The non-avalanche hash makes the lattice a **metric space**: similar network states produce similar hashes, so geometric neighborhood = behavioral similarity. This is what enables holographic propagation.

### 1.3 Observation Planes

Each plane is a public channel that projects the same underlying truth in a different form:

| Plane | Channel | Fiber coordinate | Reveals |
|---|---|---|---|
| `CONTROL` | BGP (RouteViews, RIPE RIS) | reachability | topology, outages, hijacks |
| `NAMING` | DNS | resolution state | intent, infrastructure change |
| `IDENTITY` | Certificate Transparency | certificate state | new deployments pre-announcement |
| `PROBE` | RIPE Atlas | latency/loss | health, performance |
| `TIMING` | GPS / GNSS | clock offset | global sync, ionospheric events |
| `CONSENSUS` | Blockchain ledgers | propagation delay | tamper-evident global state |
| `BACKSCATTER` | Own sensors | retry/misdirection | adversarial activity |

**Key property:** planes are *independent* but *consistent* — they all observe the same underlying network. A cable cut shows up in PROBE latency, TIMING offsets, CONSENSUS propagation, and CONTROL withdrawals simultaneously. Cross-plane agreement is what makes the model trustworthy; cross-plane disagreement is exactly the anomaly signal.

---

## 2. Core Data Model

### 2.1 Node Identity

```python
@dataclass(frozen=True)
class NodeId:
    """A network node in the base space X."""
    kind: NodeKind            # ENDPOINT | AUTONOMOUS_SYSTEM | PREFIX | ROOT
    key: str                  # canonical identifier (IP, ASN, CIDR, "root")
```

Nodes form a hierarchy: `ROOT` → `AUTONOMOUS_SYSTEM` → `PREFIX` → `ENDPOINT`. Every endpoint belongs to a prefix, every prefix to an AS. This gives the model its coarse-to-fine structure — the same coarse-to-fine structure the pisphere's depth dimension provides.

### 2.2 The Fiber

```python
@dataclass
class Fiber:
    """The state of one node across all observation planes."""
    node_id: NodeId
    phase: Dict[Plane, Tuple[float, float]]   # (theta, phi) per plane
    confidence: Dict[Plane, float]            # per-plane certainty [0,1]
    last_observed: Dict[Plane, float]         # per-plane timestamp
    observations: int                         # total measurements absorbed
```

The phase `(θ, φ)` is the quantum-inspired encoding: `θ` encodes the plane's primary measurement (e.g. normalized latency), `φ` encodes a secondary dimension (e.g. variance). `P = cos²(θ/2)` gives a natural probability-of-health reading.

### 2.3 The Sheaf (Model)

```python
class NetworkSheaf:
    """The total space E — the living model of the network."""
    nodes: Dict[NodeId, Fiber]
    lattice: Pisphere            # geometric substrate
    adjacency: Dict[NodeId, Set[NodeId]]   # base-space topology
```

The sheaf holds the *current best section* — the model's belief about every node.

---

## 3. The Four Core Algorithms

### 3.1 Predict

```python
def predict(sheaf, node_id, plane) -> Tuple[float, float]:
    """Predict a node's phase in a plane from its neighborhood."""
```

For an unobserved `(node, plane)`, predict the phase by **weighted neighborhood interpolation** in the metric space: neighbors with high confidence in that plane pull the prediction toward their observed phase. Weights come from the non-avalanche similarity between node hashes — close in the lattice means behaviorally similar.

This is the mechanism that makes the network *knowable without measurement*: an endpoint never probed still has a predicted state, inferred from its AS, its prefix, and its behavioral neighbors.

### 3.2 Residual

```python
def residual(sheaf, obs: Observation) -> float:
    """How much an observation fails to be explained by the model."""
```

`r = |observed_phase − predicted_phase|`, normalized to `[0,1]`, weighted by observation confidence. **The residual is the only thing the system ever needs to measure.** It is simultaneously:
- The **information gain** of a measurement (how much the model will learn)
- The **anomaly score** of a measurement (how surprising the event is)

### 3.3 Absorb (Holographic Update)

```python
def absorb(sheaf, obs: Observation, strength: float):
    """Update the model from an observation, holographically."""
```

When an observation arrives:
1. **Direct update** — the node's fiber in that plane moves toward the observed phase, scaled by `strength` and the observation's own confidence.
2. **Holographic propagation** — the update radiates to the node's lattice neighborhood with strength decaying in non-avalanche similarity. Neighbors learn "something near you changed" without being measured.

This is the "a part reconstructs the whole" property: one measurement updates a *region*, not a point. The decay is governed by the same `α` similarity structure that makes the hash a metric.

### 3.4 Probe Selection (Active Inference)

```python
def select_probe(sheaf, budget: int) -> List[NodeId]:
    """Choose the measurements that will most reduce model uncertainty."""
```

Rank candidate `(node, plane)` pairs by **expected information gain** = predicted residual × uncertainty × staleness. Probe the top `budget`. This is active inference / Bayesian experimental design: the system *chooses what to look at next* rather than scanning blindly. As the model converges, the selected probes naturally migrate from broad exploration to the shrinking set of genuinely unknown regions and to the frontiers of active change.

---

## 4. The Reconstruction Loop

```
                    ┌──────────────────────────────┐
                    │      Public Channels         │
                    │  BGP · DNS · CT · Atlas ·    │
                    │  GPS · Consensus · Backscatter│
                    └──────────────┬───────────────┘
                                   │ observations
                                   ▼
   ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
   │   PREDICT    │◄───────│   ABSORB     │───────▶│   RESIDUAL   │
   │ (neighborhood│        │ (holographic │        │ (information │
   │  inference)  │        │  propagation)│        │  gain)       │
   └──────────────┘        └──────────────┘        └──────┬───────┘
          ▲                                                 │
          │                                                 ▼
          │                                        ┌──────────────┐
          └────────────────────────────────────────│ SELECT PROBE │
                model update                       │ (active      │
                                                   │  inference)  │
                                                   └──────────────┘
```

**Convergence:** as the model absorbs measurements, residuals shrink toward noise. Total residual energy over the lattice is the convergence metric — when it stops decreasing, the model *is* the network (the observable part of it).

---

## 5. Public Channel Adapters

Each adapter is a **plane projection** — it converts a public channel's raw output into `Observation` records in a single plane. All adapters are read-only, rate-limited, and use only public data.

| Adapter | Source | Plane | Notes |
|---|---|---|---|
| `BGPAdapter` | RouteViews / RIPE RIS MRT dumps | CONTROL | public route collectors |
| `DNSAdapter` | standard resolution | NAMING | A/AAAA superposition, TTL |
| `CTAdapter` | Certificate Transparency logs | IDENTITY | new-cert observations |
| `AtlasAdapter` | RIPE Atlas API | PROBE | active measurements |
| `GPSAdapter` | GNSS timing receiver / NTP | TIMING | clock offsets |
| `ConsensusAdapter` | public blockchain headers | CONSENSUS | block propagation |

Adapters are **pluggable and optional**. The core never depends on any single channel — losing one plane degrades gracefully because the others constrain it. This is the resilience property of the sheaf.

For local development and testing, a `SyntheticNetwork` generates a ground-truth network so convergence can be *proven* against a known answer — the critical validation step.

---

## 6. Why This Is a Paradigm Shift

1. **From scanning to inference.** The model knows the network without measuring it, because sparsity + structure make it compressible.
2. **From single-channel to cross-plane.** Every plane corrects the others' blind spots; agreement is trust, disagreement is anomaly.
3. **From snapshot to living model.** The residual loop keeps the model converged as the network changes underneath it.
4. **From tool to substrate.** Once converged, every network task (reachability, performance, security, routing) becomes a *query to the model*.

## 7. Honest Scope

- Covers the **observable** network. Dark space / private infrastructure is outside the horizon.
- Probing is rate-limited and respectful by construction; RIPE Atlas is the preferred active substrate.
- This is a network observability and inference system — a frontier capability, not AGI.
