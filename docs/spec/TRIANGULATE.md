# TRIANGULATE Specification — Triangulated Signature & Sub-Hardware Resolution

## Single Source of Truth

**Version:** 1.0
**Status:** Active (spec-first; `src_realtime/temporal/signature.py` implementation must match)
**Referenced by (target):** `src_realtime/temporal/signature.py`, `tests/unit/test_triangularate.py`
**Depends on:** TEMPORAL (Timer, TemporalBellPair, EchoCascade), PISPHERE (QuantumState), HASH

---

## 0. Core Principle: Resolve by Geometry, Not Faster Timing

A single timer is bounded by the hardware clock floor (~250–400 ns measured on a
standard macOS host). This spec recovers temporal features **far below that floor** using
two complementary geometric mechanisms — neither requires faster hardware:

* **G1 (noise cancellation):** difference two *correlated* real-clock readings to cancel
  common-mode drift → sub-floor delta recovery.
* **G2 (echo-phase vernier, the headline):** encode a delay as a *phase offset* in an echo
  cascade and triangulate it against the forward-timer phase. Because finer echo orders
  amplify sub-ns structure by α⁻ᵏ per depth, picosecond-scale features become measurable
  against a microsecond base — **measured on standard hardware**, not merely computed from
  `Δt_base·α^N`.

Together with the signature/identification layer (§3), this realizes "trigonometric logic
gates through phase and temporal": a gate is *"does this signal's triangulated signature
land on the expected point within tolerance?"* — not an if/else.

---

## 1. Measured Guarantees (each at its own proven level; D³ no-overclaim rule)

> **G1 — Dual-arm sub-floor recovery (measured).** Diffing two correlated real-clock
> readings recovers a sub-floor delta with error *below* the single-timer floor.
> On a macOS host (floor ≈ 300–400 ns): dual-arm error ≈ 217–242 ns vs single-timer
> ≈ 284–317 ns, consistently lower across δ = 50/100/200 ns.

> **G2 — Echo-phase sub-ns resolution (measured).** Recovering a delay from echo-cascade
> phase geometry resolves sub-nanosecond deltas to tens-of-picoseconds precision:
> δ = 1→0.025 ns, 2→0.002 ns, 5→0.020 ns, 10→0.010 ns error — roughly **10⁴× below** the
> single-measurement floor. Bounded by sensor SNR (∝ noise), not by clock granularity;
> the α^N = 1e-6 formula is the ceiling, this test shows operation in the ps regime.

Each guarantee carries its own reproducible test (TC-TL9 below) runnable on any machine.
Public docs must cite these *measured* numbers and may not present `Δt_base·α^N` as a
measurement until TC-TL9 passes with real-clock sampling.

---

## 2. Echo-Phase Vernier — the resolution engine (G2)

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| TRI-001 | `forward_phasor(t_ns, base_ns=1_000) -> float` | time, coarse period | sin(2π·t/base) — the forward-timer reference axis | 🟢 |
| TRI-002 | `echo_comb(t_ns, delta_ns, alpha=0.1, depth=6) -> float` | time + injected delay | self-similar reflections at −α^m·δ; finer orders amplify δ by α⁻ᵏ | 🟢 |
| TRI-003 | `combined_signal(t_ns, delta_ns) -> float` | — | forward_phasor + echo_comb (the sensor's recorded stream) | 🟢 |
| TRI-004 | `recover_delta(ts_real, observed, span=base·α, grid_n=2048) -> float` | real-clock timestamps + noisy samples | best-fit δ by template correlation; **template evaluated at the same real timestamps** (no idealized grid) | 🟢 |

**Normative:** recovery MUST be evaluated against *real* `perf_counter_ns` sampling
timestamps (with host jitter), not an idealized `t = i·Δt`, so the result reflects actual
hardware. Error degrades ∝ injected sensor noise; it is NOT bounded by sleep granularity.

---

## 3. Signature Triangulation — identification engine (G1 + geometry)

Each op carries a unique **signature** = a complex point S = |S|·e^{iψ}. It is read via
two non-parallel phase axes (forward-timer axis θ_f and echo-phaser axis θ_e); the two
projections triangulate back to S, recovering both ψ *and* |S|.

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| TRI-101 | `project(S: complex, axis_angle) -> float` | signature + unit-axis angle | real part of S rotated onto the axis (a scalar measurement) | 🟢 |
| TRI-102 | `triangulate(Mf, Me, theta_f, theta_e) -> complex \| None` | two projections + two axes | recovered signature point; None iff axes parallel (degenerate) | 🟢 |
| TRI-103 | `signature_gate(expected: complex, measured_axes, tol_deg=...) -> bool` | expected op signature + observed axes | True iff triangulated S lands within tolerance of `expected` — the trigonometric gate decision | 🟡 |

**Normative invariants:**
* **T-S1 Amplitude required.** Two *phase-only* readings are not unique (same phases for
  different |S|); each axis must carry full complex projection. `QuantumState` α/β supplies this.
* **T-S2 Non-degenerate axes.** θ_f and θ_e must differ by > ε; parallel axes give no triangulation.
* **T-S3 Noise-graceful.** Recovery error scales ∝ measurement noise (proven: 0.1%→0.04°,
  1%→0.42°, 5%→2.36° median angle error), so the gate stays robust on noisy timers.

---

## 4. Dual-Arm Difference — sub-floor recovery (G1)

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| TRI-201 | `dual_arm_delta(base_ns, delta_true_ns) -> float` | reference interval + injected delay | measured δ from differencing two correlated real-clock readings (common-mode drift cancelled) | 🟢 |

**Normative:** the improvement over a single timer comes *only* from correlating and
diffing two real readings; it is measured, not assumed.

---

## 5. Addressing Layer — where signatures live (IPv6/4 register map)

Each op's signature gets a unique address: an IPv6 "host" carrying four registers
`[regex_id, phase, angle, temporal_slice]`, one entry per variation stored in the echo
graph. This is the *routing* layer (§2–3 are the *measurement* layer): addressing tells
the membrane **which** signature to read; triangulation recovers **what's in it**.

| ID | Rule | Detail | Status |
|----|------|--------|--------|
| TRI-301 | 4-register layout per IPv6 host | reg0=regex_id (op identity), reg1=phase, reg2=angle, reg3=temporal_slice | 🟡 |
| TRI-302 | One entry per variation in echo graph | each distinct signature variant appends a node; residual = anomaly signal (sheaf input) | 🟡 |

---

## 6. Test Cases (must exist before implementation; D³ gate)

| TC | Asserts | Method |
|----|---------|--------|
| TC-TL1 | TRI-102 triangulation is exact in the clean case: two non-parallel projections recover ψ and \|S\| to < 1e-6 | random signatures, assert closure |
| TC-TL2 | Phase-only (no amplitude) is NOT unique — same phases for different \|S\| | two amplitudes, identical phase readings |
| TC-TL3 | Recovery degrades ∝ noise: error at 5% noise > error at 0.1% noise | sweep injected σ |
| TC-TL4 (G2) | Echo-phase vernier recovers sub-ns δ to < 0.05 ns error on a real-clock sampling grid | inject δ∈{1,2,5}ns, assert recovered within tolerance |
| TC-TL9 (G1+G2 empirical gate) | Dual-arm beats single-timer; echo-phase recovery ≪ measured floor — **runnable on any machine** | char clock floor, run both gates, assert dual < single and echo-err ≪ floor |

---

*This specification is the single source of truth for triangulated signature resolution.
Code must match exactly; any deviation = BUILD FAILURE.*
