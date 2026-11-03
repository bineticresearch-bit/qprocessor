# `src.pisphere.register`

## `Register`

> PISP-009: A single register in the pisphere lattice.
> 
> Each register stores:
> - id: Unique identifier
> - depth: Depth in the pisphere hierarchy (0 = root)
> - theta: Polar angle in spherical coordinates [0, π]
> - phi: Azimuthal angle in spherical coordinates [0, 2π)
> - value: Current quantum state value (complex amplitude)
> - phase: Current phase (θ, φ) as tuple
> 
> Spec: docs/spec/PISPHERE.md #PISP-009
