# `src.temporal.engine`

## `SyncResult`

> Result of timer synchronization.

## `TemporalMeasurement`

> Result of temporal measurement.

## `EchoResolutionResult`

> Result of resolving all timers via echo cascades.

## `TemporalEngine`

> TEMP-001: Temporal computation engine.
> 
> Manages a collection of timers and provides quantum gate operations
> in the temporal domain. Time IS the computation.
> 
> Now with ECHO INTEGRATION for hyperfractal picosecond precision.
> 
> Parameters:
>     resolution_us: Timer resolution in microseconds (default: 1)
>     max_timers: Maximum number of concurrent timers (default: 10000)
>     echo_enabled: Enable echo cascade by default (default: True)
>     echo_depth: Default echo cascade depth (default: 6 → 1ps)
> 
> Spec: docs/spec/TEMPORAL.md #TEMP-001
