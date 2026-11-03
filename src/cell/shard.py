"""
Self-Describing Shard — SHARD-001 through SHARD-015

Every Cell carries a complete self-description containing 9 sections:
Identity, Position, Lineage, Operations, Temporal Significance,
Receipts, History, Capability, and Self-Reference.

Spec Reference: docs/spec/SHARD.md
"""

import time
import hashlib
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from ..hash.non_avalanche import non_avalanche_hash, hash_with_position, hash_with_temporal


@dataclass
class IdentitySection:
    """SHARD-002: Who am I?"""
    cell_id: str
    generation: int
    cell_type: str
    created_at: float


@dataclass
class PositionSection:
    """SHARD-003: Where am I relative to the whole?"""
    lattice_coords: tuple  # (depth, theta, phi)
    neighbors: List[str]   # neighbor cell IDs
    containment_depth: int  # how deeply nested


@dataclass
class LineageSection:
    """SHARD-004: Where did I come from?"""
    ancestor_chain: List[str]      # parent → grandparent → ...
    lineage_hash: bytes            # cumulative lineage hash
    generation_path: List[int]     # generation numbers


@dataclass
class OperationsSection:
    """SHARD-005: What have I done?"""
    operation_log: List[Dict[str, Any]]  # append-only log
    merkle_root: bytes                   # Merkle proof chain


@dataclass
class TemporalSection:
    """SHARD-006: When do I matter?"""
    creation_time_ns: int
    phase_age: float           # how long in current phase
    significance_score: float  # temporal importance


@dataclass
class ReceiptsSection:
    """SHARD-007: Proof of my computations."""
    receipts: List[Dict[str, bytes]]  # input_hash, output_hash, proof


@dataclass
class HistorySection:
    """SHARD-008: My complete timeline."""
    state_snapshots: List[Dict[str, Any]]
    timeline_hash: bytes


@dataclass
class CapabilitySection:
    """SHARD-009: What can I become?"""
    differentiation_potential: List[str]  # possible cell types
    resource_capacity: Dict[str, int]     # timers, memory, etc.


class SelfDescribingShard:
    """
    SHARD-001: The Self-Describing Shard.
    
    Every Cell carries a complete self-description that includes:
    - Identity: Who am I?
    - Position: Where am I?
    - Lineage: Where did I come from?
    - Operations: What have I done?
    - Temporal: When do I matter?
    - Receipts: Proof of computations
    - History: Complete timeline
    - Capability: What can I become?
    - Self-Reference: Hash of myself (quine property)
    
    Parameters:
        cell_id: Unique cell identifier
        lattice_coords: Position in the lattice (depth, theta, phi)
        lineage: Optional parent lineage info
    
    Spec: docs/spec/SHARD.md #SHARD-001
    """
    
    def __init__(
        self,
        cell_id: str,
        lattice_coords: tuple = (0, 0.0, 0.0),
        lineage: Optional[Dict] = None
    ):
        self.cell_id = cell_id
        
        # Initialize all 9 sections
        self._identity = IdentitySection(
            cell_id=cell_id,
            generation=0,
            cell_type="undifferentiated",
            created_at=time.time()
        )
        
        self._position = PositionSection(
            lattice_coords=lattice_coords,
            neighbors=[],
            containment_depth=lattice_coords[0]
        )
        
        if lineage:
            self._lineage = LineageSection(
                ancestor_chain=lineage.get("ancestor_chain", []),
                lineage_hash=lineage.get("lineage_hash", b'\x00' * 32),
                generation_path=lineage.get("generation_path", [0])
            )
        else:
            self._lineage = LineageSection(
                ancestor_chain=[],
                lineage_hash=b'\x00' * 32,
                generation_path=[0]
            )
        
        self._operations = OperationsSection(
            operation_log=[],
            merkle_root=b'\x00' * 32
        )
        
        self._temporal = TemporalSection(
            creation_time_ns=int(time.time() * 1e9),
            phase_age=0.0,
            significance_score=1.0
        )
        
        self._receipts = ReceiptsSection(receipts=[])
        
        self._history = HistorySection(
            state_snapshots=[],
            timeline_hash=b'\x00' * 32
        )
        
        self._capability = CapabilitySection(
            differentiation_potential=["gpu", "cpu", "memory", "network", "io"],
            resource_capacity={"timers": 1000, "registers": 10000}
        )
        
        # Self-reference (computed lazily)
        self._self_hash: Optional[bytes] = None
    
    def get_identity(self) -> IdentitySection:
        """SHARD-002: Get identity section."""
        return self._identity
    
    def get_position(self) -> PositionSection:
        """SHARD-003: Get position section."""
        return self._position
    
    def get_lineage(self) -> LineageSection:
        """SHARD-004: Get lineage section."""
        return self._lineage
    
    def get_operations(self) -> OperationsSection:
        """SHARD-005: Get operations section."""
        return self._operations
    
    def get_temporal_significance(self) -> TemporalSection:
        """SHARD-006: Get temporal significance section."""
        return self._temporal
    
    def get_receipts(self) -> ReceiptsSection:
        """SHARD-007: Get receipts section."""
        return self._receipts
    
    def get_history(self) -> HistorySection:
        """SHARD-008: Get history section."""
        return self._history
    
    def get_capability(self) -> CapabilitySection:
        """SHARD-009: Get capability section."""
        return self._capability
    
    def get_self_reference(self) -> bytes:
        """
        SHARD-010: Get self-reference hash.
        
        Returns the hash of this shard (quine property — contains hash of itself).
        
        Spec: docs/spec/SHARD.md #SHARD-010
        """
        if self._self_hash is None:
            self._self_hash = self._compute_self_hash()
        return self._self_hash
    
    def _compute_self_hash(self) -> bytes:
        """Compute the self-referential hash."""
        data = self.serialize()
        return hashlib.sha256(data).digest()
    
    def serialize(self) -> bytes:
        """
        SHARD-011: Serialize the shard to bytes.
        
        Spec: docs/spec/SHARD.md #SHARD-011
        """
        state = {
            "identity": {
                "cell_id": self._identity.cell_id,
                "generation": self._identity.generation,
                "cell_type": self._identity.cell_type,
                "created_at": self._identity.created_at,
            },
            "position": {
                "lattice_coords": list(self._position.lattice_coords),
                "neighbors": self._position.neighbors,
                "containment_depth": self._position.containment_depth,
            },
            "lineage": {
                "ancestor_chain": self._lineage.ancestor_chain,
                "lineage_hash": self._lineage.lineage_hash.hex(),
                "generation_path": self._lineage.generation_path,
            },
            "operations": {
                "operation_count": len(self._operations.operation_log),
                "merkle_root": self._operations.merkle_root.hex(),
            },
            "temporal": {
                "creation_time_ns": self._temporal.creation_time_ns,
                "phase_age": self._temporal.phase_age,
                "significance_score": self._temporal.significance_score,
            },
            "receipts": {
                "receipt_count": len(self._receipts.receipts),
            },
            "capability": {
                "differentiation_potential": self._capability.differentiation_potential,
                "resource_capacity": self._capability.resource_capacity,
            },
        }
        return json.dumps(state, sort_keys=True).encode('utf-8')
    
    def verify(self) -> bool:
        """
        SHARD-012: Verify the shard's integrity.
        
        Checks that the self-hash is consistent with the serialized data.
        
        Spec: docs/spec/SHARD.md #SHARD-012
        """
        computed = self._compute_self_hash()
        if self._self_hash is None:
            self._self_hash = computed
            return True
        return computed == self._self_hash
    
    def record_operation(self, op_type: str, params: dict, result: Any) -> None:
        """
        SHARD-013: Record an operation in the shard's log.
        
        Parameters:
            op_type: Type of operation
            params: Operation parameters
            result: Operation result
        
        Spec: docs/spec/SHARD.md #SHARD-013
        """
        entry = {
            "op_type": op_type,
            "params": params,
            "result_hash": hashlib.sha256(str(result).encode()).hexdigest(),
            "timestamp": time.time(),
        }
        
        self._operations.operation_log.append(entry)
        
        # Update Merkle root
        log_data = json.dumps(self._operations.operation_log, sort_keys=True).encode()
        self._operations.merkle_root = hashlib.sha256(log_data).digest()
        
        # Invalidate self-hash
        self._self_hash = None
    
    def update_position(self, new_coords: tuple) -> None:
        """
        SHARD-014: Update the shard's position.
        
        Spec: docs/spec/SHARD.md #SHARD-014
        """
        self._position.lattice_coords = new_coords
        self._position.containment_depth = new_coords[0]
        self._self_hash = None
    
    def add_receipt(self, input_hash: bytes, output_hash: bytes, proof: bytes) -> None:
        """
        SHARD-015: Add a computation receipt.
        
        Spec: docs/spec/SHARD.md #SHARD-015
        """
        self._receipts.receipts.append({
            "input_hash": input_hash,
            "output_hash": output_hash,
            "proof": proof,
            "timestamp": time.time(),
        })
        self._self_hash = None
