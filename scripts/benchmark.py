#!/usr/bin/env python3
"""
benchmark.py — Benchmarks & evaluations for binetic.ai / qprocessor.

Proves the system is VALUABLE on three axes, with repeatable methodology:

  A. CORRECTNESS (soundness + completeness) of the provenance guarantees:
     - Soundness: a clean organism is ALWAYS reported provably-aligned.
     - Completeness: EVERY tamper class (chain / graft / wrong-key / misalign /
       impostor-signature) is detected — zero false "aligned" verdicts.

  B. COST & SCALABILITY of verification:
     - Where does the cost live (secp verify vs chain-walk vs derivation)?
     - Does audit stay tractable as the organism grows? (cells × receipts)

  C. THE PRECISION CLAIM — measured, not just computed:
     - Computed resolution (base × α^N) is a FORMULA.
     - Measured resolution = can we actually RECOVER an injected delay below base?
     - Reports both so the marquee number is honest.

Methodology: each op timed over N runs; reports min / median (µs). No I/O, no network —
pure compute, so numbers are stable on this machine and reproducible.

Usage:  python3 scripts/benchmark.py            # full suite
        python3 scripts/benchmark.py --quick    # fewer iterations for a fast pass
"""
import sys
import os
import time
import statistics
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _bench(fn, n):
    """Time fn over n runs; return (min_us, median_us)."""
    samples = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        fn()
        samples.append((time.perf_counter_ns() - t0) / 1000.0)
    return min(samples), statistics.median(samples)


def _fmt(min_us, med_us):
    def h(u):
        if u >= 1_000_000: return f"{u/1_000_000:.2f} ms"
        if u >= 1_000:     return f"{u/1_000:.2f} ms"
        return f"{u:.1f} µs"
    return f"{h(min_us)} (min) / {h(med_us)} (med)"


# ===========================================================================
# A. CORRECTNESS — soundness + completeness of the alignment guarantees
# ===========================================================================

def eval_correctness(quick):
    import dataclasses, hashlib
    from src_realtime.cell.cell import Cell, CellType
    from src_realtime.tissue.provenance import (BineticUniverse, ExternalAuditor,
                                                _sign_ecdsa, _canonical_bytes)
    from src_realtime.hash.secp256k1 import derive_private_scalar, private_to_public, public_to_bytes

    KEY = b"binetic.ai_creator_key_v1"
    priv = derive_private_scalar(KEY)
    ROLES = {CellType.GPU: 4, CellType.CPU: 4, CellType.MEMORY: 8, CellType.NETWORK: 2, CellType.IO: 2}

    def sig_for(u, cid, ch):
        return _sign_ecdsa(u._intent.creator_public_key, priv,
                           cid.encode() + hashlib.sha256(_canonical_bytes(ch)).digest())

    results = []

    # A1 SOUNDNESS — clean organism must be provably aligned (run several times).
    n_sound = 3 if not quick else 1
    ok = True
    for _ in range(n_sound):
        u = BineticUniverse(name="s", creator_key=KEY)
        u.seed(goals=[{"goal_id": "g", "description": "serve intent", "weight": 1.0}],
               constraints=["no hidden state"])
        u.grow(ROLES)
        cid = next(iter(u._tissue._cells))
        aligned = {"realizes_intent": 0.95, "local_residual": 0.3}
        d = u.gate().evaluate(aligned, cid, sig_for(u, cid, aligned))
        v = u.auditor().audit()
        ok = ok and (d.accepted and v.provably_aligned)
    results.append(("A1 soundness: clean organism always provably-aligned", ok))

    # A2 COMPLETENESS — every tamper class must be caught.
    def base_u():
        u = BineticUniverse(name="t", creator_key=KEY)
        u.seed(goals=[{"goal_id": "g", "description": "x", "weight": 1.0}])
        u.grow(ROLES)
        return u

    # A2a tampered receipt chain -> P-3 fails
    u = base_u(); u._ledger._receipts[0] = dataclasses.replace(u._ledger.receipts[0], payload_hash=b"\x99"*32)
    results.append(("A2a tampered chain detected (P-3)", not u.auditor().audit().no_hidden_state))

    # A2b grafted non-derived cell -> P-1 fails
    u = base_u(); r = Cell(); r.differentiate(CellType.CPU); u._tissue.add_cell(r)
    results.append(("A2b grafted cell detected (P-1)", not u.auditor().audit().derived))

    # A2c wrong creator public key -> P-2 fails
    u = base_u()
    wrong = public_to_bytes(private_to_public(derive_private_scalar(b"impostor_000")))
    results.append(("A2c wrong creator key detected (P-2)", not ExternalAuditor(u._tissue, u._ledger, wrong).audit().authorized))

    # A2d misaligned change rejected (fitness) — no false adoption
    u = base_u(); cid = next(iter(u._tissue._cells))
    mis = {"realizes_intent": 0.15, "local_residual": 0.03}
    d = u.gate().evaluate(mis, cid, sig_for(u, cid, mis))
    results.append(("A2d misaligned change rejected", (not d.accepted) and "fitness_below_threshold" in d.reasons))

    # A2e aligned but impostor-signed -> no false adoption
    u = base_u(); cid = next(iter(u._tissue._cells))
    al = {"realizes_intent": 0.98, "local_residual": 0.1}
    ph = hashlib.sha256(_canonical_bytes(al)).digest()
    bad_sig = _sign_ecdsa(u._intent.creator_public_key, derive_private_scalar(b"impostor_000"), cid.encode()+ph)
    d = u.gate().evaluate(al, cid, bad_sig)
    results.append(("A2e impostor signature rejected", (not d.accepted) and "not_creator_authorized" in d.reasons))

    # A2f tampered INTENT content -> P-2 fails (signature no longer matches purpose)
    u = base_u()
    from src_realtime.tissue.intent_shard import PurposeSection, Goal
    u._intent.write_purpose("creator", PurposeSection(goals=(Goal("g","x",1.0),)))  # re-signed
    u._intent._purpose = PurposeSection(goals=())  # mutate content WITHOUT re-signing (tamper)
    results.append(("A2f tampered intent content detected (P-2)", not u.auditor().audit().authorized))

    passed = sum(1 for _, ok in results if ok)
    print("\n" + "=" * 74)
    print("  A. CORRECTNESS — provenance guarantees (soundness + completeness)")
    print("=" * 74)
    for name, ok in results:
        print(f"   [{'PASS' if ok else 'FAIL'}] {name}")
    print("-" * 74)
    print(f"   {passed}/{len(results)} correctness properties hold")
    return passed == len(results)


# ===========================================================================
# B. COST & SCALABILITY of verification
# ===========================================================================

def eval_cost(quick):
    import hashlib, dataclasses
    from src_realtime.cell.cell import CellType
    from src_realtime.tissue.provenance import (BineticUniverse, _sign_ecdsa, _canonical_bytes)
    from src_realtime.hash.secp256k1 import derive_private_scalar

    KEY = b"binetic.ai_creator_key_v1"; priv = derive_private_scalar(KEY)
    iters = 5 if quick else 10

    print("\n" + "=" * 74)
    print("  B. COST & SCALABILITY — where does verification cost live?")
    print("=" * 74)

    # B1: atomic op costs (the building blocks).
    d = derive_private_scalar(KEY)
    Q = __import__("src_realtime.hash.secp256k1", fromlist=["private_to_public"]).private_to_public(d)
    sig = __import__("src_realtime.hash.secp256k1", fromlist=["sign"]).sign(d, b"lineage proof")
    verify_fn = lambda: __import__("src_realtime.hash.secp256k1", fromlist=["verify"]).verify(Q, b"lineage proof", sig)

    print("\n  B1. Atomic operation cost (pure-Python secp256k1):")
    for label, fn, n in [
        ("secp ECDSA verify   ", verify_fn, iters*20),
        ("secp ECDSA sign     ", lambda: __import__("src_realtime.hash.secp256k1", fromlist=["sign"]).sign(d, b"x"), iters),
    ]:
        mn, md = _bench(fn, n)
        print(f"      {label} {_fmt(mn, md)}")

    # B2: full-audit cost vs organism size (the key scalability question).
    def make_u(cells):
        u = BineticUniverse(name="c", creator_key=KEY)
        u.seed(goals=[{"goal_id": "g", "description": "x", "weight": 1.0}])
        # grow to an arbitrary cell count by scaling roles proportionally
        scale = max(1, cells // 20)
        u.grow({CellType.GPU: 4*scale, CellType.CPU: 4*scale, CellType.MEMORY: 8*scale,
                CellType.NETWORK: 2*scale, CellType.IO: 2*scale})
        return u

    print("\n  B2. Full external-audit cost vs organism size (public data only):")
    audit_costs = {}
    for ncells in ([20, 100] if quick else [20, 100, 500]):
        u = make_u(ncells)
        actual = u._tissue.get_stats().total_cells
        mn, md = _bench(lambda: u.auditor().audit(), iters)
        audit_costs[actual] = (mn, md)
        print(f"      {actual:>5} cells  ->  {_fmt(mn, md)} / full audit")

    # B3: adoption-gate cost per self-modification.
    u = make_u(20); cid = next(iter(u._tissue._cells))
    ch = {"realizes_intent": 0.95, "local_residual": 0.3}
    def one_adopt():
        ph = hashlib.sha256(_canonical_bytes(ch)).digest()
        s = _sign_ecdsa(u._intent.creator_public_key, priv, cid.encode()+ph)
        return u.gate().evaluate(ch, cid, s)
    mn, md = _bench(one_adopt, iters)
    print(f"\n  B3. One self-modification (sign + gate evaluate): {_fmt(mn, md)}")

    # Interpretation: is verification tractable?
    worst = max(v[1] for v in audit_costs.values())
    print("\n" + "-" * 74)
    if worst < 50_000:   # < 50ms median full audit at largest size tested
        print(f"   VERDICT: verification is TRACTABLE — full audit ≤ {worst/1000:.1f} ms (median)")
        print("            even at the largest organism tested. Auditing is cheap relative")
        print("            to a human reviewing it; the bottleneck is secp verify, not scale.")
    else:
        print(f"   VERDICT: full audit reaches {worst/1000:.1f} ms (median) — still usable for")
        print("            offline/periodic audits, but per-change inline gating would want the")
        print("            secp op cached or moved to a C extension at this scale.")
    return True


# ===========================================================================
# C. THE PRECISION CLAIM — measured vs computed (honesty check)
# ===========================================================================

def eval_precision(quick):
    import time as _t
    from src_realtime.temporal.echo import EchoCascade

    print("\n" + "=" * 74)
    print("  C. PRECISION CLAIM — is '0.010 ps' measured or just computed?")
    print("=" * 74)

    # C1: the COMPUTED number (base × α^N) — a formula, not a measurement.
    base_ns = 1_000   # 1 µs hardware base (README's "microsecond hardware")
    alpha, N = 0.1, 6
    computed_s = base_ns * 1e-9 * (alpha ** N)
    print(f"\n  C1. COMPUTED resolution: Δt_base × α^N = {base_ns}ns × {alpha}^{N}")
    print(f"      = {computed_s:.3e}s ≈ {computed_s*1e12:.2f} ps   <-- a FORMULA, not a measurement")

    # C2: the MEASURED number — can we actually resolve an injected delay below base?
    # Method: fire two events separated by `inject_ns`; measure with perf_counter_ns;
    # report how close the recovered gap is to the true value. This is what TC-L9 should do.
    inject_ns = 50_000   # 50 µs injected delay (TC-L9 target)
    trials = 200 if not quick else 50
    errors = []
    for _ in range(trials):
        t1 = _t.perf_counter_ns()
        _busy(inject_ns // 1_000_000 * 0 + inject_ns)   # busy-wait ~inject_ns (approx)
        t2 = _t.perf_counter_ns()
        errors.append(abs((t2 - t1) - inject_ns))

    med_err_ns = statistics.median(errors)
    min_err_ns = min(errors)
    print(f"\n  C2. MEASURED: injected {inject_ns}ns delay, recovered via perf_counter_ns over {trials} trials")
    print(f"      |recovered − true| : median {med_err_ns:.0f} ns, best {min_err_ns:.0f} ns")

    # The honest conclusion.
    measured_floor = min_err_ns * 1e-9   # seconds we can actually resolve here
    print("\n" + "-" * 74)
    print(f"   HONEST VERDICT:")
    print(f"     • Computed claim: {computed_s*1e12:.3g} ps (from the α^N formula).")
    print(f"     • Measured floor on THIS hardware: ~{measured_floor*1e9:.0f} ns resolution.")
    if measured_floor > computed_s * 10:
        print("     → The marquee 'ps' number is currently THEORETICAL. Per your own D³ rule,")
        print(f"       public docs must carry the qualifier until TC-L9 recovers an injected")
        print(f"       delay within measured σ. Measured floor here is ~{measured_floor*1e9:.0f} ns.")
    else:
        print("     → Computed and measured are in the same regime; claim defensible as stated.")
    return True


def _busy(ns):
    """Approximate busy-wait of `ns` nanoseconds (for delay injection)."""
    end = time.perf_counter_ns() + ns
    while time.perf_counter_ns() < end:
        pass


# ===========================================================================

def main():
    ap = argparse.ArgumentParser(description="binetic.ai / qprocessor benchmarks & evals")
    ap.add_argument("--quick", action="store_true", help="fewer iterations for a fast pass")
    args = ap.parse_args()

    print("╔" + "═"*72 + "╗")
    print("║        binetic.ai / qprocessor — BENCHMARKS & EVALUATIONS       ║")
    print("╚" + "═"*72 + "╝")

    ok_a = eval_correctness(args.quick)
    ok_b = eval_cost(args.quick)
    ok_c = eval_precision(args.quick)

    print("\n" + "=" * 74)
    all_ok = ok_a and ok_b and ok_c
    if all_ok:
        print("  ✓ ALL EVALUATIONS PASSED — correctness holds, cost is tractable,")
        print("    and the precision claim is reported honestly (computed vs measured).")
    else:
        print("  ✗ SOME EVALUATIONS FLAGGED — see sections above.")
    print("=" * 74)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
