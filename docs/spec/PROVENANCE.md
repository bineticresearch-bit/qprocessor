# PROVENANCE Specification — Provably-Derived Self-Modification (binetic.ai)

## Single Source of Truth

**Version:** 1.0
**Status:** Active (spec-first; `src_realtime/tissue/provenance.py` implementation must match)
**Referenced by (target):** `src_realtime/tissue/provenance.py`, `tests/unit/test_provenance.py`
**Depends on:** TISSUE (§4 Intent Shard, §6 Alignment), LANE-ISA §4.2 (fitness + EV-R1/R3), HASH (HASH-007 secp256k1), GENESIS

---

## 0. Core Principle: Alignment as a Verifiable Theorem

A self-modifying intelligence is only credible if "it derives from and serves creator
intent" can be **checked without trusting the system**. This spec makes that checkable.

An external auditor — holding *only* public keys and receipts, never the private scalar —
re-proves three properties of any organism:

| Property | Claim | Mechanism |
|----------|-------|-----------|
| **P-1 Derivation** | every cell descends from the founding seed | Intent Shard lineage + `verify_derivation` (TISSUE I-3) |
| **P-2 Authorization** | creator signed the intent AND authorized each adopted change | secp256k1 ECDSA over intent + each ADOPT receipt (HASH-007) |
| **P-3 No hidden state** | every protocol state change has a receipt; none are silent | hash-chained Receipt Ledger (EV-R3) |

If all three hold, the organism is **provably aligned**: `AuditVerdict.provably_aligned`.
This composes LANE-ISA §4.2 (fitness), I-1 (creator-writable intent), and EV-R3 (receipts)
into a single closed loop with an independent verifier — the "synthetic universe of
intelligence" becoming *auditable*.

---

## 1. Receipt & Ledger — `Receipt`, `ReceiptLedger`

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| PRV-001 | `class Receipt` (frozen) | seq, event_type, subject_id, payload_hash, creator_signature(64B r‖s), prev_hash, timestamp | immutable record of one state change | 🟢 |
| PRV-002 | `Receipt.compute_hash() -> bytes` | none | sha256 over (seq,type,subject,payload,sig,prev) — the chain link | 🟢 |
| PRV-003 | `class ReceiptLedger` | none | append-only ledger; genesis anchor prev=all-zeros | 🟢 |
| PRV-004 | `ReceiptLedger.append(event_type, subject_id, payload, creator_signature) -> Receipt` | change details + 64B sig | new receipt; updates stored head hash | 🟢 |
| PRV-005 | `ReceiptLedger.verify_chain() -> bool` | none | True iff every link intact AND stored head matches recomputed (detects tamper even at length 1) | 🟢 |

**Normative:** the ledger stores a `_head_hash`. Tampering any receipt changes its
recomputed hash, which either breaks a downstream `prev_hash` or mismatches the stored
head — so *any* single-receipt edit is detectable (not just multi-receipt chains).

---

## 2. Adoption Gate — `AdoptionGate`, `AdoptionDecision`

The **only** path a self-modification may take to be committed. A change is adopted iff ALL hold:

| ID | Check | Reject reason on failure |
|----|-------|--------------------------|
| PRV-101 | Δfitness ≥ ε_min on tissue-scale fitness (creator-alignment dominant) | `fitness_below_threshold` |
| PRV-102 | creator's public key authorizes it (ECDSA over subject + payload hash) | `not_creator_authorized` |
| PRV-103 | a receipt is emitted and the chain stays intact | `receipt_chain_broken` |
| PRV-104 | derivation to seed still verifies after the change | `derivation_broken` (receipt rolled back — rejection leaves no trace) |

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| PRV-105 | `class AdoptionGate` | tissue, ledger, creator_public_key(33B), min_delta | gate bound to an organism | 🟢 |
| PRV-106 | `AdoptionGate.evaluate(candidate_behavior, subject_id, creator_signature) -> AdoptionDecision` | proposed change + 64B sig | accepted/rejected + reasons + receipt seq | 🟢 |

**Normative:** this is EV-R1 (monotone adoption) + I-1 (creator-authorizes) + EV-R3
(receipts) composed. The organism may explore freely, but a *committed* change must be
aligned, authorized, logged, and derived — or it is rejected with no trace left behind.

---

## 3. External Auditor — `ExternalAuditor`, `AuditVerdict`

Reconstructs the alignment proof from **public artifacts only** (tissue to read cells +
intent, the ledger, and the creator's PUBLIC key). Never sees the private scalar.

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| PRV-201 | `class ExternalAuditor` | tissue, ledger, creator_public_key(33B) | auditor bound to an organism + expected creator | 🟢 |
| PRV-202 | `ExternalAuditor.audit() -> AuditVerdict` | none | derived / authorized / no_hidden_state flags + summary | 🟢 |

**Normative checks:**
* **P-3** — `verify_chain()` True AND receipt seq contiguous.
* **P-2** — Intent Shard's embedded creator public key == the expected key (binds to *the*
  creator, not just "some" signer), intent self-signature valid, and every ADOPT receipt's
  signature verifies against that public key.
* **P-1** — every cell passes `verify_derivation` against the seeded intent; any failure is a breach.

`AuditVerdict.provably_aligned = derived AND authorized AND no_hidden_state`.

---

## 4. binetic.ai — `BineticUniverse` (public face)

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| PRV-301 | `class BineticUniverse(name, creator_key)` | name + ≥16-byte key | universe with ledger; intent/tissue set on seed/grow | 🟢 |
| PRV-302 | `BineticUniverse.seed(goals, constraints) -> None` | goal list + hard constraints | stores signed IntentShard; records INTENT_SEED receipt (seq 0) | 🟢 |
| PRV-303 | `BineticUniverse.grow(roles: Dict[CellType,int]) -> None` | role mix | creates tissue, binds intent, differentiates cells (each inherits signed intent) | 🟢 |
| PRV-304 | `BineticUniverse.gate(min_delta=1e-9) -> AdoptionGate` | threshold | gate over this universe's ledger + creator key | 🟢 |
| PRV-305 | `BineticUniverse.auditor() -> ExternalAuditor` | none | auditor using only public data (works post-seed, pre-grow) | 🟢 |

---

## 5. Test Cases (must exist before implementation; D³ gate)

| TC | Asserts | Method |
|----|---------|--------|
| TC-P1 | Positive: aligned change adopted → `provably_aligned` True | seed+grow, evaluate an aligned signed change, audit |
| TC-P2 | Misaligned change (better local residual, lower alignment) rejected with `fitness_below_threshold` | T-I2 tissue-scale fitness |
| TC-P3 | Aligned but impostor-signed change rejected with `not_creator_authorized` | sign with a non-creator scalar |
| TC-P4 | Tampered receipt chain → auditor reports `no_hidden_state` False (P-3) | edit `_receipts[0].payload_hash`, audit |
| TC-P5 | Grafted cell without intent inheritance → auditor reports `derived` False, ≥1 breach (P-1) | add a non-propagated cell, audit |
| TC-P6 | Audit with wrong creator public key → `authorized` False (P-2) | ExternalAuditor with impostor pubkey |

---

*This specification is the single source of truth for provably-derived self-modification.
Code must match exactly; any deviation = BUILD FAILURE.*
