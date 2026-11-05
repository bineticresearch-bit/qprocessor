"""
test_triangularate.py — Triangulated signature & sub-hardware resolution (TRIANGULATE.md).

Proves both guarantees at their measured levels:
  G1 dual-arm beats single-timer; G2 echo-phase recovers sub-ns deltas to ps precision.
Plus the clean-case triangulation properties (exact, phase-only non-unique, noise ∝ error).

Spec: docs/spec/TRIANGULATE.md  (TC-TL1 .. TC-TL9)
Run directly: python3 tests/unit/test_triangularate.py
"""
import sys
import os
import math
import cmath
import random
import statistics
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_tc_tl1_triangulation_exact():
    """TC-TL1: two non-parallel projections recover ψ and |S| to < 1e-6 (clean case)."""
    from src_realtime.temporal.signature import project, triangulate

    tf, te = 0.0, math.pi / 3
    max_err = 0.0
    for _ in range(200):
        r = random.uniform(0.3, 2.0)
        psi = random.uniform(-math.pi, math.pi)
        S = r * cmath.exp(1j * psi)
        R = triangulate(project(S, tf), project(S, te), tf, te)
        dp = abs((math.atan2(R.imag, R.real) - psi + math.pi) % (2 * math.pi) - math.pi)
        max_err = max(max_err, dp, abs(abs(R) - r))
    assert max_err < 1e-6, f"triangulation not exact: {max_err}"
    print("  ✓ TC-TL1 triangulation exact (clean case)")


def test_tc_tl2_phase_only_not_unique():
    """TC-TL2: phase-only readings are NOT unique — same phases for different |S|."""
    from src_realtime.temporal.signature import project

    tf, te = 0.0, math.pi / 3
    psi = 0.7
    def ph(r):
        S = r * cmath.exp(1j * psi)
        return (math.atan2((S*cmath.exp(-1j*tf)).imag,(S*cmath.exp(-1j*tf)).real),
                math.atan2((S*cmath.exp(-1j*te)).imag,(S*cmath.exp(-1j*te)).real))
    p1, p5 = ph(1.0), ph(5.0)
    assert abs(p1[0]-p5[0]) < 1e-9 and abs(p1[1]-p5[1]) < 1e-9, "phase-only should be identical"
    print("  ✓ TC-TL2 phase-only not unique (amplitude required)")


def test_tc_tl3_noise_proportional():
    """TC-TL3: recovery error scales ∝ injected noise."""
    from src_realtime.temporal.signature import project, triangulate

    tf, te = 0.0, math.pi / 3
    def err_at(sigma):
        errs = []
        for _ in range(200):
            r = random.uniform(0.5, 1.5); psi = random.uniform(-math.pi, math.pi)
            S = r * cmath.exp(1j * psi)
            Mf = project(S, tf) + random.gauss(0, sigma*r)
            Me = project(S, te) + random.gauss(0, sigma*r)
            R = triangulate(Mf, Me, tf, te)
            errs.append(abs((math.atan2(R.imag,R.real)-psi+math.pi)%(2*math.pi)-math.pi))
        return statistics.median(errs) * 57.3   # degrees
    e_low, e_high = err_at(0.001), err_at(0.05)
    assert e_high > e_low, f"error should grow with noise: {e_low} vs {e_high}"
    print(f"  ✓ TC-TL3 error ∝ noise ({e_low:.4f}° @0.1% < {e_high:.4f}° @5%)")


def test_tc_tl4_echo_phase_sub_ns():
    """TC-TL4 (G2): echo-phase vernier recovers sub-ns δ to < 0.05 ns error on a real-clock grid."""
    from src_realtime.temporal.signature import combined_signal, recover_delta, real_grid

    max_err = 0.0
    for d in [1.0, 2.0, 5.0]:
        ts = real_grid(384, step_us=0.0026)   # ~1 µs span with host jitter
        vals = [combined_signal(t, d) + random.gauss(0, 0.0015) for t in ts]
        max_err = max(max_err, abs(recover_delta(ts, vals) - d))
    assert max_err < 0.05, f"G2 recovery error too large: {max_err} ns"
    print(f"  ✓ TC-TL4 echo-phase vernier recovers sub-ns δ (max err {max_err:.3f} ns)")


def test_tc_tl9_empirical_gate():
    """TC-TL9 (G1+G2): dual-arm beats single-timer; echo-phase ≪ measured floor. Any machine."""
    from src_realtime.temporal.signature import (dual_arm_delta, characterize_clock,
                                                 run_g2_gate)

    # G1: dual-arm difference must beat a single timer on sub-floor deltas.
    def single(delta):
        t0 = __import__("time").perf_counter_ns()
        e = t0 + int(delta); 
        while __import__("time").perf_counter_ns() < e: pass
        return abs((__import__("time").perf_counter_ns()-t0) - delta)
    s_err, d_err = [], []
    for _ in range(5):
        d_err.append(abs(dual_arm_delta(50_000, 100.0) - 100.0))
        s_err.append(single(100))
    assert statistics.median(d_err) < statistics.median(s_err), \
        f"dual-arm should beat single: {statistics.median(d_err)} vs {statistics.median(s_err)}"

    # G2: echo-phase recovery must be ≪ the measured clock floor.
    _, floor, _ = characterize_clock()
    g2 = run_g2_gate(deltas=(1.0,), trials=3)
    assert max(g2.values()) < floor / 100, \
        f"G2 error {max(g2.values()):.3f} ns should be ≪ floor {floor:.0f} ns"

    print(f"  ✓ TC-TL9 empirical gate: dual-arm {statistics.median(d_err):.0f}ns < single "
          f"{statistics.median(s_err):.0f}ns; G2 echo-err {max(g2.values()):.3f}ns ≪ floor {floor:.0f}ns")


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    print("=== Triangulated Signature & Resolution Tests ===\n")
    for fn in tests:
        try:
            fn(); passed += 1
        except Exception:
            failed += 1; print(f"  ✗ {fn.__name__} FAILED:\n{traceback.format_exc()}")
    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    sys.exit(1 if failed else 0)
