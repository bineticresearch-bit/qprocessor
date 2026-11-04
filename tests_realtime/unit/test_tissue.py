"""
test_tissue.py — Tissue (organism) + Intent Shard contract tests.

Covers:
  * Current Tissue core behavior      -> TC-T1, TC-T2, TC-T3   (must pass now)
  * Intent Shard creator-alignment    -> INT-001..007          (gates the draft)
  * Tissue-scale fitness + derivation -> TC-T4, TC-T5, TC-T6

Spec: docs/spec/TISSUE.md  (+ LANE-ISA.md §4.2)

Run directly:   python3 tests_realtime/unit/test_tissue.py
Or via suite:   (added to scripts when realtime suite is wired up)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src_realtime.cell.cell import Cell, CellType
from src_realtime.cmp.protocol import CMPFrame, MessageType
from src_realtime.tissue.tissue import Tissue, TissueType, TissueStats


# ---------------------------------------------------------------------------
# Helpers: build a tissue with an exact "computer" role mix (alive cells).
# ---------------------------------------------------------------------------

def _build_computer_tissue(tissue_type=TissueType.GENERAL_PURPOSE):
    """One tissue holding exactly the default form_computer thresholds, alive."""
    t = Tissue(tissue_type=tissue_type)
    roles = [CellType.GPU] * 4 + [CellType.CPU] * 4 + \
            [CellType.MEMORY] * 8 + [CellType.NETWORK] * 2 + [CellType.IO] * 2
    cells = []
    for rt in roles:
        c = Cell()
        c.differentiate(rt)
        t.add_cell(c)
        cells.append(c)
    return t, cells


# ---------------------------------------------------------------------------
# TC-T1 — form_computer is all-or-nothing over ALIVE cells only.
# ---------------------------------------------------------------------------

def test_tc_t1_form_computer_all_or_nothing():
    """FORM-002/003: True iff every role threshold met by alive cells; killing one flips False."""
    t, _ = _build_computer_tissue()
    assert t.form_computer() is True, "exact-threshold tissue must form a computer"

    # Kill exactly one GPU cell -> gpu count 4->3 < 4 => not formed.
    gpus = [c for c in t.get_cells_by_type(CellType.GPU)]
    gpus[0].apoptosis()
    assert t.form_computer() is False, "killing one required role must break formation"

    # Dead cells never count (FORM-002): stats reflect the loss.
    stats = t.get_stats()
    assert stats.type_distribution.get("gpu", 0) == 3
    print("  ✓ TC-T1 form_computer all-or-nothing over alive cells")


# ---------------------------------------------------------------------------
# TC-T2 — broadcast excludes sender and skips dead cells in the count.
# ---------------------------------------------------------------------------

def test_tc_t2_broadcast_excludes_sender_and_dead():
    """D-2: delivered == (alive non-sender). 5-cell tissue, kill 1 -> deliver to 3."""
    t = Tissue()
    src = Cell(); a = Cell(); b = Cell(); c = Cell(); d = Cell()
    for cell in (src, a, b, c, d):
        t.add_cell(cell)
    d.apoptosis()  # dead -> skipped

    delivered = t.broadcast(src.get_id(), b"hello")
    assert delivered == 3, f"expected 3 deliveries (a,b,c), got {delivered}"
    for cell in (a, b, c):
        assert len(cell._inbox) == 1, "each alive non-sender gets exactly one frame"
    assert len(src._inbox) == 0, "sender must not receive its own broadcast"

    # Broadcast from an absent id is a no-op returning 0 (D-3).
    assert t.broadcast("nonexistent", b"x") == 0
    print("  ✓ TC-T2 broadcast excludes sender and dead cells")


# ---------------------------------------------------------------------------
# TC-T3 — send_message: unknown id -> False, known pair -> exactly one frame.
# ---------------------------------------------------------------------------

def test_tc_t3_send_message_semantics():
    """D-1/D-3: at-most-once delivery; unknown id is a no-op returning False."""
    t = Tissue()
    src = Cell(); dst = Cell()
    t.add_cell(src); t.add_cell(dst)

    # Unknown destination -> False, nothing logged.
    assert t.send_message(src.get_id(), "ghost", b"m") is False
    assert len(dst._inbox) == 0

    # Known pair -> True, exactly one frame delivered (at-most-once).
    before = len(t._message_log)
    assert t.send_message(src.get_id(), dst.get_id(), b"payload") is True
    assert len(dst._inbox) == 1
    assert len(t._message_log) == before + 1

    # Unknown source -> False.
    assert t.send_message("ghost", dst.get_id(), b"m2") is False
    print("  ✓ TC-T3 send_message at-most-once / unknown-id no-op")


# ---------------------------------------------------------------------------
# Intent Shard contract (INT-001..007). GATES the draft implementation.
# Import lazily so the Tissue-core tests above run even before INT is built.
# ---------------------------------------------------------------------------

def _import_intent():
    from src_realtime.tissue.intent_shard import (
        IntentShard, PurposeSection, Goal, SuccessModel, IntentReadOnlyError,
    )
    return IntentShard, PurposeSection, Goal, SuccessModel, IntentReadOnlyError


def test_int_001_construction_and_purpose_section():
    """INT-001/002: construct with a frozen PurposeSection; get_purpose returns it."""
    IntentShard, PurposeSection, Goal, SuccessModel, _ = _import_intent()
    purpose = PurposeSection(
        goals=[Goal(goal_id="g1", description="serve creator intent", weight=1.0)],
        constraints=("no hidden state",),
        success_criteria=SuccessModel(criteria={"alignment_threshold": 0.9}),
    )
    shard = IntentShard(b"creator_key_seed", purpose)
    got = shard.get_purpose()
    assert got is not None
    assert len(got.goals) == 1 and got.goals[0].goal_id == "g1"
    # PurposeSection is frozen (I-1 support): in-place mutation must fail.
    import dataclasses
    try:
        got.goals = ()  # type: ignore
        raised = False
    except dataclasses.FrozenInstanceError:
        raised = True
    assert raised, "PurposeSection must be a frozen dataclass"
    print("  ✓ INT-001/002 construction + frozen PurposeSection")


def test_int_003_creator_writable_only():
    """INT-003/I-1: creator actor writable; organism actor always False at this stage."""
    IntentShard, PurposeSection, Goal, SuccessModel, _ = _import_intent()
    purpose = PurposeSection(goals=[], constraints=(), success_criteria=None)
    shard = IntentShard(b"creator_key_seed", purpose)

    assert shard.is_creator_writable("creator") is True
    # Any non-creator actor (the organism / its cells) is read-only.
    assert shard.is_creator_writable("organism") is False
    assert shard.is_creator_writable(Cell().get_id()) is False
    print("  ✓ INT-003 creator-writable / organism-read-only (I-1)")


def test_int_004_write_purpose_readonly_error():
    """INT-004/I-1: organism write raises IntentReadOnlyError; creator write succeeds."""
    IntentShard, PurposeSection, Goal, SuccessModel, IntentReadOnlyError = _import_intent()
    purpose = PurposeSection(goals=[], constraints=(), success_criteria=None)
    shard = IntentShard(b"creator_key_seed", purpose)

    new_purpose = PurposeSection(
        goals=[Goal(goal_id="g2", description="refined intent", weight=1.0)],
        constraints=("no hidden state",), success_criteria=None,
    )
    try:
        shard.write_purpose("organism", new_purpose)
        raised = False
    except IntentReadOnlyError:
        raised = True
    assert raised, "organism write must raise IntentReadOnlyError"

    # Creator write succeeds and updates the stored purpose.
    shard.write_purpose("creator", new_purpose)
    assert shard.get_purpose().goals[0].goal_id == "g2"
    print("  ✓ INT-004 write_purpose read-only enforcement")


def test_int_005_propagate_to_daughter_content_unchanged():
    """INT-005/I-2: mitosis copies intent content verbatim; only lineage differs."""
    IntentShard, PurposeSection, Goal, SuccessModel, _ = _import_intent()
    purpose = PurposeSection(
        goals=[Goal(goal_id="g1", description="serve creator intent", weight=1.0)],
        constraints=("no hidden state",), success_criteria=None,
    )
    parent_shard = IntentShard(b"creator_key_seed", purpose)

    daughter = Cell()
    parent_shard.propagate_to_daughter(parent_shard, daughter)

    # The daughter now carries an Intent Shard with identical content.
    dshard = daughter.get_intent_shard()
    assert dshard is not None, "daughter must inherit an IntentShard"
    dp = dshard.get_purpose()
    pp = parent_shard.get_purpose()
    assert [g.goal_id for g in dp.goals] == [g.goal_id for g in pp.goals], \
        "intent content must be inherited unchanged (I-2)"
    assert dp.constraints == pp.constraints
    print("  ✓ INT-005 propagate_to_daughter inherits content unchanged (I-2)")


def test_int_006_verify_derivation():
    """INT-006/I-3: genuine descendant verifies True; grafted/broken lineage False."""
    IntentShard, PurposeSection, Goal, SuccessModel, _ = _import_intent()
    purpose = PurposeSection(goals=[], constraints=(), success_criteria=None)

    good = Cell(); bad = Cell()
    parent_shard = IntentShard(b"creator_key_seed", purpose)
    parent_shard.propagate_to_daughter(parent_shard, good)   # real descent
    parent_shard.propagate_to_daughter(parent_shard, bad)     # then break it

    assert parent_shard.verify_derivation(good) is True

    # Corrupt the daughter's lineage so ancestry no longer traces to seed.
    dshard = bad.get_intent_shard()
    dshard._lineage_hash = b"\x00" * 32  # break derivation chain (test seam)
    assert parent_shard.verify_derivation(bad) is False, \
        "broken lineage must fail derivation verification (I-3)"
    print("  ✓ INT-006 verify_derivation distinguishes genuine vs grafted")


def test_int_007_score_alignment_bounds():
    """INT-007: alignment score in [0,1]; higher intent-realization -> higher score."""
    IntentShard, PurposeSection, Goal, SuccessModel, _ = _import_intent()
    purpose = PurposeSection(
        goals=[Goal(goal_id="g1", description="serve creator intent", weight=1.0)],
        constraints=("no hidden state",), success_criteria=None,
    )
    shard = IntentShard(b"creator_key_seed", purpose)

    aligned = {"realizes_intent": 0.95}
    misaligned = {"realizes_intent": 0.20}
    s_hi = shard.score_alignment(aligned)
    s_lo = shard.score_alignment(misaligned)
    assert 0.0 <= s_lo <= s_hi <= 1.0, f"bounds/order violated: {s_lo}, {s_hi}"
    print("  ✓ INT-007 score_alignment bounded and monotone")


# ---------------------------------------------------------------------------
# TC-T4 — Tissue-scale fitness (T-I2): a self-serving-but-misaligned change is rejected.
# ---------------------------------------------------------------------------

def test_tc_t4_tissue_scale_fitness():
    """A member cell's locally-better residual that lowers tissue creator-alignment is not adopted."""
    from src_realtime.tissue.intent_shard import IntentShard, PurposeSection, Goal
    purpose = PurposeSection(
        goals=[Goal(goal_id="g1", description="serve creator intent", weight=1.0)],
        constraints=("no hidden state",), success_criteria=None,
    )

    t, cells = _build_computer_tissue()
    # Seed the tissue's shared intent (T-I1: one intent per tissue).
    t.set_intent_shard(IntentShard(b"creator_key_seed", purpose))

    # Two candidate self-modifications for a member cell:
    aligned_change   = {"realizes_intent": 0.95, "local_residual": 0.30}
    misaligned_change = {"realizes_intent": 0.20, "local_residual": 0.05}

    # Tissue-scale fitness must rank the intent-aligned change higher even though
    # its local residual is worse (w_creator dominates). See LANE-ISA §4.2 / EVO-101.
    f_hi = t.evaluate_fitness(aligned_change)
    f_lo = t.evaluate_fitness(misaligned_change)
    assert f_hi > f_lo, \
        "tissue-scale fitness must favor creator-alignment over local residual (T-I2)"

    # Adoption gate: misaligned change rejected despite better local metric.
    assert t.should_adopt(aligned_change) is True
    assert t.should_adopt(misaligned_change) is False
    print("  ✓ TC-T4 tissue-scale fitness favors creator-alignment (T-I2)")


# ---------------------------------------------------------------------------
# TC-T6 — derivation breach reported as covenant violation via audit.
# ---------------------------------------------------------------------------

def test_tc_t6_derivation_breach_audit():
    """A grafted cell with broken intent lineage surfaces exactly one derivation breach."""
    from src_realtime.tissue.intent_shard import IntentShard, PurposeSection, Goal
    purpose = PurposeSection(goals=[], constraints=(), success_criteria=None)

    t = Tissue()
    good = Cell(); bad = Cell()
    t.add_cell(good); t.add_cell(bad)
    seed = IntentShard(b"creator_key_seed", purpose)
    t.set_intent_shard(seed)
    seed.propagate_to_daughter(seed, good)
    seed.propagate_to_daughter(seed, bad)
    bad.get_intent_shard()._lineage_hash = b"\x00" * 32  # graft: break lineage

    report = t.get_alignment_report()
    assert report["total_cells"] == 2
    assert report["derivation_breaches"] == 1, \
        f"expected exactly one derivation breach, got {report['derivation_breaches']}"
    print("  ✓ TC-T6 derivation breach reported as covenant violation")


# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Portal (TISSUE.md §6): creator's interface into the synthetic universe.
# ---------------------------------------------------------------------------

def test_portal_build_universe_and_audit():
    """End-to-end: seed intent, grow role mix, form computer, audit clean."""
    from src_realtime import Portal
    p = Portal(b"binetic_creator_key_v1")
    res = p.build_universe(
        name="my_intel",
        goals=[{"goal_id": "g1", "description": "serve creator intent", "weight": 1.0}],
        constraints=["no hidden state"],
    )
    assert res["formed_computer"] is True, "default role mix must form a computer"
    audit = res["audit"]
    assert audit["seeded"] is True
    assert audit["derivation_breaches"] == 0, "freshly-grown cells all derive from seed (I-2)"
    assert audit["covenant_compliant"] is True

    obs = p.observe_tissue("my_intel")
    assert obs["type_distribution"]["gpu"] == 4 and obs["alive_cells"] == 20
    print("  ✓ Portal build_universe + clean audit (universe of intelligence)")


def test_portal_flags_grafted_non_derived_cell():
    """Grafting a cell without intent propagation surfaces exactly one derivation breach."""
    from src_realtime import Portal, CellType
    p = Portal(b"binetic_creator_key_v1")
    res = p.build_universe(name="org", goals=[{"goal_id": "g1", "description": "x", "weight": 1.0}])

    # Graft a rogue cell directly (no intent inheritance) -> hidden non-derived state.
    from src_realtime.cell.cell import Cell
    rogue = Cell(); rogue.differentiate(CellType.CPU)
    p._tissues["org"].add_cell(rogue)

    audit = p.audit("org")
    assert audit["derivation_breaches"] == 1, "exactly one non-derived cell must be flagged"
    assert audit["covenant_compliant"] is False, "a derivation breach is a covenant violation"
    print("  ✓ Portal flags grafted non-derived cell as covenant breach")


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    print("=== Tissue + Intent Shard Tests ===\n")
    for fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ {fn.__name__} FAILED:\n{traceback.format_exc()}")
    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    sys.exit(1 if failed else 0)
