# LANE-ISA Specification — 40B Lane Framing, Membrane ISA & Adaptive Evolution

## Single Source of Truth

**Version:** 1.0
**Status:** Active (spec-first; implementation pending per D³ build order)
**Referenced by (target):** `src/lane/framing.py`, `src/lane/matcher.py`,
`src/lane/isa.py`, `src/cmp/transport.py`
**Depends on:** HASH, CMP (§1.6), SHARD, TEMPORAL, COVENANT

---

## 0. Core Principle: The Packet Train IS the Header

A single datagram cannot carry a wide header within v4's 60-byte IP budget.
Therefore **the unit of meaning is not the datagram — it is an ordered train
of datagrams.** Each datagram carries one fixed-size lane (40 bytes) of a
logical header; reassembled at the membrane, `concat(lane_0 .. lane_N-1)`
is the executable header.

Consequences (invariants):

* **L-I1 (Ordering is semantics):** The sequence number is part of the
  program counter. A train executes only when lanes form a contiguous run
  starting at k=0; otherwise it buffers or drops per LANE-007.
* **L-I2 (Loss is control flow):** A missing lane mid-train is an ISA
  interrupt, not mere data loss. Reassembly-window expiry emits a sheaf
  residual identifying the failing edge/cell (fault localization).
* **L-I3 (Address = sequence):** Lane k of a train occupies address
  `base_addr + k` in v6 space; routing a train is prefix routing. The low
  order bits reserved for depth/θ/φ double as the lane index dimension.
* **L-I4 (Version floor / backward compatibility):** ISA version lives in
  lane 0. A membrane executes at `min(sender_version, local_version)`
  capability; any op it cannot execute degrades to `RECEIPT(seal-only)`,
  never drops the train. This is the concrete mechanism of COVENANT Layer 7.

---

## 1. Lane Framing (LANE-001 … LANE-008)

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| LANE-001 | `class LaneFrame` | lane_index, train_id, total_lanes, payload_40b, seq, is_final | LaneFrame | 🟡 |
| LANE-002 | `LaneFrame.serialize() -> bytes` | none | 56-byte datagram (16B routing hdr + 40B lane, CRC32; 60B total) | 🟡 |
| LANE-003 | `LaneFrame.deserialize(data: bytes) -> LaneFrame` | raw bytes | LaneFrame or raises `TruncatedLaneError` | 🟡 |
| LANE-004 | `class TrainAssembler` | train_id, expected_lanes, window_ns | TrainAssembler | 🟡 |
| LANE-005 | `TrainAssembler.feed(frame: LaneFrame) -> AssemblerState` | one lane frame | COMPLETE / PARTIAL / EXPIRED / REJECTED | 🟡 |
| LANE-006 | `TrainAssembler.reassembled_header() -> bytes` | none (COMPLETE only) | logical header bytes or raises `IncompleteTrainError` | 🟡 |
| LANE-007 | `class ReassemblyPolicy` | max_buffer_trains, window_ns, on_gap: str | ReassemblyPolicy | 🟡 |
| LANE-008 | `ReassemblyPolicy.on_expire(assembler) -> ResidualEvent` | expired assembler | ResidualEvent (sheaf input) with missing lane indices + edge hint | 🟡 |

### 1.1 Lane Datagram Format (60 bytes)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| ISA Ver (4b) | Msg Type (4b) | Flags (8b): FIN(1) RSV(7)     |   <- u32 vtf
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Lane Index k (8b) | Total Lanes N (8b) | Hop Count (8b)| Rsvd |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Train ID (32 bits)                                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Source Cell CRC-32 (32 bits, of cell id string)          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  [ base routing header = 16 bytes — pure routing, middlebox-safe ]
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Timestamp ns (64b) | Phase θ (16b) | Phase φ (16b)         |   <- lane temporal preamble
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Lane Op Data (28 bytes = 224 bits)                       |
+                                                           +
| ...                                                      |     [ lane payload = 40 bytes ]
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| CRC-32 over base header + lane payload (32 bits)         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Fixed size: **60 bytes** per datagram. The logical header width is unbounded in N; each additional lane adds one 60-byte datagram. Timestamp/phase are carried *in* the lane (per-lane arrival self-description for SYNC / PHASE_BANK), keeping the 16-byte base header pure routing so it survives middleboxes that only inspect IP.

### 1.2 Reassembly Window Rule (LANE-007)

* Buffer keyed by `train_id`. Accept frames with `lane_index < total_lanes`.
* **Contiguity rule:** execution trigger fires only when lanes `{0..N-1}` are
  all present. Gaps set the GAP flag on subsequent acks; policy decides:
  * `on_gap = "buffer"` (default): hold until window expiry, then EXPIRED → LANE-008.
  * `on_gap = "drop"`: immediate REJECTED + residual.
* Window default `window_ns = 25_000_000` (25 ms), configurable per membrane.

### 1.3 Loss-as-Interrupt Semantics (L-I2)

On EXPIRED/REJECTED, LANE-008 emits:

```
ResidualEvent(train_id, missing_lanes=[k...], last_seen_cell, expected_edge, residual_magnitude)
```

`residual_magnitude = |expected_arrival_window − actual| / window`. This event
feeds the sheaf sensor as a first-class observation (SHEAF-003 region input),
so a chronically dropping edge raises its anomaly score before packet-loss
metrics do.

---

## 2. Membrane ISA (ISA-001 … ISA-010)

The logical header is an **opcode stream**: each op reads/writes *lane
indices*, not byte offsets, so the ISA is dimension-free — extending N never
breaks in-flight trains.

| ID | Opcode | Lane Layout (within reassembled header) | Semantics at membrane | Receipt emitted |
|----|--------|------------------------------------------|----------------------|-----------------|
| ISA-001 | `FORWARD(dst_prefix, next_hops)` | lanes 1..2 | Advance train toward dst; increment hop count; re-seal | seal(hop) |
| ISA-002 | `DIFFERENTIATE(target_type, cfg_lanes)` | lane 3 + cfg region | Membrane cell reconfigures local engine per DIFF-* spec; records op in shard | op-receipt(type, before/after capability hash) |
| ISA-003 | `MITOSIS(fork_ratio, prefix_split)` | lanes 4..5 | Cell replicates (MITO-*); daughters inherit lane 0 version + split v6 prefix at fork point | lineage receipt(parent→daughters, address sweep bounds) |
| ISA-004 | `SYNC(t0_ns, phase_theta, phase_phi, basis)` | lanes 6..7 | Temporal sync: record two-way offset estimate into cell clock model; contributes one trilateration equation (TRIG spec) | sync receipt(Δt_est, σ_local) |
| ISA-005 | `MEASURE(basis, register_ref)` | lane 8 | Measure addressed pisphere register in given basis; result appended to payload receipts section | measurement receipt(outcome ∈ {0,1}, P-model check) |
| ISA-006 | `RECEIPT(seal_only: bool = False)` | lane 9 (or degraded form of any op per L-I4) | Seal-only execution: verify chain, append seal, no state change. Mandatory fallback for unknown ops | seal receipt(prev_seal_hash → new_seal_hash) |
| ISA-007 | `ROUTE_UPDATE(prefix, next_hop, ttl)` | lanes 10..11 | Update local route table entry; broadcast delta to neighbors via ROUTE msg (CMP-021) | routing receipt(old→new, residual impact est.) |
| ISA-008 | `PHASE_BANK(tones: list[(f_i, φ_i)])` | lanes 12..15 (4 tones × 32b) | Install multi-tone reference bank for trigonometric temporal measurement; each tone is a measured phase at arrival | tone receipt(fitted t₀, σ_fit) per TRIG-002 |
| ISA-009 | `EVOLVE(proposal_id, fitness_delta, parent_isa_ver)` | lanes 16..17 | Register an ISA mutation proposal in shard Operations; adoption decision deferred to EVOLVE_EVAL (ISA-010) | evolution receipt(proposal_id, Δfitness measured) |
| ISA-010 | `EVOLVE_EVAL(proposal_id, accept: bool)` | lane 18 | Apply or reject a registered proposal on this membrane only; acceptance is per-cell (no global fork) — selection happens across the lattice via receipts | adoption receipt(cell, version_before → after) |

### 2.1 Execution Rules

* **E-R1:** Ops execute in lane order k=0..N-1 at the destination membrane
  and at any intermediate cell whose multidimensional match (below) fires.
* **E-R2:** Every executed op MUST append a receipt to the payload receipts
  section before forwarding; a train arriving with missing receipts for
  executed ops is rejected (integrity, not just CRC).
* **E-R3:** Header authenticity: each hop seals `seal_k = MAC(header_0..k | seal_{k-1})`
  using an *avalanching* keyed hash (distinct from the non-avalanche lineage
  hash — two hashes, two jobs; see HASH spec amendment note §5).
* **E-R4:** Hop-count overflow → `APOPTOSIS`-style drop + residual (L-I2).

---

## 3. Multidimensional Match Algebra (MATCH-001 … MATCH-006)

A membrane decides which ops fire via a pattern over four axes simultaneously:

| Axis | Domain | Predicate form |
|------|--------|----------------|
| lane   | lane index k ∈ [0, N) | exact set / range |
| seq    | position + gap structure of train | contiguity regex (e.g. `0-2,4` = lanes 0..2 then gap at 3 then 4) |
| phase  | (θ, φ) within tolerance ε_θ, ε_φ | temporal window predicate: "train arrived in correct time bin" |
| lineage| shard-hash prefix of train origin | `startswith(hash_prefix)` → "descended from cell X" |

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| MATCH-001 | `class MembranePattern` | lane_spec, seq_regex, phase_window: (θ_c, φ_c, ε_θ, ε_φ) \| None, lineage_prefix: bytes \| None | MembranePattern | 🟡 |
| MATCH-002 | `MembranePattern.match(train_header, arrival_phase, origin_hash) -> bool` | reassembled header + context | True iff ALL non-None axes match (conjunction) | 🟡 |
| MATCH-003 | `class PatternCompiler` | patterns: list[MembranePattern] | compiled decision tree keyed on (opcode, lane) first | 🟡 |
| MATCH-004 | `PatternCompiler.compile() -> TwoStageMatcher` | none | two-stage matcher per cost model below | 🟡 |
| MATCH-005 | `TwoStageMatcher.stage1(header) -> candidate_ops: list[ISA-op]` | header only (no phase/lineage) | exact (opcode, lane) survivors — O(1) table lookup | 🟡 |
| MATCH-006 | `TwoStageMatcher.stage2(candidates, arrival_phase, origin_hash) -> fired_ops` | candidates + context | tolerance-checked survivors; empty list = no fire | 🟡 |

### 3.1 Two-Stage Cost Model (required for line-rate viability)

* **Stage 1** is a hash table over `(opcode_id, lane_index)` — exact, O(1),
  executed on every train. Patterns with no opcode/lane constraint are
  compile-time errors (they would defeat stage 1).
* **Stage 2** evaluates phase-window and lineage predicates only for the
  candidate set produced by stage 1 (expected size ≤ 4 ops per pattern bank).
* Compile-time validation: `MATCH-004` rejects any pattern whose stage-1 key
  collides with conflicting tolerances, forcing explicit priority order.

### 3.2 Temporal Predicates as First-Class Conditions

A `SYNC` op may fire only on `opcode ∧ lane_range ∧ phase_window ∧ lineage`.
The same train is therefore interpreted differently by different cells based
on where/when/how it arrived — context-sensitive header logic with **zero
payload inspection**, preserving middlebox survival of the control plane.

---

## 4. Adaptive ISA Evolution (EVO-001 … EVO-006)

The ISA is a genome; packet outcomes are fitness; differentiation/mitosis are
mutation operators. Fitness function (fixed, spec-mandated):

```
fitness = −( w_σ · trilateration_residual_mean + w_int · receipt_integrity_failures )
subject to: version-floor invariant L-I4 holding on every edge.
```

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| EVO-001 | `class FitnessLedger` | cell_ref, window_n_receipts | rolling (op-seq → outcome) ledger from shard Operations/Receipts | 🟡 |
| EVO-002 | `FitnessLedger.delta_fitness(proposal_id) -> float` | registered proposal | measured Δfitness vs parent variant over equal receipt counts | 🟡 |
| EVO-003 | `class EvolutionProposer` | membrane_ref, ledger | proposes: op reorder / lane addition / tolerance change (one mutation per cycle) | 🟡 |
| EVO-004 | `EvolutionProposer.propose() -> Proposal(proposal_id, parent_isa_ver, diff)` | none | immutable proposal record; ships as ISA-009 train to neighbors | 🟡 |
| EVO-005 | `class AdoptionGate` | min_delta: float (default +ε_min), min_receipts: int | per-cell adoption decision for a proposal | 🟡 |
| EVO-006 | `AdoptionGate.evaluate(proposal, ledger) -> bool` | proposal + local evidence | True iff Δfitness ≥ ε_min over ≥ min_receipts AND L-I4 holds | 🟡 |

### 4.1 Evolution Rules (the only "evolution" claims permitted)

* **EV-R1 (Monotone-per-adoption):** A change is adopted at a cell only if
  measured better than its parent by ≥ ε_min on the fitness function above.
  No global-optimality claim is made or testable; convergence of the lattice
  as a whole is NOT guaranteed (co-adaptive, moving target) and must not be
  asserted in docs/tests.
* **EV-R2 (Mitosis carries versions):** Mitosis forks both address prefix AND
  ISA version — daughter cells trial mutated opcode sets on half the lattice
  without forking the network; lineage hash traces variant ancestry.
* **EV-R3 (No silent mutation):** Every proposal is a receipt-logged event
  (ISA-009/010). An auditor can replay any cell's ISA history from receipts
  alone. This is the "no hidden state" invariant made executable: *any
  protocol state change without a receipt chain is a covenant violation.*

---

## 5. Cross-Spec Amendments Required (recorded here, SSOT rule)

1. **HASH spec:** add HASH-006 `avalanching_mac(key, data) -> bytes` for the
   E-R3 seal chain (security role). Non-avalanche hash retains lineage/
   similarity role only. Two hashes, two jobs — registry §1.1 must split.
2. **CMP spec:** CMP-004 transport gains `LANE_TRAIN` mode; UDP port 2837
   carries lane datagrams (v4 compat path); v6 native path uses extension
   header chain with train_id in a destination-option block.
3. **SHEAF spec:** SHEAF sensor input set extended with LANE-008 residual
   events as region observations.

---

## 6. Test Cases (must exist before implementation; D³ gate)

| TC | Asserts | Method |
|----|---------|--------|
| TC-L1 | A 3-lane train reassembles to the exact logical header bytes | build lanes, feed in order, compare `reassembled_header()` |
| TC-L2 | Out-of-order arrival (2,0,1) still reaches COMPLETE; execution order is lane order not arrival order | shuffle feed sequence, assert op-execution log == [op@0, op@1, op@2] |
| TC-L3 | Missing lane 1 → window expiry → EXPIRED + ResidualEvent naming missing=[1] | drop one frame, advance clock past window_ns |
| TC-L4 | Unknown opcode at older membrane degrades to RECEIPT(seal-only); train not dropped (L-I4) | send ISA-008 to ver=1 membrane expecting seal receipt only |
| TC-L5 | Seal chain: corrupting any prior lane invalidates all subsequent seals (E-R3, avalanching) | flip 1 bit in lane 2, assert MAC verification fails at lane ≥ 2 |
| TC-L6 | Phase-window match: identical train fires SYNC inside window and NOT outside ε_φ tolerance | two arrival phases ±(ε+δ), assert fire/no-fire split |
| TC-L7 | Lineage axis: pattern with prefix P matches only trains whose origin hash starts with P | 3 origins, 1 matching prefix |
| TC-L8 | Evolution gate: proposal with Δfitness < ε_min rejected; ≥ ε_min over min_receipts accepted (EV-R1) | synthetic ledgers both sides of threshold |
| TC-L9 | **Empirical anchor:** two localhost cells sweep contiguous v6 loopback prefix as 3-lane train over UDP/2837, one lane carries SYNC(ISA-004); assert reassembled execution AND recovered clock offset < σ_fit against a known injected delay (target: 50 µs injection, recovered within 10×σ) | real sockets, `perf_counter_ns`, measured not computed |
| TC-L10 | Version floor: parent ver=2 train + daughter ver=3 membrane → executes at ver=2 capability set; no op loss beyond seal-degradation (L-I4) | mixed-version pair, assert per-op outcomes |

---

## 7. Build Order (appended to REGISTRY §3.2)

10. **LANE** — depends on CMP, HASH(avalanching MAC), TEMPORAL
    * LANE framing → Matcher → ISA exec → Evolution ledger
    * TC-L9 is the empirical gate: until it passes with measured σ, all
      temporal-precision claims in public docs MUST carry the qualifier
      "theoretical" (per D³ no-deviation rule).

---

*This specification is the single source of truth for lane framing, membrane
ISA semantics, multidimensional matching, and adaptive evolution. Code must
match exactly; any deviation = BUILD FAILURE.*
