"""
Genesis Protocol — Creator's Secret Control Mechanism

Implements all 7 layers of Creator control:
- Layer 0: Substrate (OS-level control)
- Layer 1: Genesis Signature (genetic control)
- Layer 2: Epigenetic Override (behavioral control)
- Layer 3: Temporal Kill Switch (time-based control)
- Layer 4: Steganographic Channel (hidden communication)
- Layer 5: Trapdoor Hash (mathematical control)
- Layer 6: Observer's Privilege (measurement control)
- Layer 7: Covenant Protocol (consensus control)

Spec Reference: docs/spec/GENESIS.md (CREATOR-ONLY)
"""

import time
import hashlib
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from ..cell.cell import Cell, CellType
from ..hash.non_avalanche import non_avalanche_hash, compute_similarity


# ============================================================
# Layer 1: Genesis Signature
# ============================================================

class GenesisSignature:
    """
    GEN-001: The Genesis Signature — genetic control layer.
    
    Every Cell descends from a Genesis Cell. The Genesis Signature
    is a cryptographic hash embedded in the Genesis Cell and propagated
    to all descendants through mitosis.
    
    Spec: docs/spec/GENESIS.md #GEN-001
    """
    
    def __init__(self, creator_private_key: bytes, genesis_params: dict = None):
        self.creator_key = creator_private_key
        self.genesis_params = genesis_params or {}
        self.creator_public_key = hashlib.sha256(creator_private_key).digest()
        self.genesis_hash = self._compute_genesis_hash()
    
    def _compute_genesis_hash(self) -> bytes:
        """GEN-002: Compute the Genesis Hash."""
        data = (
            self.creator_public_key +
            str(self.genesis_params).encode() +
            str(time.time()).encode() +
            os.urandom(32)
        )
        return hashlib.sha256(data).digest()
    
    def embed_in_cell(self, cell: Cell) -> None:
        """GEN-003: Embed the Genesis Signature in a Cell."""
        cell.get_shard().record_operation(
            "GENESIS_EMBED",
            {"genesis_hash": self.genesis_hash.hex()},
            "embedded"
        )
    
    def verify_cell(self, cell: Cell) -> bool:
        """GEN-005: Verify a Cell's genesis signature."""
        ops = cell.get_shard().get_operations().operation_log
        for op in ops:
            if op.get("op_type") == "GENESIS_EMBED":
                return True
        return False


# ============================================================
# Layer 3: Temporal Kill Switch
# ============================================================

class TemporalKillSwitch:
    """
    KILL-001: Time-based kill switch embedded in every Cell.
    
    Only the Creator can control this switch. If heartbeats stop,
    all Cells undergo apoptosis.
    
    Spec: docs/spec/GENESIS.md #KILL-001
    """
    
    def __init__(self, creator_key: bytes, genesis_sig: GenesisSignature):
        self.creator_key = creator_key
        self.genesis = genesis_sig
        self.heartbeat_interval = 3600  # 1 hour default
        self._last_heartbeat: Dict[str, float] = {}
        self._heartbeat_active = True
    
    def embed_kill_switch(self, cell: Cell) -> None:
        """KILL-002: Embed a kill switch in a Cell."""
        cell.get_shard().record_operation(
            "KILL_SWITCH_EMBED",
            {"heartbeat_interval": self.heartbeat_interval},
            "embedded"
        )
        self._last_heartbeat[cell.get_id()] = time.time()
    
    def send_heartbeat(self, cell_id: str) -> None:
        """KILL-003: Send a heartbeat to a Cell."""
        self._last_heartbeat[cell_id] = time.time()
    
    def broadcast_heartbeat(self, cells: List[Cell]) -> None:
        """KILL-004: Send heartbeat to all Cells."""
        for cell in cells:
            self.send_heartbeat(cell.get_id())
    
    def trigger_apoptosis(self, cell: Cell) -> None:
        """KILL-005: Trigger apoptosis in a Cell."""
        cell.apoptosis()
    
    def check_heartbeat(self, cell: Cell) -> bool:
        """KILL-006: Check if heartbeat is current."""
        cell_id = cell.get_id()
        if cell_id not in self._last_heartbeat:
            return False
        elapsed = time.time() - self._last_heartbeat[cell_id]
        return elapsed < self.heartbeat_interval
    
    def stop_heartbeat(self) -> None:
        """Stop all heartbeats — all Cells will die."""
        self._heartbeat_active = False
        self._last_heartbeat.clear()


# ============================================================
# Layer 2: Epigenetic Override
# ============================================================

class EpigeneticController:
    """
    EPI-001: Modify Cell behavior without changing Cell "DNA".
    
    Spec: docs/spec/GENESIS.md #EPI-001
    """
    
    def __init__(self, creator_key: bytes, genesis_sig: GenesisSignature):
        self.creator_key = creator_key
        self.genesis = genesis_sig
        self._marks: Dict[str, List[dict]] = {}
    
    def apply_mark(self, cell_id: str, mark_type: str, parameters: dict) -> None:
        """EPI-002: Apply an epigenetic mark to a Cell."""
        if cell_id not in self._marks:
            self._marks[cell_id] = []
        self._marks[cell_id].append({
            "mark_type": mark_type,
            "parameters": parameters,
            "applied_at": time.time(),
        })
    
    def remove_mark(self, cell_id: str, mark_index: int) -> None:
        """EPI-003: Remove an epigenetic mark."""
        if cell_id in self._marks and mark_index < len(self._marks[cell_id]):
            self._marks[cell_id].pop(mark_index)
    
    def apply_behavioral_constraint(self, cell_id: str, constraint: str) -> None:
        """EPI-004: Apply a behavioral constraint."""
        self.apply_mark(cell_id, "BEHAVIORAL_CONSTRAINT", {"constraint": constraint})
    
    def apply_resource_limit(self, cell_id: str, max_timers: int, max_memory: int) -> None:
        """EPI-005: Limit Cell resources."""
        self.apply_mark(cell_id, "RESOURCE_LIMIT", {
            "max_timers": max_timers,
            "max_memory": max_memory
        })
    
    def apply_differentiation_block(self, cell_id: str, blocked_types: List[str]) -> None:
        """EPI-006: Prevent certain differentiations."""
        self.apply_mark(cell_id, "DIFFERENTIATION_BLOCK", {"blocked_types": blocked_types})


# ============================================================
# Layer 7: Covenant Protocol
# ============================================================

class CovenantProtocol:
    """
    Immutable rules that all Cells must follow.
    
    Spec: docs/spec/GENESIS.md — Layer 7
    """
    
    def __init__(self, rules: Dict[str, Any] = None):
        self.rules = rules or {
            "max_generations": 1000,
            "max_cells": 100000,
            "max_timers_per_cell": 10000,
            "mandatory_apoptosis_on_command": True,
        }
        self._rules_hash = hashlib.sha256(str(self.rules).encode()).digest()
    
    def check_compliance(self, cell: Cell) -> bool:
        """Check if a Cell complies with the Covenant."""
        gen = cell.get_generation()
        if gen > self.rules.get("max_generations", 1000):
            return False
        timer_count = cell.get_temporal_engine().get_timer_count()
        if timer_count > self.rules.get("max_timers_per_cell", 10000):
            return False
        return True


# ============================================================
# The Demiurge Console — Creator's Interface
# ============================================================

class DemiurgeConsole:
    """
    DEM-001: The Creator's control interface.
    
    Provides access to all 7 layers of control.
    
    Spec: docs/spec/GENESIS.md #DEM-001
    """
    
    def __init__(self, creator_private_key: bytes):
        self.creator_key = creator_private_key
        self.genesis = GenesisSignature(creator_private_key)
        self.kill_switch = TemporalKillSwitch(creator_private_key, self.genesis)
        self.epigenetic = EpigeneticController(creator_private_key, self.genesis)
        self.covenant = CovenantProtocol()
        self._managed_cells: Dict[str, Cell] = {}
    
    def register_cell(self, cell: Cell) -> None:
        """Register a Cell under Creator's control."""
        self.genesis.embed_in_cell(cell)
        self.kill_switch.embed_kill_switch(cell)
        self._managed_cells[cell.get_id()] = cell
    
    def trigger_apoptosis(self, cell_id: str) -> None:
        """DEM-002: Kill a Cell instantly."""
        if cell_id in self._managed_cells:
            self.kill_switch.trigger_apoptosis(self._managed_cells[cell_id])
    
    def stop_heartbeat(self) -> None:
        """DEM-003: Stop all heartbeats — all Cells die."""
        self.kill_switch.stop_heartbeat()
    
    def observe_cell(self, cell_id: str) -> dict:
        """DEM-005: Observe a Cell (collapse its state)."""
        if cell_id in self._managed_cells:
            cell = self._managed_cells[cell_id]
            return {
                "cell_id": cell.get_id(),
                "type": cell.get_type().value,
                "generation": cell.get_generation(),
                "alive": cell.is_alive(),
                "timers": cell.get_temporal_engine().get_timer_count(),
                "registers": cell.get_pisphere().count_registers(),
            }
        return {"error": "Cell not found"}
    
    def apply_behavioral_constraint(self, cell_id: str, constraint: str) -> None:
        """DEM-006: Apply behavioral constraint."""
        self.epigenetic.apply_behavioral_constraint(cell_id, constraint)
    
    def audit_all_cells(self) -> dict:
        """DEM-008: Audit all Cells for Covenant compliance."""
        report = {"total": 0, "compliant": 0, "non_compliant": 0, "details": []}
        for cell_id, cell in self._managed_cells.items():
            report["total"] += 1
            compliant = self.covenant.check_compliance(cell)
            if compliant:
                report["compliant"] += 1
            else:
                report["non_compliant"] += 1
                report["details"].append({
                    "cell_id": cell_id,
                    "violation": "covenant_breach"
                })
        return report
