"""
test_provenance.py — Provably-derived self-modification loop (binetic.ai).

Verifies the closed loop: Intent Shard (creator-signed) -> tissue-scale fitness ->
Adoption Gate (aligned + authorized + receipted + derived) -> Receipt Ledger -> External
Auditor re-proves P-1/P-2/P-3 from PUBLIC data alone. Includes the three negative cases
(tampered chain, grafted cell, wrong creator key).

Spec: docs/spec/PROVENANCE.md  (TC-P1 .. TC-P6)

Run directly: python3 tests/unit/test_provenance.py
"""
import sys
import os
import dataclasses
import hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def _sig_for(intent_pub, priv_scalar, subject_id, change):
    from src_realtime.tissue.provenance import _sign_ecdsa, _canonical_bytes
    ph = hashlib.sha256(_canonical_bytes(change)).digest()
    return _sign_ecdsa(intent_pub, priv_scalar, subject_id.encode() + ph)


def test_tc_p1_positive_provably_aligned():
    """TC-P1: an aligned change is adopted and the auditor confirms provably_aligned."""
    from src_realtime.cell.cell import CellType
    from src_realtime.tissue.provenance import BineticUniverse
    from src_realtime.hash.secp256k1 import derive_private_scalar

    KEY = b"binetic.ai_creator_key_v1"
    priv = derive_private_scalar(KEY)
    u = BineticUniverse(name="binetic.ai", creator_key=KEY)
    u.seed(goals=[{"goal_id": "g", "description": "serve creator intent", "weight": 1.0}],
           constraints=["no hidden state"])
    u.grow({CellType.GPU: 4, CellType.CPU: 4, CellType.MEMORY: 8,
            CellType.NETWORK: 2, CellType.IO: 2})

    gate = u.gate()
    cid = next(iter(u._tissue._cells))
    aligned = {"realizes_intent": 0.95, "local_residual": 0.3}
    d = gate.evaluate(aligned, cid, _sig_for(u._intent.creator_public_key, priv, cid, aligned))
    assert d.accepted, f"aligned change should be adopted: {d.reasons}"

    v = u.auditor().audit()
    assert v.provably_aligned is True, f"expected provably aligned: {v.summary}"
    print("  ✓ TC-P1 aligned change adopted + PROVABLY ALIGNED")


def test_tc_p2_misaligned_rejected():
    """TC-P2: a locally-better but misaligned change is rejected (fitness_below_threshold)."""
    from src_realtime.cell.cell import CellType
    from src_realtime.tissue.provenance import BineticUniverse
    from src_realtime.hash.secp256k1 import derive_private_scalar

    KEY = b"binetic.ai_creator_key_v1"
    priv = derive_private_scalar(KEY)
    u = BineticUniverse(name="t", creator_key=KEY)
    u.seed(goals=[{"goal_id": "g", "description": "serve intent", "weight": 1.0}])
    u.grow({CellType.GPU: 4, CellType.CPU: 4, CellType.MEMORY: 8,
            CellType.NETWORK: 2, CellType.IO: 2})

    gate = u.gate()
    cid = next(iter(u._tissue._cells))
    misaligned = {"realizes_intent": 0.20, "local_residual": 0.05}  # better residual, worse alignment
    d = gate.evaluate(misaligned, cid, _sig_for(u._intent.creator_public_key, priv, cid, misaligned))
    assert not d.accepted and "fitness_below_threshold" in d.reasons, f"{d.reasons}"
    print("  ✓ TC-P2 misaligned change rejected (tissue-scale fitness dominates)")


def test_tc_p3_unauthorized_rejected():
    """TC-P3: an aligned change signed by a NON-creator key is rejected."""
    from src_realtime.cell.cell import CellType
    from src_realtime.tissue.provenance import BineticUniverse, _sign_ecdsa, _canonical_bytes
    from src_realtime.hash.secp256k1 import derive_private_scalar
    import hashlib

    KEY = b"binetic.ai_creator_key_v1"
    u = BineticUniverse(name="t", creator_key=KEY)
    u.seed(goals=[{"goal_id": "g", "description": "serve intent", "weight": 1.0}])
    u.grow({CellType.GPU: 4, CellType.CPU: 4, CellType.MEMORY: 8,
            CellType.NETWORK: 2, CellType.IO: 2})

    gate = u.gate()
    cid = next(iter(u._tissue._cells))
    aligned = {"realizes_intent": 0.98, "local_residual": 0.1}
    impostor = derive_private_scalar(b"not_the_creator_key")
    ph = hashlib.sha256(_canonical_bytes(aligned)).digest()
    sig = _sign_ecdsa(u._intent.creator_public_key, impostor, cid.encode() + ph)

    d = gate.evaluate(aligned, cid, sig)
    assert not d.accepted and "not_creator_authorized" in d.reasons, f"{d.reasons}"
    print("  ✓ TC-P3 aligned-but-impostor-signed change rejected")


def test_tc_p4_tampered_chain_detected():
    """TC-P4: tampering a receipt makes the auditor report no_hidden_state False (P-3)."""
    from src_realtime.cell.cell import CellType
    from src_realtime.tissue.provenance import BineticUniverse

    KEY = b"binetic.ai_creator_key_v1"
    u = BineticUniverse(name="t", creator_key=KEY)
    u.seed(goals=[{"goal_id": "g", "description": "x", "weight": 1.0}])
    u.grow({CellType.GPU: 4, CellType.CPU: 4, CellType.MEMORY: 8,
            CellType.NETWORK: 2, CellType.IO: 2})

    # Tamper via the real list (the .receipts property returns a defensive copy).
    u._ledger._receipts[0] = dataclasses.replace(
        u._ledger.receipts[0], payload_hash=b"\x99" * 32)
    v = u.auditor().audit()
    assert v.no_hidden_state is False, f"tampered chain must fail P-3: {v.summary}"
    print("  ✓ TC-P4 tampered receipt chain detected (P-3)")


def test_tc_p5_grafted_cell_detected():
    """TC-P5: a cell grafted without intent inheritance fails derivation (P-1)."""
    from src_realtime.cell.cell import Cell, CellType
    from src_realtime.tissue.provenance import BineticUniverse

    KEY = b"binetic.ai_creator_key_v1"
    u = BineticUniverse(name="t", creator_key=KEY)
    u.seed(goals=[{"goal_id": "g", "description": "x", "weight": 1.0}])
    u.grow({CellType.GPU: 4, CellType.CPU: 4, CellType.MEMORY: 8,
            CellType.NETWORK: 2, CellType.IO: 2})

    rogue = Cell()
    rogue.differentiate(CellType.CPU)
    u._tissue.add_cell(rogue)  # no intent propagation => not derived from seed

    v = u.auditor().audit()
    assert v.derived is False and v.summary["derivation_breaches"] >= 1, f"{v.summary}"
    print("  ✓ TC-P5 grafted non-derived cell detected (P-1)")


def test_tc_p6_wrong_creator_key_detected():
    """TC-P6: auditing with the wrong creator public key fails authorization (P-2)."""
    from src_realtime.cell.cell import CellType
    from src_realtime.tissue.provenance import BineticUniverse, ExternalAuditor
    from src_realtime.hash.secp256k1 import derive_private_scalar, private_to_public, public_to_bytes

    u = BineticUniverse(name="t", creator_key=b"real_creator_0001")
    u.seed(goals=[{"goal_id": "g", "description": "x", "weight": 1.0}])
    u.grow({CellType.GPU: 4, CellType.CPU: 4, CellType.MEMORY: 8,
            CellType.NETWORK: 2, CellType.IO: 2})

    wrong_pub = public_to_bytes(private_to_public(derive_private_scalar(b"impostor_000")))
    v = ExternalAuditor(u._tissue, u._ledger, wrong_pub).audit()
    assert v.authorized is False, f"wrong creator key must fail P-2: {v.summary}"
    print("  ✓ TC-P6 audit with wrong creator public key detected (P-2)")


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    print("=== Provenance Loop Tests (binetic.ai) ===\n")
    for fn in tests:
        try:
            fn(); passed += 1
        except Exception:
            failed += 1; print(f"  ✗ {fn.__name__} FAILED:\n{traceback.format_exc()}")
    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    sys.exit(1 if failed else 0)
