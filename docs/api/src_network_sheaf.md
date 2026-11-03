# `src.network.sheaf`

## `Plane`

> A public observation channel.
> 
> Each plane projects the same underlying network truth in a different
> form. Planes are independent but consistent: they all observe the same
> network, so cross-plane agreement is trust and cross-plane disagreement
> is exactly the anomaly signal.

## `NodeKind`

> Hierarchy level of a network node.

## `NodeId`

> A network node in the base space X.
> 
> Nodes form a hierarchy: ROOT → AUTONOMOUS_SYSTEM → PREFIX → ENDPOINT.
> This gives the model its coarse-to-fine structure, mirroring the
> pisphere's depth dimension.

## `Fiber`

> The state of one node across all observation planes.
> 
> The phase (θ, φ) is the quantum-inspired encoding of a plane's
> measurement:
>     θ  encodes the primary measurement  (e.g. normalized latency)
>     φ  encodes a secondary dimension    (e.g. variance)
>     P(healthy) = cos²(θ/2)
> 
> Confidence is per-plane certainty in [0, 1]; it decays with staleness
> and rises with each absorbed observation.

## `Observation`

> A single measurement of one node in one plane.
> 
> This is the atom of the whole system: every public channel adapter
> converts its raw output into Observation records.

## `NetworkSheaf`

> The total space E — the living model of the network.
> 
> Holds the current best section: the model's belief about every node
> in every plane. Provides:
> 
>   - node identity and hierarchy
>   - base-space topology (adjacency)
>   - the metric structure (via non-avalanche similarity) that makes
>     geometric neighborhood mean behavioral similarity
