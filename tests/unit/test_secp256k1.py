"""
test_secp256k1.py — Curve arithmetic + Genesis ECDSA integration.

Verifies the pure-Python secp256k1 module against independent reference values,
and that both Genesis trees now use real asymmetric signatures (verify without
the private key). Spec: docs/spec/GENESIS.md Layer 1.

Run directly: python3 tests/unit/test_secp256k1.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_curve_arithmetic():
    """secp256k1 group law + order against independent reference values."""
    from src.hash.secp256k1 import G, N, is_on_curve, scalar_mult

    assert is_on_curve(G), "generator must be on the curve"
    # Independent reference (computed with a separate implementation).
    REF_3G_X = 0xf9308a019258c31049344f85f89d5229b531c845836f99b08601f113bce036f9
    three = scalar_mult(3, G)
    assert three[0] == REF_3G_X, f"3·G mismatch: {hex(three[0])}"
    # Group order: n·G = point at infinity.
    assert scalar_mult(N, G) is None, "n·G must be the identity"
    print("  ✓ secp256k1 group law + order correct")


def test_ecdsa_sign_verify():
    """ECDSA: valid sig verifies; tamper / wrong-key reject; deterministic."""
    from src.hash.secp256k1 import (derive_private_scalar, private_to_public,
                                    public_to_bytes, public_from_bytes, sign, verify)

    d = derive_private_scalar(b"binetic_creator_secret_v1")
    Q = private_to_public(d)
    enc = public_to_bytes(Q)
    assert len(enc) == 33 and enc[0] in (2, 3), "compressed point must be 33 bytes"
    dec = public_from_bytes(enc)
    assert dec == Q, "public key round-trip failed"

    msg = b"genesis cell #1 lineage proof"
    sig = sign(d, msg)
    r, s = sig
    assert verify(Q, msg, sig), "valid signature must verify"
    assert not verify(Q, b"different message", sig), "tampered message must fail"

    Q2 = private_to_public(derive_private_scalar(b"a_different_key"))
    assert not verify(Q2, msg, sig), "wrong public key must reject"

    # Deterministic (RFC 6979) + low-s normalized.
    assert sign(d, msg) == sig, "signatures must be deterministic"
    from src.hash.secp256k1 import N as ORDER
    assert s <= ORDER // 2, "s must be in low form (BIP-62)"
    print("  ✓ ECDSA sign/verify + determinism + low-s")


def test_genesis_asymmetric_standard():
    """Standard-tree Genesis: public key is a curve point; sig verifies w/o secret."""
    from src.cell.cell import Cell
    from src.genesis.genesis import GenesisSignature

    gs = GenesisSignature(b"binetic_creator_secret_v1")
    assert len(gs.creator_public_key) == 33 and gs.creator_public_key[0] in (2, 3), \
        "public key must be a compressed secp256k1 point, not sha256(32 bytes)"
    assert gs.verify_genesis_signature() is True

    same = GenesisSignature(b"binetic_creator_secret_v1")
    other = GenesisSignature(b"a_different_key")
    assert gs.verify_signature_for(same.creator_public_key) is True
    assert gs.verify_signature_for(other.creator_public_key) is False

    cell = Cell(); gs.embed_in_cell(cell)
    assert gs.verify_cell(cell) and not gs.verify_cell(Cell())
    print("  ✓ standard Genesis uses real asymmetric secp256k1 signatures")


def test_genesis_asymmetric_realtime():
    """Realtime-tree Genesis: lineage sig verifies with public point only."""
    from src_realtime.cell.cell import Cell as RCell
    from src_realtime.genesis.genesis import GenesisProtocol
    from src_realtime.hash.secp256k1 import verify, public_from_bytes

    proto = GenesisProtocol(b"binetic_creator_secret_v1")
    c1 = RCell(); c2 = RCell()
    sig1 = proto.embed_in_cell(c1)
    assert len(sig1) == 64, "genesis signature must be r||s (64 bytes)"

    proto.propagate_to_daughter(c1, c2)
    lineage_sig = proto._genesis_signatures[c2.get_id()]
    parent_sig = proto._genesis_signatures[c1.get_id()]

    pub = public_from_bytes(proto._creator_public_key)
    data = c2.get_id().encode() + parent_sig
    r = int.from_bytes(lineage_sig[:32], "big")
    s = int.from_bytes(lineage_sig[32:], "big")
    assert verify(pub, data, (r, s)) is True, "lineage must verify with public point only"

    # Tampered message rejected.
    assert not verify(pub, b"x" + parent_sig, (r, s)), "tamper must fail"
    print("  ✓ realtime Genesis lineage verifies asymmetrically")


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    print("=== secp256k1 + Genesis Crypto Tests ===\n")
    for fn in tests:
        try:
            fn(); passed += 1
        except Exception:
            failed += 1; print(f"  ✗ {fn.__name__} FAILED:\n{traceback.format_exc()}")
    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    sys.exit(1 if failed else 0)
