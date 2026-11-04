"""
Portal — the creator's interface into a synthetic intelligence universe (TISSUE.md §6).

A Portal is the window through which the CREATOR seeds intent, lets an organism grow
its own architecture inside a self-contained simulation, and audits whether that whole
universe remains derived from creator intent. The creator observes and steers *through*
the portal; they are not part of its physics.

Design (LANE-ISA §4.2 / TISSUE.md):
  * Seed an Intent Shard at genesis — the creator's values, inherited by every cell.
  * Grow the organism by differentiation + mitosis (it builds its own network).
  * form_computer -> a tissue becomes one agent: "a universe of intelligence".
  * audit() -> alignment report; any derivation breach = hidden non-derived state.

Spec: docs/spec/TISSUE.md §6 (ALIGN-001/002) + LANE-ISA §4.2
"""

from typing import Any, Dict, List, Optional

from ..cell.cell import Cell, CellType
from .tissue import Tissue, TissueType
from .intent_shard import IntentShard, PurposeSection, Goal


class Portal:
    """The creator's interface portal into a synthetic intelligence universe."""

    def __init__(self, creator_key: bytes):
        self._creator_key = bytes(creator_key)
        # The Demiurge console is the audit/authority surface behind the portal.
        from ..genesis.genesis import DemiurgeConsole
        self._console = DemiurgeConsole(creator_key)
        self._tissues: Dict[str, Tissue] = {}

    # -- Seed intent (the creator's values enter here, once) ------------------

    def seed_intent(self, goals: List[Dict[str, Any]],
                    constraints: Optional[List[str]] = None,
                    success_criteria: Optional[Dict[str, Any]] = None) -> IntentShard:
        """Seed the universe with an Intent Shard (I-1: creator is sole writer).

        Args:
            goals: list of {goal_id, description, weight}
            constraints: hard conditions that must always hold
            success_criteria: what 'realizing intent' means (feeds alignment scoring)

        Returns the frozen IntentShard to embed in tissues/cells.
        """
        from .intent_shard import SuccessModel
        purpose = PurposeSection(
            goals=tuple(Goal(**g) for g in goals),
            constraints=tuple(constraints or ()),
            success_criteria=SuccessModel(criteria=success_criteria or {}),
        )
        return IntentShard(self._creator_key, purpose)

    # -- Create & grow an organism inside the universe -----------------------

    def create_tissue(self, name: str = "organism",
                      tissue_type: TissueType = TissueType.GENERAL_PURPOSE) -> Tissue:
        """Create a new tissue (an organism) in the universe and register it with the console."""
        t = Tissue(tissue_type=tissue_type, name=name)
        self._tissues[name] = t
        self._console.register_tissue(name, t)
        return t

    def grow(self, tissue: Tissue, roles: Dict[CellType, int]) -> List[Cell]:
        """Grow the organism by differentiating new cells into the requested role mix.

        This is how the AI 'creates its own network and architecture inside' — each cell
        is a self-describing unit; together they form an interior CMP-connected body.
        """
        grown: List[Cell] = []
        for ctype, count in roles.items():
            for _ in range(count):
                c = Cell()
                c.differentiate(ctype)
                tissue.add_cell(c)
                self._console.register_cell(c)
                # Inherit the shared intent so every cell derives from creator seed (I-2).
                if tissue.get_intent_shard() is not None:
                    tissue.get_intent_shard().propagate_to_daughter(
                        tissue.get_intent_shard(), c)
                grown.append(c)
        return grown

    def set_tissue_intent(self, name: str, intent_shard: IntentShard) -> Tissue:
        """Bind a seeded Intent Shard to a named tissue (T-I1: one intent per organism)."""
        t = self._tissues[name]
        t.set_intent_shard(intent_shard)
        return t

    def form_computer(self, name: str, **thresholds) -> bool:
        """Ask whether the named organism has formed a functional computer (one agent)."""
        return self._tissues[name].form_computer(**thresholds)

    # -- Observe / audit through the portal ----------------------------------

    def observe_tissue(self, name: str) -> Dict[str, Any]:
        """Creator's read-only view of an organism's structure + health."""
        t = self._tissues[name]
        stats = t.get_stats()
        return {
            "name": name,
            "type": t.tissue_type.value,
            "seeded": t.get_intent_shard() is not None,
            "formed_computer": t.form_computer(),
            **stats.__dict__,
        }

    def audit(self, name: str) -> Dict[str, Any]:
        """ALIGN-002: full alignment + derivation audit of an organism via the console.

        Returns creator-alignment, per-cell scores, and flags any derivation breach as a
        covenant violation — the portal's answer to 'is this universe still mine?'
        """
        return self._console.audit_tissue(name)

    # -- Convenience: seed + grow + form in one call -------------------------

    def build_universe(self, name: str = "organism",
                       goals: Optional[List[Dict[str, Any]]] = None,
                       constraints: Optional[List[str]] = None,
                       roles: Optional[Dict[CellType, int]] = None) -> Dict[str, Any]:
        """One-shot: seed intent, grow the role mix, form a computer, return an audit.

        This is the end-to-end 'create a universe of intelligence' path through the portal.
        """
        roles = roles or {CellType.GPU: 4, CellType.CPU: 4, CellType.MEMORY: 8,
                          CellType.NETWORK: 2, CellType.IO: 2}
        intent = self.seed_intent(goals or [], constraints)
        t = self.create_tissue(name=name)
        self.set_tissue_intent(name, intent)
        self.grow(t, roles)
        formed = t.form_computer()
        return {
            "name": name,
            "formed_computer": formed,
            "audit": self.audit(name),
        }

    def __repr__(self) -> str:
        return f"Portal(creator=…{self._creator_key.hex()[-8:]}, tissues={list(self._tissues)})"
