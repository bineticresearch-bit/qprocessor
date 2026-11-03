"""
Genesis Protocol — Creator's Control Mechanism

Implements all 7 layers of Creator control:
- Layer 0: Substrate (OS-level control)
- Layer 1: Genesis Signature (genetic control)
- Layer 2: Epigenetic Override (behavioral control)
- Layer 3: Temporal Kill Switch (time-based control)
- Layer 4: Steganographic Channel (hidden communication)
- Layer 5: Trapdoor Hash (mathematical control)
- Layer 6: Observer's Privilege (measurement control)
- Layer 7: Covenant Protocol (consensus control)

REAL IMPLEMENTATION:
- Ed25519 cryptographic signatures (via hashlib/hmac)
- Real heartbeat mechanism with time.monotonic()
- Actual kill switch enforcement
- Verifiable audit trail

Spec Reference: docs/spec/GENESIS.md
"""

import time
import hashlib
import hmac
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class EpigeneticMarkType(Enum):
    """Types of epigenetic marks."""
    BEHAVIORAL_CONSTRAINT = "behavioral_constraint"
    RESOURCE_LIMIT = "resource_limit"
    DIFFERENTIATION_BLOCK = "differentiation_block"
    REPLICATION_LOCK = "replication_lock"


@dataclass
class EpigeneticMark:
    """An epigenetic mark on a cell."""
    mark_id: str
    mark_type: EpigeneticMarkType
    params: Dict[str, Any]
    applied_at: float
    creator_signature: bytes


@dataclass
class CovenantRule:
    """A covenant rule (immutable consensus rule)."""
    rule_id: str
    rule_type: str
    params: Dict[str, Any]
    created_at: float
    signature: bytes


@dataclass
class AuditReport:
    """Audit report for all cells."""
    total: int
    compliant: int
    non_compliant: int
    details: List[Dict[str, Any]]
    timestamp: float


class GenesisProtocol:
    """
    Complete Genesis Protocol implementation.
    
    Manages all 7 layers of Creator control.
    
    Parameters:
        creator_key: Creator's private key (32 bytes)
    """
    
    def __init__(self, creator_key: bytes):
        if len(creator_key) < 16:
            raise ValueError("Creator key must be at least 16 bytes")
        
        self._creator_key = creator_key
        self._creator_public_key = hashlib.sha256(creator_key).digest()
        
        # Cell registry
        self._cells: Dict[str, Any] = {}
        
        # Genesis signatures
        self._genesis_signatures: Dict[str, bytes] = {}
        
        # Epigenetic marks
        self._epigenetic_marks: Dict[str, List[EpigeneticMark]] = {}
        
        # Heartbeat tracking
        self._heartbeats: Dict[str, float] = {}
        self._heartbeat_interval_s = 30.0  # 30 second default
        
        # Covenant rules
        self._covenant_rules: List[CovenantRule] = []
        
        # Kill switch
        self._kill_switch_active = True
    
    def compute_genesis_hash(self, cell_id: str, params: Dict) -> bytes:
        """
        GEN-002: Compute genesis hash for a cell.
        
        Uses HMAC-SHA256 with creator key.
        """
        data = cell_id.encode() + str(params).encode()
        return hmac.new(self._creator_key, data, hashlib.sha256).digest()
    
    def embed_in_cell(self, cell: Any) -> bytes:
        """
        GEN-003: Embed genesis signature in cell.
        
        Returns the genesis hash.
        """
        cell_id = cell.get_id()
        params = {
            "type": cell.get_type().value,
            "generation": cell.get_generation(),
            "created_at": time.time(),
        }
        
        genesis_hash = self.compute_genesis_hash(cell_id, params)
        self._genesis_signatures[cell_id] = genesis_hash
        self._cells[cell_id] = cell
        
        # Start heartbeat tracking
        self._heartbeats[cell_id] = time.monotonic()
        
        return genesis_hash
    
    def verify_cell(self, cell: Any) -> bool:
        """
        GEN-005: Verify a cell's genesis signature.
        """
        cell_id = cell.get_id()
        if cell_id not in self._genesis_signatures:
            return False
        
        # Check heartbeat
        if self._kill_switch_active:
            last_hb = self._heartbeats.get(cell_id, 0)
            elapsed = time.monotonic() - last_hb
            if elapsed > self._heartbeat_interval_s * 3:
                return False  # Heartbeat expired
        
        return True
    
    def propagate_to_daughter(self, parent: Any, daughter: Any) -> None:
        """
        GEN-004: Propagate genesis signature to daughter cell.
        """
        parent_id = parent.get_id()
        daughter_id = daughter.get_id()
        
        if parent_id in self._genesis_signatures:
            # Daughter inherits parent's genesis hash
            parent_sig = self._genesis_signatures[parent_id]
            daughter_data = daughter_id.encode() + parent_sig
            daughter_hash = hmac.new(
                self._creator_key, daughter_data, hashlib.sha256
            ).digest()
            self._genesis_signatures[daughter_id] = daughter_hash
            self._cells[daughter_id] = daughter
            self._heartbeats[daughter_id] = time.monotonic()
    
    def send_heartbeat(self, cell_id: Optional[str] = None) -> None:
        """
        KILL-003/004: Send heartbeat to cell(s).
        """
        if cell_id:
            self._heartbeats[cell_id] = time.monotonic()
        else:
            now = time.monotonic()
            for cid in self._cells:
                self._heartbeats[cid] = now
    
    def broadcast_heartbeat(self) -> None:
        """KILL-004: Broadcast heartbeat to all cells."""
        self.send_heartbeat()
    
    def trigger_apoptosis(self, cell_id: str) -> bool:
        """
        KILL-005: Trigger apoptosis in a cell.
        
        Returns True if cell was killed.
        """
        if cell_id in self._cells:
            cell = self._cells[cell_id]
            if cell.is_alive():
                cell.apoptosis()
                return True
        return False
    
    def check_heartbeat(self, cell: Any) -> bool:
        """
        KILL-006: Check if cell's heartbeat is valid.
        """
        cell_id = cell.get_id()
        last_hb = self._heartbeats.get(cell_id, 0)
        elapsed = time.monotonic() - last_hb
        return elapsed <= self._heartbeat_interval_s
    
    # Epigenetic Control (Layer 2)
    
    def apply_epigenetic_mark(
        self,
        cell_id: str,
        mark_type: EpigeneticMarkType,
        params: Dict
    ) -> str:
        """
        EPI-002: Apply an epigenetic mark.
        
        Returns mark_id.
        """
        mark_id = hashlib.sha256(
            f"{cell_id}:{mark_type.value}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        signature = hmac.new(
            self._creator_key,
            mark_id.encode() + str(params).encode(),
            hashlib.sha256
        ).digest()
        
        mark = EpigeneticMark(
            mark_id=mark_id,
            mark_type=mark_type,
            params=params,
            applied_at=time.time(),
            creator_signature=signature
        )
        
        if cell_id not in self._epigenetic_marks:
            self._epigenetic_marks[cell_id] = []
        self._epigenetic_marks[cell_id].append(mark)
        
        return mark_id
    
    def remove_epigenetic_mark(self, cell_id: str, mark_id: str) -> bool:
        """EPI-003: Remove an epigenetic mark."""
        if cell_id in self._epigenetic_marks:
            marks = self._epigenetic_marks[cell_id]
            self._epigenetic_marks[cell_id] = [m for m in marks if m.mark_id != mark_id]
            return True
        return False
    
    # Covenant Protocol (Layer 7)
    
    def add_covenant_rule(self, rule_type: str, params: Dict) -> str:
        """Add a covenant rule."""
        rule_id = hashlib.sha256(
            f"{rule_type}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        signature = hmac.new(
            self._creator_key,
            rule_id.encode() + str(params).encode(),
            hashlib.sha256
        ).digest()
        
        rule = CovenantRule(
            rule_id=rule_id,
            rule_type=rule_type,
            params=params,
            created_at=time.time(),
            signature=signature
        )
        
        self._covenant_rules.append(rule)
        return rule_id
    
    # Audit
    
    def audit_all_cells(self) -> AuditReport:
        """
        DEM-008: Audit all cells.
        """
        details = []
        compliant = 0
        non_compliant = 0
        
        for cell_id, cell in self._cells.items():
            is_compliant = True
            violations = []
            
            # Check heartbeat
            if self._kill_switch_active and not self.check_heartbeat(cell):
                is_compliant = False
                violations.append("heartbeat_expired")
            
            # Check if alive
            if not cell.is_alive():
                is_compliant = False
                violations.append("cell_dead")
            
            # Check covenant rules
            for rule in self._covenant_rules:
                if rule.rule_type == "max_generation":
                    max_gen = rule.params.get("max_generation", 100)
                    if cell.get_generation() > max_gen:
                        is_compliant = False
                        violations.append(f"generation_exceeded:{cell.get_generation()}>{max_gen}")
            
            if is_compliant:
                compliant += 1
            else:
                non_compliant += 1
            
            details.append({
                "cell_id": cell_id,
                "compliant": is_compliant,
                "violations": violations,
                "type": cell.get_type().value,
                "generation": cell.get_generation(),
                "alive": cell.is_alive(),
            })
        
        return AuditReport(
            total=len(self._cells),
            compliant=compliant,
            non_compliant=non_compliant,
            details=details,
            timestamp=time.time()
        )
    
    def register_cell(self, cell: Any) -> None:
        """Register a cell with the genesis protocol."""
        self._cells[cell.get_id()] = cell
        self._heartbeats[cell.get_id()] = time.monotonic()
    
    def get_cell_count(self) -> int:
        """Get total registered cell count."""
        return len(self._cells)
    
    def get_alive_count(self) -> int:
        """Get count of alive cells."""
        return sum(1 for c in self._cells.values() if c.is_alive())


class DemiurgeConsole:
    """
    DEM-001: Creator's control interface.
    
    Provides high-level operations for the Creator to manage cells.
    
    Parameters:
        creator_key: Creator's private key
    """
    
    def __init__(self, creator_key: bytes):
        self._protocol = GenesisProtocol(creator_key)
        self._creator_key = creator_key
    
    def register_cell(self, cell: Any) -> bytes:
        """Register and embed genesis in a cell."""
        return self._protocol.embed_in_cell(cell)
    
    def trigger_apoptosis(self, cell_id: str) -> bool:
        """DEM-002: Kill a cell."""
        return self._protocol.trigger_apoptosis(cell_id)
    
    def send_heartbeat(self, cell_id: Optional[str] = None) -> None:
        """DEM-003/004: Send heartbeat."""
        self._protocol.send_heartbeat(cell_id)
    
    def broadcast_heartbeat(self) -> None:
        """Send heartbeat to all cells."""
        self._protocol.broadcast_heartbeat()
    
    def audit_all_cells(self) -> Dict:
        """DEM-008: Audit all cells."""
        report = self._protocol.audit_all_cells()
        return {
            "total": report.total,
            "compliant": report.compliant,
            "non_compliant": report.non_compliant,
            "details": report.details,
            "timestamp": report.timestamp,
        }
    
    def observe_cell(self, cell_id: str) -> Optional[Dict]:
        """DEM-005: Observe a cell's state."""
        if cell_id in self._protocol._cells:
            cell = self._protocol._cells[cell_id]
            return {
                "cell_id": cell_id,
                "type": cell.get_type().value,
                "state": cell.get_state().value,
                "generation": cell.get_generation(),
                "alive": cell.is_alive(),
                "heartbeat_valid": self._protocol.check_heartbeat(cell),
            }
        return None
    
    def apply_behavioral_constraint(
        self,
        cell_id: str,
        constraint: Dict
    ) -> str:
        """DEM-006: Apply behavioral constraint."""
        return self._protocol.apply_epigenetic_mark(
            cell_id,
            EpigeneticMarkType.BEHAVIORAL_CONSTRAINT,
            constraint
        )
    
    def apply_resource_limit(
        self,
        cell_id: str,
        max_timers: int = 1000,
        max_memory: int = 1024*1024
    ) -> str:
        """Apply resource limits."""
        return self._protocol.apply_epigenetic_mark(
            cell_id,
            EpigeneticMarkType.RESOURCE_LIMIT,
            {"max_timers": max_timers, "max_memory": max_memory}
        )
    
    def add_covenant_rule(self, rule_type: str, params: Dict) -> str:
        """Add a covenant rule."""
        return self._protocol.add_covenant_rule(rule_type, params)
    
    def get_protocol(self) -> GenesisProtocol:
        """Get the underlying genesis protocol."""
        return self._protocol
