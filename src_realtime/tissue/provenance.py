"""
Provenance Loop — provably-derived self-modification (binetic.ai).

This is the composition that makes a self-modifying intelligence *auditable*: an
external auditor, holding only public keys and receipts (no private state), can prove
three things without trusting the running system:

  P-1 Derivation   — every cell descends from the founding seed (lineage + intent).
  P-2 Authorization — the creator signed the intent AND authorized each adopted change.
  P-3 No hidden state — every protocol state change has a receipt; none are silent.

The loop: Intent Shard (creator-signed) -> tissue-scale fitness -> Adoption Gate
(accepts only if Δfitness ≥ ε_min AND creator-authorized AND receipt emitted AND lineage
still verifies) -> Receipt Ledger -> external Auditor replays and re-proves all three.

Spec: docs/spec/PROVENANCE.md  (+ LANE-ISA §4.2, TISSUE.md §4/§6)
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Receipt — the atomic "no hidden state" record (EV-R3).
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Receipt:
    """An immutable, hash-chained record of one protocol state change.

    `prev_hash` links each receipt to its predecessor, forming a tamper-evident chain:
    corrupting any earlier receipt invalidates all subsequent ones (like LANE-ISA's seal
    chain). This is what makes 'no silent mutation' checkable by an external auditor.
    """
    seq: int
    event_type: str                 # e.g. "ADOPT", "MITOSIS", "INTENT_SEED"
    subject_id: str                 # cell / tissue id the change applies to
    payload_hash: bytes             # sha256 of the change's canonical content
    creator_signature: bytes        # 64-byte ECDSA r||s authorizing this change
    prev_hash: bytes                # hash of previous receipt (chain link)
    timestamp: float

    def compute_hash(self) -> bytes:
        blob = (str(self.seq).encode() + self.event_type.encode() +
                self.subject_id.encode() + self.payload_hash +
                self.creator_signature + self.prev_hash)
        return hashlib.sha256(blob).digest()


# ---------------------------------------------------------------------------
# Receipt Ledger — the append-only, hash-chained audit trail.
# ---------------------------------------------------------------------------

class ReceiptLedger:
    """Append-only ledger of receipts forming a tamper-evident hash chain."""

    def __init__(self):
        self._receipts: List[Receipt] = []
        # Genesis receipt (seq 0) anchors the chain; prev_hash is all-zeros.
        self._prev_hash = b"\x00" * 32
        self._head_hash = b"\x00" * 32

    @property
    def receipts(self) -> List[Receipt]:
        return list(self._receipts)

    @property
    def head_hash(self) -> bytes:
        """Hash of the most recent receipt (or genesis anchor if empty)."""
        return self._receipts[-1].compute_hash() if self._receipts else self._prev_hash

    def append(self, event_type: str, subject_id: str, payload: Any,
               creator_signature: bytes) -> Receipt:
        """Record a state change. `payload` is canonicalized (sorted JSON-ish) before hashing."""
        seq = len(self._receipts)
        if isinstance(payload, dict):
            canon = _canonical_bytes(payload)
        elif isinstance(payload, (bytes, bytearray)):
            canon = bytes(payload)
        else:
            canon = str(payload).encode()
        payload_hash = hashlib.sha256(canon).digest()

        receipt = Receipt(
            seq=seq, event_type=event_type, subject_id=subject_id,
            payload_hash=payload_hash, creator_signature=creator_signature,
            prev_hash=self._prev_hash, timestamp=time.time(),
        )
        self._receipts.append(receipt)
        self._prev_hash = receipt.compute_hash()
        self._head_hash = receipt.compute_hash()   # stored, so a tamper is detectable even at length 1
        return receipt

    def verify_chain(self) -> bool:
        """Recompute the whole chain; True iff every link is intact AND the stored head
        matches. Detects tampering even for a single-receipt ledger."""
        prev = b"\x00" * 32
        for i, r in enumerate(self._receipts):
            if r.seq != i:
                return False
            if r.prev_hash != prev:
                return False
            prev = r.compute_hash()
        # Stored head must equal the recomputed head (catches last-receipt tamper).
        expected_head = prev if self._receipts else b"\x00" * 32
        return self._head_hash == expected_head


def _canonical_bytes(obj: Any) -> bytes:
    """Deterministic serialization so the same change always hashes identically.

    bytes are hex-encoded and non-JSON scalars stringified, so any payload type yields
    a stable canonical form (the auditor re-hashes with this exact function).
    """
    import json
    def norm(o):
        if isinstance(o, dict):
            return {str(k): norm(v) for k, v in sorted((k2, o[k2]) for k2 in o)}
        if isinstance(o, (list, tuple)):
            return [norm(x) for x in o]
        if isinstance(o, (bytes, bytearray)):
            return "0x" + bytes(o).hex()
        if isinstance(o, (str, int, float, bool)) or o is None:
            return o
        return str(o)
    return json.dumps(norm(obj), sort_keys=True).encode()


# ---------------------------------------------------------------------------
# Adoption Gate — the only path a self-modification may take to be committed.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AdoptionDecision:
    accepted: bool
    reasons: List[str]              # empty iff accepted; else the failed checks
    receipt_seq: Optional[int]


class AdoptionGate:
    """Enforces that a self-modification is adopted ONLY if ALL of P-1..P-3 hold.

    A change passes when, and only when:
      1. Δfitness ≥ ε_min on tissue-scale fitness (creator-alignment dominant).   [interest]
      2. The creator's public key authorizes it (ECDSA over the change payload).   [authorization]
      3. A receipt is emitted into the ledger and the chain stays intact.          [no hidden state]
      4. Derivation to seed still verifies after the change.                       [derivation]

    This is EV-R1 + I-1 + EV-R3 composed: the organism may explore, but a *committed*
    change must be aligned, authorized, logged, and derived — or it is rejected.
    """

    def __init__(self, tissue, ledger: ReceiptLedger, creator_public_key: bytes,
                 min_delta: float = 1e-9):
        self._tissue = tissue
        self._ledger = ledger
        self._creator_pub = creator_public_key
        self._min_delta = min_delta

    def evaluate(self, candidate_behavior: Dict[str, Any], subject_id: str,
                 creator_signature: bytes) -> AdoptionDecision:
        reasons: List[str] = []

        # 1. Fitness (interest aligns with intent).
        if not self._tissue.should_adopt(candidate_behavior):
            reasons.append("fitness_below_threshold")

        # 2. Authorization: signature must verify against the creator's public key.
        payload_hash = hashlib.sha256(_canonical_bytes(candidate_behavior)).digest()
        message = subject_id.encode() + payload_hash
        if not _verify_ecdsa(self._creator_pub, message, creator_signature):
            reasons.append("not_creator_authorized")

        # 3 & 4. If aligned+authorized, commit: emit receipt and re-check derivation/chain.
        if not reasons:
            self._ledger.append("ADOPT", subject_id, candidate_behavior, creator_signature)
            if not self._ledger.verify_chain():
                return AdoptionDecision(False, ["receipt_chain_broken"], None)

            # Derivation: the acting cell must still trace to seed.
            from ..cell.cell import Cell  # local import avoids cycle at module load
            cell = self._tissue.get_cell(subject_id) if hasattr(self._tissue, "get_cell") else None
            intent = self._tissue.get_intent_shard()
            if intent is not None and cell is not None:
                if not intent.verify_derivation(cell):
                    # Roll back the receipt we just added (rejection must leave no trace).
                    self._ledger._receipts.pop()
                    new_recs = self._ledger.receipts
                    self._ledger._prev_hash = new_recs[-1].compute_hash() if new_recs else b"\x00"*32
                    self._ledger._head_hash = self._ledger._prev_hash
                    return AdoptionDecision(False, ["derivation_broken"], None)

            seq = len(self._ledger.receipts) - 1
            return AdoptionDecision(True, [], seq)

        return AdoptionDecision(False, reasons, None)


def _verify_ecdsa(public_key_bytes: bytes, message: bytes, signature: bytes) -> bool:
    """Verify a 64-byte r||s ECDSA signature against a compressed public point."""
    from ..hash.secp256k1 import verify, public_from_bytes
    if len(signature) != 64 or len(public_key_bytes) != 33:
        return False
    try:
        pub = public_from_bytes(public_key_bytes)
    except ValueError:
        return False
    r = int.from_bytes(signature[:32], "big")
    s = int.from_bytes(signature[32:], "big")
    return verify(pub, message, (r, s))


def _sign_ecdsa(creator_public_key: bytes, creator_private_scalar: int,
                message: bytes) -> bytes:
    """Creator-side helper: produce the 64-byte signature an auditor will check."""
    from ..hash.secp256k1 import sign
    r, s = sign(creator_private_scalar, message)
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


# ---------------------------------------------------------------------------
# External Auditor — re-proves P-1..P-3 from PUBLIC data only. No private state.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuditVerdict:
    derived: bool                  # P-1: all cells derive from seed
    authorized: bool               # P-2: intent + every ADOPT receipt creator-signed
    no_hidden_state: bool          # P-3: receipt chain intact, seq contiguous
    summary: Dict[str, Any] = field(default_factory=dict)

    @property
    def provably_aligned(self) -> bool:
        return self.derived and self.authorized and self.no_hidden_state


class ExternalAuditor:
    """Reconstructs the organism's alignment proof using only public artifacts.

    Input is deliberately limited to what a third party could hold: the tissue (to read
    cells + intent), the receipt ledger, and the creator's PUBLIC key. It never sees the
    private scalar. If it returns provably_aligned=True, the claim 'this self-modifying
    organism derives from and is authorized by its creator' is independently checkable —
    no trust in the running system required.
    """

    def __init__(self, tissue, ledger: ReceiptLedger, creator_public_key: bytes):
        self._tissue = tissue
        self._ledger = ledger
        self._creator_pub = creator_public_key

    def audit(self) -> AuditVerdict:
        summary: Dict[str, Any] = {}

        # --- P-3: no hidden state — chain intact + contiguous seq --------------
        chain_ok = self._ledger.verify_chain()
        receipts = self._ledger.receipts
        contiguous = all(r.seq == i for i, r in enumerate(receipts))
        summary["receipt_count"] = len(receipts)
        summary["chain_intact"] = chain_ok
        no_hidden_state = chain_ok and contiguous

        # --- P-2: authorization — intent signed by THE expected creator, and every ADOPT receipt ----
        authorized = True
        intent = self._tissue.get_intent_shard()
        if intent is None or not intent.verify_signature():
            authorized = False
        else:
            # The Intent Shard's embedded creator public key must match the auditor's.
            # (Self-verification alone would pass for any key; this binds to *the* creator.)
            if intent.creator_public_key != self._creator_pub:
                authorized = False
        summary["intent_signed"] = bool(intent) and (intent.verify_signature() if intent else False)
        # Every ADOPT receipt's creator_signature must verify against the public key.
        adopt_count = 0
        for r in receipts:
            if r.event_type != "ADOPT":
                continue
            adopt_count += 1
            payload_hash = r.payload_hash
            message = r.subject_id.encode() + payload_hash
            # The receipt stores the signature; verify it matches the creator key.
            if not _verify_ecdsa(self._creator_pub, message, r.creator_signature):
                authorized = False
        summary["adopt_receipts"] = adopt_count

        # --- P-1: derivation — every cell traces to seed ------------------------
        derived = True
        breaches = 0
        total_cells = len(getattr(self._tissue, "_cells", {}))
        if intent is not None:
            for cell_id, cell in getattr(self._tissue, "_cells", {}).items():
                if not intent.verify_derivation(cell):
                    derived = False
                    breaches += 1
        else:
            # No seeded intent => nothing to derive from; treat as not-derived.
            derived = total_cells == 0
        summary["total_cells"] = total_cells
        summary["derivation_breaches"] = breaches

        return AuditVerdict(
            derived=derived, authorized=authorized, no_hidden_state=no_hidden_state,
            summary=summary,
        )


# ---------------------------------------------------------------------------
# binetic.ai — the public face: a one-call builder of a provably-aligned organism.
# ---------------------------------------------------------------------------

class _EmptyTissue:
    """Minimal tissue view for auditing before any cells are grown."""
    def __init__(self, intent):
        self._intent = intent
        self._cells = {}
    def get_intent_shard(self):
        return self._intent

class BineticUniverse:
    """A self-modifying intelligence universe with machine-checkable alignment.

    This is the 'vision on the map': build it, let it propose changes, and hand any
    third party an ExternalAuditor that proves — from public data alone — that the
    organism derives from creator intent, every change was authorized, and no state
    changed silently.
    """

    def __init__(self, name: str = "binetic.ai", creator_key: bytes = b""):
        self.name = name
        if not creator_key:
            raise ValueError("creator_key required")
        from .portal import Portal
        self._portal = Portal(creator_key)
        self._ledger = ReceiptLedger()
        self._intent = None      # the seeded, creator-signed IntentShard
        self._tissue = None      # the organism

    def seed(self, goals: List[Dict[str, Any]], constraints: Optional[List[str]] = None):
        """Seed intent (creator-signed) and record it in the ledger."""
        from ..hash.secp256k1 import derive_private_scalar
        self._intent = self._portal.seed_intent(goals, constraints)
        # Record the intent seed as receipt 0 (authorization proven by its signature).
        priv = derive_private_scalar(self._portal._creator_key)
        msg = b"INTENT_SEED:" + self._intent.creator_public_key + self._intent.signature
        sig = _sign_ecdsa(self._intent.creator_public_key, priv, msg)
        self._ledger.append("INTENT_SEED", self.name, {"purpose_hash": self._intent.get_purpose().to_hash()}, sig)

    def grow(self, roles: Dict[Any, int]) -> None:
        """Grow the organism's role mix (each cell inherits the signed intent)."""
        if self._tissue is None:
            self._tissue = self._portal.create_tissue(name=self.name)
        if self._intent is not None:
            self._tissue.set_intent_shard(self._intent)
        self._portal.grow(self._tissue, roles)

    def gate(self, min_delta: float = 1e-9):
        """Return the Adoption Gate bound to this universe's ledger + creator key."""
        assert self._tissue is not None and self._intent is not None, "seed() then grow() first"
        return AdoptionGate(
            tissue=self._tissue, ledger=self._ledger,
            creator_public_key=self._intent.creator_public_key, min_delta=min_delta,
        )

    def auditor(self) -> ExternalAuditor:
        """Return an external auditor using only public data (creator PUBLIC key).

        Works after seed() alone (audits the intent + ledger); a tissue is optional.
        """
        assert self._intent is not None, "seed() first"
        # Auditor reads cells off the tissue if present; else an empty view.
        return ExternalAuditor(
            tissue=self._tissue if self._tissue is not None else _EmptyTissue(self._intent),
            ledger=self._ledger, creator_public_key=self._intent.creator_public_key,
        )

    def __repr__(self) -> str:
        return f"BineticUniverse(name={self.name!r}, receipts={len(self._ledger.receipts)})"
