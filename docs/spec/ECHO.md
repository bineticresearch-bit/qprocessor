# ECHO Specification — Hyperfractal Echo Precision

## Single Source of Truth

**Version:** 1.0
**Status:** Active
**Referenced by:** `src/temporal/engine.py`, `src/temporal/echo.py`,
`src/temporal/timer.py`, `src_realtime/temporal/*`

---

## 1. Core Principle

A timer event does not produce a single point in time — it produces a
**cascade of echoes** at geometrically decreasing intervals. Each echo is a
self-similar replica of the original event, scaled by factor α.

By analyzing the **interference pattern** of these echoes and computing their
**derivatives** (rates of change across recursion depths), temporal features
far below the base hardware resolution can be resolved.

This is a **temporal vernier caliper**: just as a vernier achieves
sub-millimeter precision using only millimeter markings, the echo cascade
achieves picosecond precision from microsecond-scale hardware.

### Mathematical Foundation

```
Echo at depth k:
    Δt_k = Δt_0 × α^k          (geometric temporal decay)
    A_k  = A_0 × β^k           (amplitude envelope)
    φ_k  = φ_0 + k·δ           (phase accumulation)

Echo derivative (finite difference across depths):
    d^(1)_k = (E_{k+1} - E_k) / (Δt_{k+1} - Δt_k)
    d^(n)_k = (d^(n-1)_{k+1} - d^(n-1)_k) / (Δt_{k+1} - Δt_k)

Hyperfractal resolution (Richardson extrapolation):
    Δt_effective = Δt_base × α^N
```

For α = 0.1, N = 6:  1μs × 10⁻⁶ = 1ps.

---

## 2. Specification Index

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| ECHO-001 | `class Echo` | depth, temporal_offset, phase, amplitude, parent_id | Echo | 🟢 |
| ECHO-002 | `class EchoDerivative` | order, depth, value, temporal_scale | EchoDerivative | 🟢 |
| ECHO-003 | `class EchoCascade` | origin_time, base_resolution, scaling_factor, max_depth | EchoCascade | 🟢 |
| ECHO-004 | `EchoCascade.effective_resolution_s` | none | float (property) | 🟢 |
| ECHO-005 | `EchoCascade.emit(initial_phase, initial_amplitude)` | phase, amplitude | EchoCascade | 🟢 |
| ECHO-006 | `EchoCascade.compute_derivatives(max_order)` | max_order | List[EchoDerivative] | 🟢 |
| ECHO-007 | `EchoCascade.resolve_hyperfractal()` | none | (time, precision) | 🟢 |
| ECHO-008 | `class HyperfractalResolver` | base_resolution, scaling_factor, max_depth | HyperfractalResolver | 🟢 |
| ECHO-009 | `HyperfractalResolver.emit_event(time_s, phase)` | time, phase | EchoCascade | 🟢 |
| ECHO-010 | `HyperfractalResolver.resolve_event(cascade)` | cascade | (time, precision) | 🟢 |
| ECHO-011 | `HyperfractalResolver.precision_report()` | none | Dict | 🟢 |
| ECHO-012 | `Timer.emit_echo(max_depth)` | max_depth | EchoCascade | 🟢 |

**Legend:** 🟢 = specified, implemented, tested

---

## 3. Key Properties

- **Pure software technique** — no hardware changes required
- **Exponential precision improvement** — `Δt_base × α^N`
- **Self-similar fractal structure in time** — the cascade repeats at every scale
- **Derivatives encode sub-resolution information** — the Nth derivative
  resolves features at scale `Δt_base × α^N`

### Precision by depth (α = 0.1, base = 1μs)

| Depth | Resolution | Scale |
|-------|-----------|-------|
| 0 | 1 μs | microsecond |
| 3 | 1 ns | nanosecond |
| 6 | 1 ps | picosecond |
| 9 | 1 fs | femtosecond |
| 12 | 1 as | attosecond |

---

## 4. Test Cases

- **TC1:** Same cascade parameters → same effective resolution (deterministic)
- **TC2:** `effective_resolution_s = base_resolution_s × α^max_depth`
- **TC3:** Echo count scales with `max_depth`
- **TC4:** Derivative order N resolves features at `Δt_base × α^N`
- **TC5:** Resolved precision ≤ theoretical precision

---

## 5. Realtime Variant

`src_realtime/temporal/echo.py` implements the same specification with
nanosecond-anchored timing using `time.perf_counter_ns()`. Sub-nanosecond
offsets are tracked as floating-point fractions of a nanosecond, and measured
arrival times support jitter analysis.
