"""
Multidimensional Match Algebra — MATCH-001 through MATCH-006

A membrane decides which ISA ops fire via a pattern over four axes
simultaneously: lane index, sequence/gap structure, phase window (temporal
predicate), and lineage prefix. Compiled to a two-stage cost model so the
hot path is an O(1) table lookup with tolerance checks only on survivors.

Spec Reference: docs/spec/LANE-ISA.md §3
"""

import math
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# --- MATCH-001: MembranePattern ---------------------------------------------

@dataclass(frozen=True)
class PhaseWindow:
    """Temporal predicate: (θ_c, φ_c) center with tolerances ε_θ, ε_φ."""
    theta_center: float
    phi_center: float
    eps_theta: float = math.pi / 8
    eps_phi: float = math.pi / 4

    def contains(self, theta: float, phi: float) -> bool:
        """MATCH-002 support: circular tolerance test on both axes."""
        dtheta = abs(_ang_diff(theta, self.theta_center))
        # φ is a phase (mod 2π); θ in this codebase is clamped [0, π] so linear.
        dphi = abs(_ang_diff(phi, self.phi_center))
        return dtheta <= self.eps_theta and dphi <= self.eps_phi


def _ang_diff(a: float, b: float) -> float:
    """Signed smallest angular difference in (-π, π]."""
    d = (a - b + math.pi) % (2 * math.pi) - math.pi
    return abs(d)


@dataclass(frozen=True)
class MembranePattern:
    """
    MATCH-001: A four-axis firing condition for one ISA op.

    All non-None axes must match (conjunction, MATCH-002). Patterns with no
    opcode/lane constraint are compile-time errors — they would defeat the
    stage-1 table (spec §3.1).

    lane_spec: set or range of allowed lane indices for THIS op's payload slot.
    seq_regex: contiguity regex over train structure, e.g. "0-2,4" means lanes
               0..2 present then a gap at 3 then lane 4 (L-I1/L-I2 aware).
    phase_window: temporal predicate — "train arrived in the correct time bin".
    lineage_prefix: origin shard-hash prefix — "descended from cell X".

    Spec: docs/spec/LANE-ISA.md #MATCH-001
    """
    opcode_id: int                      # ISA op this pattern arms (stage-1 key)
    lane_spec: frozenset                # allowed lane indices for the op slot
    seq_regex: str = ".*"               # gap-structure regex over present lanes
    phase_window: Optional[PhaseWindow] = None
    lineage_prefix: Optional[bytes] = b""

    def __post_init__(self):
        if not self.lane_spec:
            raise ValueError("lane_spec must be non-empty (stage-1 requires a key)")


# --- MATCH-002: match --------------------------------------------------------

def pattern_match(pattern: MembranePattern, present_lanes: frozenset,
                  arrival_theta: float, arrival_phi: float,
                  origin_hash: bytes) -> bool:
    """
    MATCH-002: True iff ALL non-None axes match (conjunction).

    Axes evaluated:
      1. seq   — present-lane structure must satisfy pattern.seq_regex
      2. phase — arrival (θ, φ) inside pattern.phase_window (if set)
      3. lineage — origin_hash startswith pattern.lineage_prefix (if non-empty)

    The lane axis is handled by the stage-1 table (see TwoStageMatcher); here we
    verify the *structural* axes so a candidate from stage 1 can be confirmed.

    Spec: docs/spec/LANE-ISA.md #MATCH-002
    """
    # Axis 1: sequence/gap structure.
    if not _seq_matches(pattern.seq_regex, present_lanes):
        return False
    # Axis 2: temporal window.
    if pattern.phase_window is not None and \
            not pattern.phase_window.contains(arrival_theta, arrival_phi):
        return False
    # Axis 3: lineage prefix.
    lp = pattern.lineage_prefix or b""
    if lp and not origin_hash.startswith(lp):
        return False
    return True


def _seq_matches(seq_regex: str, present_lanes: frozenset) -> bool:
    """Interpret a compact gap-regex like '0-2,4' or '*': match present lanes."""
    seq_regex = (seq_regex or ".*").strip()
    if seq_regex in ("", "*", ".*"):
        return True
    # Grammar: comma-separated items; each item is either 'k' or 'a-b'.
    try:
        required = set()
        for item in seq_regex.split(","):
            item = item.strip()
            if "-" in item:
                a, b = item.split("-")
                required.update(range(int(a), int(b) + 1))
            else:
                required.add(int(item))
    except ValueError:
        # Fall back to treating as an arbitrary regex over the sorted lane list.
        return re.fullmatch(seq_regex, ",".join(map(str, sorted(present_lanes)))) is not None
    # Structural match: every required lane present; extra lanes allowed (gaps ok).
    return required <= set(present_lanes)


# --- MATCH-003/004: PatternCompiler ------------------------------------------

class PatternCompileError(Exception):
    """MATCH-004: a pattern bank cannot be compiled to the two-stage model."""


@dataclass
class _Stage1Entry:
    opcode_id: int
    lane_index: int
    patterns: List[MembranePattern] = field(default_factory=list)


class TwoStageMatcher:
    """
    MATCH-004/005/006 result of compilation.

    Stage 1 (MATCH-005): hash table keyed on (opcode_id, lane_index) — exact,
        O(1), run on every reassembled header; returns candidate ops only.
    Stage 2 (MATCH-006): evaluates phase-window + lineage (+seq) predicates for
        the small candidate set produced by stage 1.

    Spec: docs/spec/LANE-ISA.md #MATCH-004/005/006
    """

    def __init__(self, table: dict):
        self._table = table          # (opcode_id, lane_index) -> [MembranePattern]
        self._opcodes = {k[0] for k in table}

    def stage1(self, header_opcode_lanes: List[Tuple[int, int]]) -> List[int]:
        """
        MATCH-005: Given the (opcode_id, lane_index) pairs found in a reassembled
        header, return candidate opcodes present in this membrane's table.

        O(len(header)) table lookups; no tolerance math here.
        """
        fired = []
        seen = set()
        for opcode_id, lane_index in header_opcode_lanes:
            if (opcode_id, lane_index) in self._table and opcode_id not in seen:
                fired.append(opcode_id)
                seen.add(opcode_id)
        return fired

    def stage2(self, candidates: List[int], present_lanes: frozenset,
               arrival_theta: float, arrival_phi: float,
               origin_hash: bytes) -> List[int]:
        """
        MATCH-006: Confirm candidates via the structural/temporal/lineage axes.

        Returns the subset of candidate opcodes whose patterns fully match.
        Empty list = no fire (train passes through without executing here).
        """
        confirmed = []
        for opcode_id in candidates:
            # Any pattern armed at this opcode that matches confirms a fire.
            for (op, lane), pats in self._table.items():
                if op != opcode_id:
                    continue
                for pat in pats:
                    if pattern_match(pat, present_lanes, arrival_theta,
                                     arrival_phi, origin_hash):
                        confirmed.append(opcode_id)
                        break
                if opcode_id in confirmed:
                    break
        return confirmed


class PatternCompiler:
    """
    MATCH-003: Compiles a list of MembranePatterns into a TwoStageMatcher.

    Compile-time validation (spec §3.1): rejects any pattern whose stage-1 key
    collides with conflicting tolerances — i.e., two patterns sharing the same
    (opcode_id, lane_index) but with incompatible phase windows or lineage
    prefixes are an error unless an explicit priority is given.

    Spec: docs/spec/LANE-ISA.md #MATCH-003
    """

    def __init__(self, patterns: List[MembranePattern]):
        self.patterns = list(patterns)

    def compile(self) -> TwoStageMatcher:
        """MATCH-004: Build the two-stage matcher; raise PatternCompileError on conflict."""
        table: dict = {}
        for pat in self.patterns:
            if not isinstance(pat.lane_spec, frozenset):
                pat = MembranePattern(
                    opcode_id=pat.opcode_id, lane_spec=frozenset(pat.lane_spec),
                    seq_regex=pat.seq_regex, phase_window=pat.phase_window,
                    lineage_prefix=pat.lineage_prefix)
            for lane in pat.lane_spec:
                key = (pat.opcode_id, lane)
                bucket = table.setdefault(key, [])
                # Conflict detection: same key, different non-None constraints.
                for other in bucket:
                    if self._conflicts(pat, other):
                        raise PatternCompileError(
                            f"stage-1 key ({pat.opcode_id},{lane}) has conflicting "
                            f"tolerances between patterns; add explicit priority")
                bucket.append(pat)
        return TwoStageMatcher(table)

    @staticmethod
    def _conflicts(a: MembranePattern, b: MembranePattern) -> bool:
        """Two patterns conflict if both constrain an axis incompatibly."""
        # Phase windows that are disjoint => conflicting for the same key.
        if a.phase_window is not None and b.phase_window is not None:
            if not _windows_overlap(a.phase_window, b.phase_window):
                return True
        # Lineage prefixes where one is not a prefix of the other => disjoint.
        la = a.lineage_prefix or b""
        lb = b.lineage_prefix or b""
        if la and lb and not (la.startswith(lb) or lb.startswith(la)):
            return True
        return False


def _windows_overlap(a: PhaseWindow, b: PhaseWindow) -> bool:
    """Conservative overlap test on the φ axis (θ treated linearly)."""
    dphi = abs(_ang_diff_signed(a.phi_center, b.phi_center))
    if dphi > a.eps_phi + b.eps_phi:
        return False
    if abs(a.theta_center - b.theta_center) > a.eps_theta + b.eps_theta:
        return False
    return True


def _ang_diff_signed(a: float, b: float) -> float:
    return (a - b + math.pi) % (2 * math.pi) - math.pi
