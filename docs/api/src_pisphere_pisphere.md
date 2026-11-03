# `src.pisphere.pisphere`

## `MeasurementResult`

> Result of a register measurement.

## `BellPair`

> A Bell-like temporal signature pair.

## `Pisphere`

> PISP-001: The Pisphere Register Lattice.
> 
> A recursive spherical architecture where each register is itself a
> complete sphere (pisphere) containing smaller spheres at every surface point.
> 
> Parameters:
>     base_radius: Base radius of the sphere (default: 1.0)
>     max_depth: Maximum recursion depth (default: 10)
>     branching_factor: Number of children per register (default: 4)
> 
> Spec: docs/spec/PISPHERE.md #PISP-001
> 
> Key Properties:
>     - Depth D has (B^(D+1) - 1) / (B - 1) total registers
>     - Default: B=4, depth=10 → 1,398,101 registers
>     - Each register stores quantum state as trigonometric temporal logic
