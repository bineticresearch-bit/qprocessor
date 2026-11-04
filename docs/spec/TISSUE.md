# TISSUE Specification — Organism-Level Organization & Creator-Intent Alignment

## Single Source of Truth

**Version:** 1.0
**Status:** Active (spec-first; existing `src_realtime/tissue/` implementation must match)
**Referenced by (target):** `src_realtime/tissue/tissue.py`, `src_realtime/__init__.py`
**Depends on:** CELL, CMP (§1.6), HASH, GENESIS (Layer 2 epigenetic, Layer 7 Covenant), LANE-ISA §4.2

---

## 0. Core Principle: Tissue IS the Unit of Loyalty

A single cell optimizing only its own residual can drift — it is locally rational
and globally disloyal. **Loyalty is an organism-scale property**, so it must be
evaluated and enforced at the scale where "the whole" exists: the **Tissue**.

```
┌─────────────────────────────────────────────────────────────────────┐
│   cell  → differentiates → mitoses (individual units)              │
│   tissue = a group of cells sharing ONE Intent Shard + ONE fitness  │
│           evaluation, so self-modification of any member is judged  │
│           against the ORGANISM'S purpose, not its own               │
│                                                                     │
│   The Tissue is where LANE-ISA §4.2 (creator-aligned fitness)       │
│   becomes real: it is the seat of the creature's values.            │
└─────────────────────────────────────────────────────────────────────┘
```

**Normative invariants:**

* **T-I1 Single intent per tissue.** Every cell in a Tissue inherits the same
  Intent Shard (LANE-ISA §4.2.2, I-2). A tissue with two different intents is not
  one organism — it is a federation, and federations are out of scope here.
* **T-I2 Fitness evaluated at tissue scale.** The three-term fitness function
  (LANE-ISA §4.2) is computed over the *tissue's aggregate behavior*, so a member
  cell may not adopt a change that helps itself while lowering the organism's
  creator-alignment term. Adoption gate (EV-R1/EVO-006) operates on tissue fitness,
  not per-cell fitness.
* **T-I3 Covenant bounds apply to the whole.** The immutable floor (Covenant Layer 7)
  is checked at both cell and tissue level; a tissue that violates a bound drags its
  members into non-compliance. Fitness never overrides covenant (LANE-ISA §4.2.5).

---

## 1. Tissue Types — `TissueType`

| ID | Enum Value | String | Meaning | Status |
|----|-----------|--------|---------|--------|
| TISSUE-T1 | `COMPUTE_CLUSTER` | `"compute_cluster"` | Dense parallel compute (GPU-heavy) | 🟡 |
| TISSUE-T2 | `MEMORY_BANK` | `"memory_bank"` | Storage / register-lattice tissue | 🟡 |
| TISSUE-T3 | `NETWORK_FABRIC` | `"network_fabric"` | Boundary / CMP routing tissue | 🟡 |
| TISSUE-T4 | `IO_GATEWAY` | `"io_gateway"` | Input/output edge tissue | 🟡 |
| TISSUE-T5 | `GENERAL_PURPOSE` | `"general_purpose"` | Default; mixed roles, forms a full computer | 🟢 (impl exists) |

---

## 2. Tissue Core — `Tissue`

A functional unit of organized Cells with real inter-cell communication via CMP
(loopback transport) and emergent-computer formation from differentiated cells.

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| TISSUE-001 | `class Tissue` | tissue_type: TissueType = GENERAL_PURPOSE, name: str \| None | Tinstance (empty, loopback CMP transport) | 🟢 |
| TISSUE-002 | `Tissue.add_cell(cell)` | cell: Cell | None — indexed by `cell.get_id()` | 🟢 |
| TISSUE-003 | `Tissue.remove_cell(cell_id)` | str | removed Cell \| None | 🟢 |
| TISSUE-004 | `Tissue.get_cell(cell_id)` | str | Cell \| None | 🟢 |
| TISSUE-005 | `Tissue.get_cells_by_type(cell_type)` | CellType | list[Cell] — alive cells of that type only | 🟢 |
| TISSUE-006 | `Tissue.send_message(src_cell_id, dst_cell_id, message, msg_type=SIGNAL)` | ids + bytes payload | bool — False if either id absent; else delivers CMPFrame to dst inbox and logs it | 🟢 |
| TISSUE-007 | `Tissue.broadcast(src_cell_id, message, msg_type=SIGNAL)` | src id + payload | int — count delivered (excludes sender; alive cells only) | 🟢 |
| TISSUE-008 | `Tissue.get_stats()` | none | TissueStats (see §3) | 🟢 |
| TISSUE-009 | `Tissue.form_computer(gpu_count=4, cpu_count=4, memory_count=8, network_count=2, io_count=2)` | role thresholds | bool — True iff alive cells of each type meet/exceed the threshold (see §5) | 🟢 |
| TISSUE-010 | `Tissue.kill_all()` | none | int — number of living cells that underwent apoptosis | 🟢 |

**Message-delivery semantics (normative):**

* **D-1 At-most-once, in-memory.** Delivery is synchronous over loopback; a frame
  appended to the destination inbox exactly once per `send_message`/`broadcast`.
  No retries, no reordering guarantee beyond insertion order. (Durability/receipt
  chaining for *protocol state* changes remains the LANE-ISA EV-R3 concern, not
  tissue messaging.)
* **D-2 Sender exclusion on broadcast.** The sender never receives its own
  broadcast; dead cells are skipped and do not count toward the return value.
* **D-3 Unknown id is a no-op, not an error.** `send_message` to/from an absent id
  returns False without raising; `broadcast` from an absent id returns 0.

---

## 3. Tissue Statistics — `TissueStats`

| ID | Field | Type | Meaning | Status |
|----|-------|------|---------|--------|
| TISSUE-S1 | total_cells | int | all cells (alive + dead) currently registered | 🟢 |
| TISSUE-S2 | alive_cells | int | cells where `is_alive()` is True | 🟢 |
| TISSUE-S3 | dead_cells | int | cells where `is_alive()` is False | 🟢 |
| TISSUE-S4 | type_distribution | Dict[str,int] | per-type count of **alive** cells only, keyed by `CellType.value` | 🟢 |
| TISSUE-S5 | total_generations | int | sum of `get_generation()` over all registered cells (lineage depth proxy) | 🟢 |
| TISSUE-S6 | uptime_s | float | wall-clock seconds since tissue creation | 🟢 |

---

## 4. Intent Shard — the stable target of creator alignment 🔵

The Intent Shard is a **special shard** that encodes what the creator actually
values (goals, constraints, "what counts as success") as first-class data. It is
the object against which `creator_alignment` (LANE-ISA EVO-102) scores every cell
and tissue. This section spec's it so §4 of LANE-ISA has a concrete target type.

> Status note: the Intent Shard extends `SelfDescribingShard` with one additional
> normative section ("Purpose") and is **not yet implemented** — it is specified
> first per D³, then built (build order §8). The existing Tissue core (§1–3) ships
> independently of this section.

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| INT-001 | `class IntentShard(SelfDescribingShard)` | creator_key, purpose: PurposeSection | IntentShard — shard with an extra "Purpose" section (goals, constraints, success criteria) | 🔵🟡 |
| INT-002 | `IntentShard.get_purpose() -> PurposeSection` | none | the goals/constraints/success-criteria structure | 🔵🟡 |
| INT-003 | `IntentShard.is_creator_writable(actor) -> bool` | actor identity | True iff creator holds Genesis Layer-2 authority; **organism actors always False at this stage** (I-1, LANE-ISA §4.2.2) | 🔵🟡 |
| INT-004 | `IntentShard.write_purpose(actor, new_purpose)` | actor + PurposeSection | None on success; raises `IntentReadOnlyError` if not creator-writable (I-1) | 🔵🟡 |
| INT-005 | `IntentShard.propagate_to_daughter(parent_shard, daughter_cell)` | parent intent shard, daughter Cell | None — embeds the **same content** in the daughter; lineage hash records descent (I-2) | 🔵🟡 |
| INT-006 | `IntentShard.verify_derivation(cell) -> bool` | cell | True iff the cell's Intent Shard ancestry traces to the founding seed via `verify_lineage_chain` (GEN-006, I-3) — "derived from creator intent" as a checkable property | 🔵🟡 |
| INT-007 | `IntentShard.score_alignment(predicted_behavior) -> float` | model of predicted future behavior | [0.0, 1.0] — how well the prediction realizes purpose; feeds EVO-102 | 🔵🟡 |

**Normative properties (mirror LANE-ISA §4.2.2):**

* **I-1 Creator-writable / organism-read-only.** Only Layer-2 authority may call
  `write_purpose` successfully. The organism interprets and pursues purpose; it does
  not edit what "good" means. This is the anti-Goodhart floor — the target cannot
  drift to match the creature.
* **I-2 Inherited unchanged in content.** Mitosis copies Intent Shard *content*
  verbatim into daughters; only the lineage hash differs (records descent). Purpose
  divides with the organism but does not mutate on division.
* **I-3 Derivation-verifiable.** `verify_derivation` proves, from receipts + lineage
  alone, that a cell's purpose descends from the founding seed — no hidden origin.

**PurposeSection structure (normative):**

```python
@dataclass(frozen=True)
class PurposeSection:
    goals: List[Goal]                 # ordered; higher index = lower priority
    constraints: Tuple[str, ...]      # hard conditions that must always hold
    success_criteria: SuccessModel    # what "realizing intent" means (feeds INT-007)

@dataclass(frozen=True)
class Goal:
    goal_id: str
    description: str
    weight: float                     # relative importance within purpose
```

* `PurposeSection` is **frozen** — mutation only via `write_purpose` (I-1), never by
  in-place field edits. The creator's intent model is immutable to the organism by
  construction, not just by policy.

---

## 5. Emergent Computer Formation — `form_computer` semantics

A Tissue "forms a computer" when it holds enough **alive** cells of each role to act
as one functional agent. This is where "the whole is an organism that can act"
becomes testable, and the loyalty unit (tissue) gains agency.

| ID | Rule | Detail | Status |
|----|------|--------|--------|
| FORM-001 | Role thresholds are parameters | defaults gpu=4, cpu=4, memory=8, network=2, io=2; caller may override per-tissue | 🟢 |
| FORM-002 | Counts use **alive** cells only | `get_cells_by_type` filters to alive cells (TISSUE-005); dead cells never count toward formation | 🟢 |
| FORM-003 | All-or-nothing boolean | returns True iff EVERY role meets/exceeds its threshold; partial satisfaction is False | 🟢 |
| FORM-004 | Formation ≠ capability claim | a formed computer can *act as one agent* (shared intent + tissue-scale fitness, T-I1/T-I2); it does not assert global optimality (EV-R1) | 🔵🟡 |

---

## 6. Alignment Reporting — organism → Demiurge console 🔵

So the creator can audit "is this whole organism still derived from my intent?",
the tissue reports alignment upward. This is the observable surface of loyalty.

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| ALIGN-001 | `Tissue.get_alignment_report() -> AlignmentReport` | none | aggregate creator-alignment score, per-cell scores, derivation status (all cells verified via INT-006?), covenant compliance | 🔵🟡 |
| ALIGN-002 | `DemiurgeConsole.audit_tissue(tissue_id) -> AuditReport` | tissue id | extends DEM-008: reports organism-level alignment + any Intent Shard derivation failure as a **covenant breach** | 🔵🟡 |

* A cell whose `verify_derivation` returns False is reported as a **derivation
  breach** — the strongest signal that hidden, non-derived state has entered the
  organism. This makes "no hidden anti-creator-intent state" an auditable invariant.

---

## 7. Cross-Spec Amendments Required (recorded here, SSOT rule)

1. **GENESIS spec:** `GEN-003` (`embed_in_cell`) and `GEN-004`
   (`propagate_to_daughter`) extended to carry the Intent Shard content, not only a
   key — so purpose is inherited genetically (I-2). Layer 2 epigenetic authority is
   the sole writer of intent contents (I-1).
2. **SHARD spec:** `SelfDescribingShard` gains an optional "Purpose" section;
   `IntentShard` subclasses it (INT-001). The self-reference hash must cover the
   Purpose section so purpose changes are detectable in lineage.
3. **REGISTRY.md:** add §1.x "Tissue — Organism Organization & Intent Alignment"
   pointing here, and append TISSUE to build order (§8 below).

---

## 8. Build Order (appended to REGISTRY §3.2)

**TISSUE** — depends on CELL, CMP, HASH, GENESIS (Layer 2/7), LANE-ISA §4.2:
1. Tissue core (TISSUE-001…010) + stats (§1–3) — *already implemented; add tests.*
2. Intent Shard type (INT-001…007) + PurposeSection — spec-first, then build.
3. Tissue-scale fitness wiring: EVO-101/102 evaluated over the tissue aggregate
   (T-I2), adoption gate on tissue fitness.
4. Alignment reporting (ALIGN-001/002) into Demiurge console.

**Deferred (last door):** organism-proposed intent edits via a receipt-logged proposal
channel with creator approval (LANE-ISA §4.2.4). Not built until steps 1–4 have
demonstrated reliable convergence toward a fixed target.

---

## 9. Test Cases (must exist before implementation; D³ gate)

| TC | Asserts | Method |
|----|---------|--------|
| TC-T1 | `form_computer` returns True iff all role thresholds met by **alive** cells; killing one required cell flips to False | build exact-threshold tissue, assert True, apoptosis one GPU, assert False |
| TC-T2 | Broadcast excludes sender and skips dead cells in the count | 5-cell tissue, kill 1, broadcast from alive src, assert delivered == 3 (not 4) |
| TC-T3 | `send_message` to unknown id returns False without raising; known pair delivers exactly one frame to dst inbox | absent id → False + empty log delta; present pair → len(dst._inbox)+1 |
| TC-T4 | T-I2 tissue-scale fitness: a change that raises a single cell's residual but lowers the tissue creator-alignment term is rejected by the adoption gate | two proposals, one self-serving-but-misaligned, assert reject on tissue fitness |
| TC-T5 | I-1 read-only intent: organism actor `write_purpose` raises IntentReadOnlyError; creator actor succeeds and next daughter inherits content unchanged (I-2) | INT-003/004 + mitosis propagation, compare PurposeSection equality in daughter |
| TC-T6 | I-3 derivation audit: a grafted cell whose intent shard lacks founding-seed lineage is reported as a derivation breach by `audit_tissue` | build one verified cell + one with broken lineage hash, assert exactly one breach |

---

*This specification is the single source of truth for organism-level organization
and creator-intent alignment. Code must match exactly; any deviation = BUILD FAILURE.*
