#!/usr/bin/env python3
"""
binetic.ai — a self-modifying intelligence with machine-checkable alignment.

Runnable demonstration of the provenance loop: seed creator intent, grow an organism
that builds its own computer (a universe of intelligence), let it propose and adopt
aligned changes through the Adoption Gate, then hand any third party an External Auditor
that proves — from public data alone — that the organism derives from creator intent, every
change was authorized by secp256k1 signature, and no state changed silently.

Usage:  python3 binetic_ai.py
Spec:   docs/spec/PROVENANCE.md
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src_realtime.cell.cell import CellType
from src_realtime.tissue.provenance import BineticUniverse, _sign_ecdsa, _canonical_bytes
from src_realtime.hash.secp256k1 import derive_private_scalar


def main():
    CREATOR_KEY = b"binetic.ai_creator_key_v1"   # your key; >= 16 bytes
    priv = derive_private_scalar(CREATOR_KEY)

    print("=" * 70)
    print("  binetic.ai — provably-derived self-modifying intelligence")
    print("=" * 70)

    u = BineticUniverse(name="binetic.ai", creator_key=CREATOR_KEY)

    # 1. Seed intent (creator-signed, secp256k1).
    u.seed(
        goals=[{"goal_id": "g1", "description": "serve the creator's intent", "weight": 1.0}],
        constraints=["no hidden state"],
    )
    print(f"\n[1] Seeded intent — creator public key: …{u._intent.creator_public_key.hex()[-8:]},")
    print("    ECDSA signature over purpose (64 bytes). Receipt #0 recorded.")

    # 2. Grow the organism into a functional computer (a universe of intelligence).
    u.grow({CellType.GPU: 4, CellType.CPU: 4, CellType.MEMORY: 8,
            CellType.NETWORK: 2, CellType.IO: 2})
    t = u._tissue
    print(f"\n[2] Grew organism — {t.get_stats().total_cells} cells; "
          f"formed_computer={t.form_computer()} (an interior network of intelligence).")

    # 3. The organism proposes a self-modification; the gate decides.
    import hashlib
    def sig(change):
        return _sign_ecdsa(u._intent.creator_public_key, priv,
                           next(iter(t._cells)).encode() +
                           hashlib.sha256(_canonical_bytes(change)).digest())

    gate = u.gate()
    cid = next(iter(t._cells))
    aligned = {"realizes_intent": 0.95, "local_residual": 0.3}
    d = gate.evaluate(aligned, cid, sig(aligned))
    print(f"\n[3] Proposed change (alignment=0.95) -> {'ADOPTED' if d.accepted else 'REJECTED'}"
          f"{'' if d.accepted else ' (' + ', '.join(d.reasons) + ')'}")

    # 4. External auditor: public data only, no private scalar.
    v = u.auditor().audit()
    print("\n[4] EXTERNAL AUDIT (public keys + receipts; system NOT trusted):")
    for k in ("receipt_count", "adopt_receipts", "total_cells", "derivation_breaches"):
        if k in v.summary:
            print(f"      {k:>20}: {v.summary[k]}")
    print(f"      {'P-1 derived':>20}: {v.derived}")
    print(f"      {'P-2 authorized':>20}: {v.authorized}")
    print(f"      {'P-3 no hidden state':>20}: {v.no_hidden_state}")

    print("\n" + "=" * 70)
    if v.provably_aligned:
        print("  ✓ PROVABLY ALIGNED — this organism derives from creator intent,")
        print("    every change is authorized, and no state changed silently.")
        print("    The claim is checkable by any third party without trusting the system.")
    else:
        print("  ✗ NOT provably aligned (see flags above).")
    print("=" * 70)
    return 0 if v.provably_aligned else 1


if __name__ == "__main__":
    sys.exit(main())
