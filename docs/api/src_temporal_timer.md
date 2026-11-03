# `src.temporal.timer`

## `TimerState`

> Timer lifecycle states.

## `TimerExpiryEvent`

> Event produced when a timer expires.

## `Timer`

> TEMP-008: A recursive temporal timer.
> 
> Each timer represents a temporal qubit. Its state is defined by:
> - target_time: When it expires (measurement event)
> - phase: (theta, phi) defining quantum state
> - amplitude: Complex amplitude cos(θ/2) + e^(iφ)·sin(θ/2)
> - depth: Recursion depth (0 = root)
> - children: Child timers created by branching
> - echo_cascade: Hyperfractal echo cascade for picosecond precision
> 
> Spec: docs/spec/TEMPORAL.md #TEMP-008
