# `src.network.fusion`

## `phase_distance`

> Distance between two phases in [0, 1].
> 
> θ is circular on [0, 2π) so we take the shorter arc; φ is treated
> linearly. The result is normalized so 1.0 = maximally different.

## `lerp_phase`

> Linear interpolation between two phases, t in [0, 1].

## `predict`

> Predict a node's phase in a plane from its neighborhood.
> 
> Weighted interpolation over neighbors that have real observations in
> this plane. Weights come from non-avalanche similarity — close in the
> lattice means behaviorally similar.
> 
> This is the mechanism that makes the network knowable *without*
> measurement: an endpoint never probed still has a predicted state,
> inferred from its AS, its prefix, and its behavioral neighbors.
> 
> Returns None if no neighbor has been observed in this plane.

## `prediction_confidence`

> Confidence in the prediction for (node, plane), in [0, 1].
> 
> Combines the node's own uncertainty with the strength of the
> neighborhood evidence supporting the prediction.

## `residual`

> How much an observation fails to be explained by the model.
> 
> r = |observed_phase − predicted_phase|, normalized to [0, 1] and
> weighted by the observation's own confidence.
> 
> The residual is simultaneously:
>   - the INFORMATION GAIN of the measurement (how much the model learns)
>   - the ANOMALY SCORE of the measurement (how surprising the event is)

## `HolographicUpdater`

> Updates the model from observations, holographically.
> 
> When an observation arrives:
>   1. DIRECT UPDATE — the node's fiber in that plane moves toward the
>      observed phase, scaled by strength and observation confidence.
>   2. HOLOGRAPHIC PROPAGATION — the update radiates to the node's
>      lattice neighborhood with strength decaying in non-avalanche
>      similarity. Neighbors learn "something near you changed" without
>      being measured.
> 
> This is the "a part reconstructs the whole" property: one measurement
> updates a region, not a point.

## `select_probes`

> Choose the measurements that will most reduce model uncertainty.
> 
> Ranks candidate (node, plane) cells by expected information gain:
> 
>     gain = uncertainty × (1 − prediction_confidence) × staleness
> 
> and returns the top `budget`. This is active inference / Bayesian
> experimental design: the system chooses what to look at next rather
> than scanning blindly.
> 
> `probeable` is an optional predicate (node_id, plane) → bool. When
> given, only cells the probe substrate can actually measure are
> ranked. This matters: aggregate nodes (root, AS) often carry the
> highest uncertainty but cannot be probed directly — ranking them
> first would waste every probe budget. The predicate keeps selection
> honest about what the substrate can do.
> 
> As the model converges, selected probes naturally migrate from broad
> exploration to the shrinking set of genuinely unknown regions and to
> the frontiers of active change.

## `ResidualReconstructor`

> Drives the model toward convergence.
> 
> Each step:
>   1. Receive observations from public channels (or probes)
>   2. Measure residuals — what does the model fail to explain?
>   3. Absorb the residuals holographically
>   4. Select the next probes by maximum expected information gain
> 
> Convergence is tracked as total residual energy over the lattice.
