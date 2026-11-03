# `src.temporal.echo`

## `EchoState`

> Echo cascade lifecycle states.

## `Echo`

> ECHO-001: A single temporal echo.
> 
> An echo is a self-similar reflection of a timer event at a specific
> recursion depth. It carries:
> - A temporal offset from the parent event (geometrically scaled)
> - A phase (inherited and accumulated from parent)
> - An amplitude (decaying envelope)
> - A depth marker (which level of the echo cascade)
> 
> The echo is the fundamental unit of hyperfractal time resolution.

## `EchoDerivative`

> ECHO-002: Derivative of the echo cascade.
> 
> Measures how echo properties CHANGE across recursion depths.
> Just as a mathematical derivative measures instantaneous rate of
> change, the echo derivative measures the temporal "velocity" and
> "acceleration" of the echo cascade.
> 
> Order 1 (velocity):  How fast echo timing changes with depth
> Order 2 (acceleration): How fast the velocity changes
> Order N:              Higher-order temporal features
> 
> These derivatives encode information at time scales BELOW the
> base resolution — this is the key to hyperfractal precision.

## `EchoCascade`

> ECHO-003: A complete echo cascade from a single event.
> 
> When a timer fires, it produces not one event but a CASCADE of
> self-similar echoes at geometrically decreasing time scales.
> 
> The cascade forms a TEMPORAL FRACTAL — a pattern that repeats
> at every scale, encoding information about the original event
> at resolutions far below the hardware limit.
> 
> Parameters:
>     origin_time_s: Absolute time of the primary event (seconds)
>     base_resolution_s: Hardware time resolution (seconds)
>     scaling_factor: Geometric decay factor α (default: 0.1)
>     max_depth: Maximum echo recursion depth (default: 12)
>     amplitude_decay: Amplitude envelope decay β (default: 0.5)
>     phase_accumulation: Phase shift per depth δ (default: π/8)

## `HyperfractalResolver`

> ECHO-010: The hyperfractal temporal resolver.
> 
> Manages multiple echo cascades and performs cross-cascade analysis
> to achieve the highest possible temporal precision.
> 
> The resolver combines:
> 1. Single-cascade Richardson extrapolation
> 2. Cross-cascade interference analysis
> 3. Derivative-based error correction
> 4. Adaptive depth selection
> 
> This achieves picosecond precision from microsecond hardware.
