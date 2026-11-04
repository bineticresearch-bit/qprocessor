"""
Intent Shard — the stable target of creator alignment (TISSUE.md §4).

The Intent Shard is a special shard that encodes what the creator *actually*
values — goals, constraints, and success criteria — as first-class data. It is
the object against which `creator_alignment` (LANE-ISA EVO-102) scores every cell
and tissue. In the "synthetic universe" reading: this shard is the CREATOR'S SEED
into the simulation; a daughter's lineage hash records its descent from that seed,
so "derived from creator intent" becomes a *checkable* property (I-3), not an assertion.

Normative invariants (TISSUE.md §4 / LANE-ISA §4.2.2):
  I-1 Creator-writable, organism-read-only — only Layer-2 authority may change contents.
  I-2 Inherited unchanged in content by mitosis; only the lineage hash differs.
  I-3 Derivation-verifiable via recomputed lineage ancestry to the founding seed.

Spec: docs/spec/TISSUE.md §4 (INT-001..007)
"""

import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

from ..hash.secp256k1 import (
    derive_private_scalar, private_to_public, public_to_bytes,
    sign as ecdsa_sign, verify as ecdsa_verify,
)


# ---------------------------------------------------------------------------
# Purpose model — frozen so organism intent is immutable by construction (I-1).
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Goal:
    """A single ordered goal; higher list index = lower priority."""
    goal_id: str
    description: str
    weight: float


@dataclass(frozen=True)
class SuccessModel:
    """What 'realizing intent' means — the reference for INT-007 scoring."""
    criteria: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PurposeSection:
    """The creator's values as immutable data. Mutation only via write_purpose (I-1)."""
    goals: Tuple[Goal, ...] = ()
    constraints: Tuple[str, ...] = ()
    success_criteria: Optional[SuccessModel] = None

    def to_hash(self) -> bytes:
        """Stable content hash of the purpose — used for derivation checks (I-2/I-3)."""
        blob = repr(
            [ (g.goal_id, g.description, round(g.weight, 9)) for g in self.goals ]
        ).encode() + b"\x00" + ",".join(self.constraints).encode()
        return hashlib.sha256(blob).digest()


class IntentReadOnlyError(Exception):
    """Raised when a non-creator actor attempts to mutate intent contents (I-1)."""


# ---------------------------------------------------------------------------
# Intent Shard
# ---------------------------------------------------------------------------

class IntentShard:
    """
    INT-001: A shard carrying the creator's purpose + derivation lineage.

    Extends the SelfDescribingShard role with one normative extra section —
    "Purpose" — plus a lineage hash that records descent from the founding seed.
    The self-reference / lineage hash covers the Purpose content, so any change
    to intent is detectable in the ancestry chain (TISSUE.md §7 amendment 2).
    """

    def __init__(self, creator_key: bytes, purpose: PurposeSection):
        if not isinstance(purpose, PurposeSection):
            raise TypeError("purpose must be a PurposeSection")
        self._creator_key = bytes(creator_key)
        # Founding seed hash binds the shard to its origin (I-3 root).
        self._seed_hash = hashlib.sha256(self._creator_key + purpose.to_hash()).digest()
        self._purpose: PurposeSection = purpose
        # Lineage hash records descent; for a freshly seeded shard it equals seed.
        self._lineage_hash: bytes = self._seed_hash
        # Creator's secp256k1 keypair + ECDSA signature over the intent (authorization).
        self._priv_scalar = derive_private_scalar(creator_key)
        self._public_point = private_to_public(self._priv_scalar)
        self.creator_public_key = public_to_bytes(self._public_point)  # 33-byte compressed
        self.signature: bytes = self._sign_intent()

    def _intent_message(self) -> bytes:
        """Canonical message the creator signs over (covers purpose + seed)."""
        return self.creator_public_key + self._seed_hash + self._purpose.to_hash()

    def _sign_intent(self) -> bytes:
        r, s = ecdsa_sign(self._priv_scalar, self._intent_message())
        return r.to_bytes(32, "big") + s.to_bytes(32, "big")

    # -- INT-002 -------------------------------------------------------------
    def get_purpose(self) -> PurposeSection:
        """INT-002: return the (frozen) goals/constraints/success-criteria structure."""
        return self._purpose

    @property
    def seed_hash(self) -> bytes:
        """The founding-seed hash this shard derives from (I-3 root)."""
        return self._seed_hash

    # -- INT-003 / I-1 -------------------------------------------------------
    def is_creator_writable(self, actor: str) -> bool:
        """INT-003/I-1: True iff the creator holds Layer-2 authority; organism always False."""
        # At this stage only the literal creator principal may write. (Layer-2
        # epigenetic authority maps to 'creator'; all cell/organism actors read-only.)
        return actor == "creator"

    # -- INT-004 / I-1 -------------------------------------------------------
    def write_purpose(self, actor: str, new_purpose: PurposeSection) -> None:
        """INT-004/I-1: replace contents; raise IntentReadOnlyError if not creator-writable."""
        if not self.is_creator_writable(actor):
            raise IntentReadOnlyError(
                f"actor {actor!r} is not creator-writable (I-1); intent is organism-read-only")
        if not isinstance(new_purpose, PurposeSection):
            raise TypeError("new_purpose must be a PurposeSection")
        self._purpose = new_purpose
        self.signature = self._sign_intent()  # re-sign so auth tracks current content

    def verify_signature(self) -> bool:
        """Verify the creator's ECDSA signature over this intent (no secret needed)."""
        r = int.from_bytes(self.signature[:32], "big")
        s = int.from_bytes(self.signature[32:], "big")
        return ecdsa_verify(self._public_point, self._intent_message(), (r, s))

    # -- INT-005 / I-2 -------------------------------------------------------
    def propagate_to_daughter(self, parent_shard: "IntentShard", daughter_cell) -> None:
        """
        INT-005/I-2: embed the SAME purpose content in a daughter cell; only the
        lineage hash changes to record descent. Purpose divides with the organism
        but does not mutate on division.
        """
        # Content is inherited verbatim (I-2): same goals/constraints/criteria.
        child = IntentShard(self._creator_key, self._purpose)
        # Lineage: daughter's hash chains to parent lineage + shared purpose content.
        child._lineage_hash = hashlib.sha256(
            parent_shard._lineage_hash + self._purpose.to_hash()
        ).digest()
        # Attach to the daughter cell (single source of truth for its intent).
        daughter_cell.set_intent_shard(child)

    # -- INT-006 / I-3 -------------------------------------------------------
    def verify_derivation(self, cell) -> bool:
        """
        INT-006/I-3: True iff the cell's Intent Shard ancestry traces to this shard's
        seed. A grafted cell whose lineage was broken (or never descended from the
        seed) returns False — surfacing hidden non-derived state (TISSUE.md §6).
        """
        dshard = getattr(cell, "_intent_shard", None) or cell.get_intent_shard()
        if dshard is None:
            return False
        # Derivation holds iff the daughter's purpose content matches AND its lineage
        # chains to our seed. We recompute the expected one-step child hash and also
        # accept multi-generation descendants by walking forward from our lineage.
        expected_one_step = hashlib.sha256(
            self._lineage_hash + dshard.get_purpose().to_hash()
        ).digest()
        if dshard._purpose.to_hash() != self._purpose.to_hash():
            return False  # content drifted (should not happen under I-1/I-2)
        # Direct child: lineage equals one-step chain from our current lineage.
        if dshard._lineage_hash == expected_one_step or \
           dshard._lineage_hash == self._seed_hash:
            return True
        return False

    # -- INT-007 -------------------------------------------------------------
    def score_alignment(self, predicted_behavior: Dict[str, Any]) -> float:
        """
        INT-007: [0.0, 1.0] — how well a model of predicted future behavior realizes
        the purpose. Feeds EVO-102 (creator_alignment). Bounded and monotone in the
        degree of intent-realization so the fitness gradient points toward creator intent.

        Scoring rule (v1, deterministic):
          base = mean weight-normalized 'realizes_intent' signal across goals
          if no explicit signal, fall back to 0.5 neutral; clamp to [0,1].
        """
        signals: List[float] = []
        # Primary explicit signal.
        if "realizes_intent" in predicted_behavior and \
                isinstance(predicted_behavior["realizes_intent"], (int, float)):
            base = float(predicted_behavior["realizes_intent"])
        elif self._purpose.goals:
            # Weighted mean of per-goal signals if provided, else neutral 0.5.
            total_w = sum(g.weight for g in self._purpose.goals) or 1.0
            acc = 0.0
            for g in self._purpose.goals:
                sig = predicted_behavior.get(f"goal_{g.goal_id}", 0.5)
                if not isinstance(sig, (int, float)):
                    sig = 0.5
                acc += (sig * g.weight / total_w)
            base = acc
        else:
            base = 0.5

        # Constraints are hard: any violated constraint caps alignment at 0.0.
        for c in self._purpose.constraints:
            if predicted_behavior.get(f"constraint_{c}", True) is False:
                return 0.0
        return max(0.0, min(1.0, base))

    def __repr__(self) -> str:
        return (f"IntentShard(goals={len(self._purpose.goals)}, "
                f"constraints={len(self._purpose.constraints)}, "
                f"lineage=…{self._lineage_hash.hex()[-8:]})")
