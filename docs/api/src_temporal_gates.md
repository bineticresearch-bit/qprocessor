# `src.temporal.gates`

## `GateType`

> Quantum gate types and their temporal equivalents.

## `TemporalGate`

> TEMP-011: A temporal quantum gate.
> 
> Each gate is defined by its type and parameters. When applied to timers,
> the gate modifies their phase, amplitude, or branching structure.
> 
> Parameters:
>     gate_type: Type of gate (GateType enum)
>     params: Gate-specific parameters
> 
> Spec: docs/spec/TEMPORAL.md #TEMP-011
