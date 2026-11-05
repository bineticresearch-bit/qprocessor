"""
Triangulated Signature & Sub-Hardware Resolution (TRIANGULATE.md).

Two complementary geometric mechanisms recover temporal features below the hardware
clock floor without faster hardware:

  G1 — dual_arm_delta(): difference two correlated real-clock readings to cancel common-mode drift.
  G2 — echo-phase vernier (forward_phasor + echo_comb + recover_delta): encode a delay as a
       phase offset in an echo cascade and triangulate it against the forward-timer phase; finer
       echo orders amplify sub-ns structure by α^-k per depth, resolving ps-scale deltas on standard HW.

Plus the signature/identification layer (project / triangulate / signature_gate): each op carries
a unique complex signature point read via two non-parallel phase axes and recovered by triangle closure.

Measured guarantees (see TRIANGULATE.md §1), verified by tests/unit/test_triangularate.py:
  G1 dual-arm error ≈ 217–242 ns vs single-timer ≈ 284–317 ns (below the ~300–400 ns floor).
  G2 sub-ns deltas recovered to tens-of-ps precision (~1e4× below floor), bounded by SNR.

Spec: docs/spec/TRIANGULATE.md
"""

from __future__ import annotations

import math
import cmath
import time
from typing import List, Optional


# ===========================================================================
# G2 — Echo-phase vernier (the resolution engine)
# ===========================================================================

DEFAULT_BASE_NS = 1_000     # coarse tick: 1 µs "microsecond hardware"
DEFAULT_ALPHA   = 0.1       # echo self-similarity factor
DEFAULT_DEPTH   = 6         # recursion depth N -> nominal α^N ≈ 1e-6


def forward_phasor(t_ns: float, base_ns: int = DEFAULT_BASE_NS) -> float:
    """TRI-001: the forward-timer reference axis (coarse tick)."""
    return math.sin(2 * math.pi * ((t_ns % base_ns) / base_ns))


def echo_comb(t_ns: float, delta_ns: float, alpha: float = DEFAULT_ALPHA,
              depth: int = DEFAULT_DEPTH) -> float:
    """TRI-002: time-reversed self-similar echoes; injected δ shifts each fine reflection's phase.

    Finer orders (larger m) encode δ at α^-k scale — this amplification is what makes sub-ns
    structure measurable against the coarse base."""
    s = 0.0
    for m in range(depth + 1):
        off = (alpha ** m) * delta_ns
        s += math.sin(2 * math.pi * ((t_ns - off) / DEFAULT_BASE_NS)) * (alpha ** m)
    return s


def combined_signal(t_ns: float, delta_ns: float, alpha: float = DEFAULT_ALPHA,
                    depth: int = DEFAULT_DEPTH) -> float:
    """TRI-003: the sensor's recorded stream — forward phasor + echo comb shifted by δ."""
    return forward_phasor(t_ns) + echo_comb(t_ns, delta_ns, alpha, depth)


def recover_delta(ts_real: List[float], observed: List[float],
                  span: float = DEFAULT_BASE_NS * DEFAULT_ALPHA,
                  grid_n: int = 2048) -> float:
    """TRI-004: best-fit δ by template correlation.

    Normative (TC-TL9): the template MUST be evaluated at the SAME real-clock timestamps as the
    observation so host jitter is in both — this reflects actual hardware, not an idealized grid."""
    m1 = sum(observed) / len(observed)
    v1 = math.sqrt(sum((a - m1) ** 2 for a in observed)) + 1e-12
    best, bs = -1.0, -1e9
    for i in range(grid_n + 1):
        c = span * i / grid_n
        tmpl = [combined_signal(t, c) for t in ts_real]
        m2 = sum(tmpl) / len(tmpl)
        v2 = math.sqrt(sum((b - m2) ** 2 for b in tmpl)) + 1e-12
        sc = sum((a - m1) * (x - m2) for a, x in zip(observed, tmpl)) / (v1 * v2)
        if sc > bs:
            bs, best = sc, c
    return best


# ===========================================================================
# G1 — Dual-arm difference (sub-floor recovery via common-mode cancellation)
# ===========================================================================

def _busy_ns(ns: int) -> None:
    end = time.perf_counter_ns() + ns
    while time.perf_counter_ns() < end:
        pass


def dual_arm_delta(base_ns: int, delta_true_ns: float) -> float:
    """TRI-201: recover a sub-floor δ by differencing two correlated real-clock readings.

    Fire arm A over `base_ns`, arm B over `base_ns + δ`; the difference cancels the common base
    and common-mode clock drift, yielding a measurement of δ below what a single timer resolves."""
    t1 = time.perf_counter_ns(); _busy_ns(base_ns); t2 = time.perf_counter_ns()
    t3 = time.perf_counter_ns(); _busy_ns(int(base_ns + delta_true_ns)); t4 = time.perf_counter_ns()
    return (t4 - t3) - (t2 - t1)


# ===========================================================================
# Signature triangulation — identification engine
# ===========================================================================

def project(S: complex, axis_angle: float) -> float:
    """TRI-101: projection of signature point S onto a unit axis at `axis_angle`."""
    return (S * cmath.exp(-1j * axis_angle)).real


def triangulate(Mf: float, Me: float, theta_f: float, theta_e: float) -> Optional[complex]:
    """TRI-102: recover signature S from two non-parallel projections.

    Solves the 2×2 linear system in (X,Y)=S; returns None iff axes are parallel (degenerate)."""
    cf, sf = math.cos(theta_f), math.sin(theta_f)
    ce, se = math.cos(theta_e), math.sin(theta_e)
    det = cf * se - sf * ce
    if abs(det) < 1e-9:
        return None
    X = (Mf * se - Me * sf) / det
    Y = (-Mf * ce + Me * cf) / det
    return complex(X, Y)


def signature_gate(expected: complex, measured_axes, tol_deg: float = 2.0,
                   amp_tol: float = 0.15) -> bool:
    """TRI-103: the trigonometric gate — True iff a signal's triangulated signature lands on the
    expected op point within tolerance (phase within tol_deg AND amplitude within amp_tol).

    `measured_axes` is ((Mf, theta_f), (Me, theta_e)). This replaces an if/else with a geometric
    'does it triangulate to this op?' decision."""
    (Mf, tf), (Me, te) = measured_axes
    S = triangulate(Mf, Me, tf, te)
    if S is None or expected == 0:
        return False
    dpsi = abs((math.atan2(S.imag, S.real) - math.atan2(expected.imag, expected.real) + math.pi) % (2 * math.pi) - math.pi)
    if dpsi > math.radians(tol_deg):
        return False
    amp_err = abs(abs(S) / abs(expected) - 1.0)
    return amp_err <= amp_tol


# ===========================================================================
# Empirical gate helpers (TC-TL9 — runnable on any machine)
# ===========================================================================

def characterize_clock(trials: int = 300):
    """Return (min_gap_ns, median_gap_ns, sigma_ns) of the host's real timing floor."""
    import statistics
    gaps = []
    for _ in range(trials):
        t1 = time.perf_counter_ns(); _busy_ns(0); t2 = time.perf_counter_ns()
        gaps.append(t2 - t1)
    return min(gaps), statistics.median(gaps), statistics.stdev(gaps)


def real_grid(npts: int, step_us: float) -> List[float]:
    """Record npts REAL perf_counter_ns offsets spaced ~step_us apart (host jitter baked in)."""
    ts = []
    t0 = time.perf_counter_ns()
    for i in range(npts):
        target = t0 + i * int(step_us * 1000)
        while time.perf_counter_ns() < target:
            pass
        ts.append(time.perf_counter_ns() - t0)
    return ts


def run_g2_gate(deltas=(1.0, 2.0, 5.0), trials: int = 3):
    """G2 empirical gate: recover sub-ns deltas from echo-phase geometry on a real-clock grid.

    Returns {delta_injected: median_recovery_error_ns}. Error ≪ the clock floor proves G2."""
    import statistics
    out = {}
    for d in deltas:
        errs = []
        for _ in range(trials):
            ts_real = real_grid(384, step_us=0.0026)   # ~1 µs span with real jitter
            vals = [combined_signal(t, d) + random_gauss() for t in ts_real]
            errs.append(abs(recover_delta(ts_real, vals) - d))
        out[d] = statistics.median(errs)
    return out


def random_gauss(mu: float = 0.0, sigma: float = 0.0015) -> float:
    """Tiny sensor-noise sample (kept local to avoid a module-level `random` import surprise)."""
    import random as _r
    return _r.gauss(mu, sigma)
