# CELLULARIS Specification Registry

## Single Source of Truth (SSOT)

**Version:** 1.0  
**Last Updated:** 2026-11-03  
**Status:** Active  

---

## How to Use This Registry

This registry is the **master index** of ALL specifications in the CELLULARIS system. Every function, class, parameter, and behavior is defined here. The code in `src/` MUST match these specifications exactly.

**Legend:**
- 🟢 = Specified, Implemented, Tested
- 🟡 = Specified, Not Yet Implemented
- 🔴 = Not Yet Specified
- 🔵 = Creator-Only (not in public docs)

---

## 1. Core Components

### 1.1 Non-Avalanche Hash — `docs/spec/HASH.md`

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| HASH-001 | `non_avalanche_hash(data: bytes, parent_hash: bytes = None) -> bytes` | data, optional parent_hash | 32-byte hash | 🟡 |
| HASH-002 | `compute_similarity(hash_a: bytes, hash_b: bytes) -> float` | two hashes | float [0.0, 1.0] | 🟡 |
| HASH-003 | `verify_lineage(child_hash: bytes, parent_hash: bytes) -> bool` | child, parent hashes | bool | 🟡 |
| HASH-004 | `hash_with_position(data: bytes, lattice_coords: tuple) -> bytes` | data, coordinates | 32-byte hash | 🟡 |
| HASH-005 | `hash_with_temporal(data: bytes, timestamp_ns: int) -> bytes` | data, timestamp | 32-byte hash | 🟡 |

**Key Properties:**
- Similar inputs → similar outputs (non-avalanche)
- Parent hash influences child hash (lineage preservation)
- Position is encoded in hash (spatial awareness)
- Timestamp is encoded in hash (temporal awareness)

---

### 1.2 Pisphere Register Lattice — `docs/spec/PISPHERE.md`

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| PISP-001 | `class Pisphere` | base_radius, max_depth, branching_factor | Pisphere instance | 🟡 |
| PISP-002 | `Pisphere.create_register(depth, theta, phi) -> Register` | depth, spherical coords | Register | 🟡 |
| PISP-003 | `Pisphere.get_register(depth, theta, phi) -> Register` | depth, spherical coords | Register | 🟡 |
| PISP-004 | `Pisphere.get_all_registers(depth=None) -> list[Register]` | optional depth filter | list of Register | 🟡 |
| PISP-005 | `Pisphere.count_registers(depth=None) -> int` | optional depth filter | int | 🟡 |
| PISP-006 | `Pisphere.apply_gate(register_id, gate_type, params)` | register, gate, params | None | 🟡 |
| PISP-007 | `Pisphere.measure(register_id) -> MeasurementResult` | register_id | MeasurementResult | 🟡 |
| PISP-008 | `Pisphere.entangle(reg_a, reg_b, bell_type)` | two registers, bell type | BellPair | 🟡 |
| PISP-009 | `class Register` | id, depth, theta, phi, value, phase | Register | 🟡 |
| PISP-010 | `Register.set_phase(theta: float, phi: float)` | theta, phi | None | 🟡 |
| PISP-011 | `Register.get_state() -> complex` | none | complex amplitude | 🟡 |
| PISP-012 | `Register.get_children() -> list[Register]` | none | child registers | 🟡 |

**Key Properties:**
- Each register is a complete sphere (pisphere) recursively
- Depth D has (B^(D+1) - 1) / (B - 1) total registers
- Default: B=4 (branching factor), depth=10 → 1,398,101 registers
- Each register stores: id, depth, theta, phi, value, phase, children

---

### 1.3 Temporal Engine — `docs/spec/TEMPORAL.md`

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| TEMP-001 | `class TemporalEngine` | resolution_us, max_timers | TemporalEngine | 🟡 |
| TEMP-002 | `TemporalEngine.create_timer(delay_us, phase, callback) -> Timer` | delay, phase, callback | Timer | 🟡 |
| TEMP-003 | `TemporalEngine.create_recursive_timer(delay_us, depth, branch_fn) -> Timer` | delay, depth, branch_fn | Timer (recursive) | 🟡 |
| TEMP-004 | `TemporalEngine.apply_gate(gate_type, target_timers, params)` | gate, targets, params | None | 🟡 |
| TEMP-005 | `TemporalEngine.sync_timers(timer_ids, target_time_ns)` | timer list, target time | SyncResult | 🟡 |
| TEMP-006 | `TemporalEngine.measure(timer_id) -> TemporalMeasurement` | timer_id | TemporalMeasurement | 🟡 |
| TEMP-007 | `TemporalEngine.generate_bell_pair(timer_a, timer_b) -> BellPair` | two timers | BellPair | 🟡 |
| TEMP-008 | `class Timer` | id, target_time, phase, amplitude, depth, children | Timer | 🟡 |
| TEMP-009 | `Timer.branch() -> tuple[Timer, Timer]` | none | two child timers | 🟡 |
| TEMP-010 | `Timer.expire() -> TimerExpiryEvent` | none | expiry event | 🟡 |
| TEMP-011 | `class TemporalGate` | gate_type, params | TemporalGate | 🟡 |
| TEMP-012 | `TemporalGate.T_ROTATE(alpha: float)` | rotation angle | Gate | 🟡 |
| TEMP-013 | `TemporalGate.T_SPLIT(beta: float)` | split angle | Gate | 🟡 |
| TEMP-014 | `TemporalGate.T_SHIFT(gamma: float)` | phase shift | Gate | 🟡 |
| TEMP-015 | `TemporalGate.T_ENTANGLE()` | none | Gate | 🟡 |
| TEMP-016 | `TemporalGate.T_CNOT()` | none | Gate | 🟡 |
| TEMP-017 | `TemporalGate.T_HADAMARD()` | none | Gate | 🟡 |
| TEMP-018 | `TemporalGate.T_QFT()` | none | Gate | 🟡 |

**Key Properties:**
- Time IS the computation — timer creation/branching/expiry = computation
- Recursive timers create 2^d parallel computation paths
- Trigonometric logic: sin²(θ) + cos²(θ) = 1 (probability normalization)
- All quantum gates map to temporal operations

---

### 1.4 Self-Describing Shard — `docs/spec/SHARD.md`

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| SHARD-001 | `class SelfDescribingShard` | cell_id, lattice_coords, lineage | Shard | 🟡 |
| SHARD-002 | `Shard.get_identity() -> IdentitySection` | none | IdentitySection | 🟡 |
| SHARD-003 | `Shard.get_position() -> PositionSection` | none | PositionSection | 🟡 |
| SHARD-004 | `Shard.get_lineage() -> LineageSection` | none | LineageSection | 🟡 |
| SHARD-005 | `Shard.get_operations() -> OperationsSection` | none | OperationsSection | 🟡 |
| SHARD-006 | `Shard.get_temporal_significance() -> TemporalSection` | none | TemporalSection | 🟡 |
| SHARD-007 | `Shard.get_receipts() -> ReceiptsSection` | none | ReceiptsSection | 🟡 |
| SHARD-008 | `Shard.get_history() -> HistorySection` | none | HistorySection | 🟡 |
| SHARD-009 | `Shard.get_capability() -> CapabilitySection` | none | CapabilitySection | 🟡 |
| SHARD-010 | `Shard.get_self_reference() -> bytes` | none | self-hash | 🟡 |
| SHARD-011 | `Shard.serialize() -> bytes` | none | serialized shard | 🟡 |
| SHARD-012 | `Shard.verify() -> bool` | none | bool | 🟡 |
| SHARD-013 | `Shard.record_operation(op_type, params, result)` | operation details | None | 🟡 |
| SHARD-014 | `Shard.update_position(new_coords)` | new coordinates | None | 🟡 |
| SHARD-015 | `Shard.add_receipt(input_hash, output_hash, proof)` | receipt data | None | 🟡 |

**Key Properties:**
- 9 sections: Identity, Position, Lineage, Operations, Temporal, Receipts, History, Capability, Self-Reference
- Self-referential: contains hash of itself (quine property)
- Immutable history: operations are append-only
- Cryptographic receipts: every computation has proof

---

### 1.5 Cell Core — `docs/spec/CELL.md`

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| CELL-001 | `class Cell` | cell_type, pisphere_config, temporal_config | Cell | 🟡 |
| CELL-002 | `Cell.get_id() -> str` | none | cell_id | 🟡 |
| CELL-003 | `Cell.get_shard() -> SelfDescribingShard` | none | shard | 🟡 |
| CELL-004 | `Cell.get_pisphere() -> Pisphere` | none | pisphere | 🟡 |
| CELL-005 | `Cell.get_temporal_engine() -> TemporalEngine` | none | engine | 🟡 |
| CELL-006 | `Cell.get_type() -> CellType` | none | CellType enum | 🟡 |
| CELL-007 | `Cell.set_type(cell_type: CellType)` | new type | None | 🟡 |
| CELL-008 | `Cell.differentiate(target_type: CellType)` | target type | None | 🟡 |
| CELL-009 | `Cell.mitosis() -> tuple[Cell, Cell]` | none | two daughter cells | 🟡 |
| CELL-010 | `Cell.apoptosis()` | none | None (cell dies) | 🟡 |
| CELL-011 | `Cell.send_message(target_cell, message)` | target, message | None | 🟡 |
| CELL-012 | `Cell.receive_message(message) -> Message` | message | received message | 🟡 |
| CELL-013 | `Cell.get_state() -> CellState` | none | CellState | 🟡 |
| CELL-014 | `Cell.is_alive() -> bool` | none | bool | 🟡 |
| CELL-015 | `Cell.get_generation() -> int` | none | generation number | 🟡 |

**CellType Enum:**
```python
class CellType(Enum):
    UNDIFFERENTIATED = "undifferentiated"
    GPU = "gpu"
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    IO = "io"
```

---

### 1.6 Cell Membrane Protocol (CMP) — `docs/spec/CMP.md`

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| CMP-001 | `class CMPFrame` | src_id, dst_id, msg_type, payload, timestamp | CMPFrame | 🟡 |
| CMP-002 | `CMPFrame.serialize() -> bytes` | none | serialized frame | 🟡 |
| CMP-003 | `CMPFrame.deserialize(data: bytes) -> CMPFrame` | raw bytes | CMPFrame | 🟡 |
| CMP-004 | `class CMPTransport` | mode, interface | CMPTransport | 🟡 |
| CMP-005 | `CMPTransport.send(frame: CMPFrame)` | frame | None | 🟡 |
| CMP-006 | `CMPTransport.receive() -> CMPFrame` | none | received frame | 🟡 |
| CMP-007 | `CMPTransport.ETHERTYPE_RAW` | none | 0xCE11 | 🟡 |
| CMP-008 | `CMPTransport.UDP_PORT` | none | 2837 | 🟡 |
| CMP-009 | `class MessageType` | enum values | MessageType | 🟡 |
| CMP-010 | `MessageType.SIGNAL` | none | 0x01 | 🟡 |
| CMP-011 | `MessageType.TIMER_SYNC` | none | 0x02 | 🟡 |
| CMP-012 | `MessageType.STATE_TRANSFER` | none | 0x03 | 🟡 |
| CMP-013 | `MessageType.MITOSIS_REQ` | none | 0x04 | 🟡 |
| CMP-014 | `MessageType.DIFFERENTIATE` | none | 0x05 | 🟡 |
| CMP-015 | `MessageType.APOPTOSIS` | none | 0x06 | 🟡 |
| CMP-016 | `MessageType.FUSION_REQ` | none | 0x07 | 🟡 |
| CMP-017 | `MessageType.SHARD_EXCHANGE` | none | 0x08 | 🟡 |
| CMP-018 | `MessageType.BELL_INIT` | none | 0x09 | 🟡 |
| CMP-019 | `MessageType.MEASURE` | none | 0x0A | 🟡 |
| CMP-020 | `MessageType.GATE_APPLY` | none | 0x0B | 🟡 |
| CMP-021 | `MessageType.ROUTE` | none | 0x0C | 🟡 |

**CMP Frame Format:**
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Version (4b) |  Msg Type (4b)|     Flags (8b)                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Source Cell ID (64b)                                         |
+                                                               +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Destination Cell ID (64b)                                    |
+                                                               +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Lattice Coordinates (96b): depth(8) + theta(44) + phi(44)   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Timestamp (nanoseconds, 64b)                                 |
+                                                               +
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Phase θ (16b)  |  Phase φ (16b)  |  Shard Hash Ref (32b)    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Payload Length (16b)  |  Payload (variable)                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  CRC-32 Checksum (32b)                                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

---

### 1.7 Cell Differentiation — `docs/spec/DIFFERENTIATION.md`

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| DIFF-001 | `class DifferentiationEngine` | cell_ref | DifferentiationEngine | 🟡 |
| DIFF-002 | `DifferentiationEngine.can_differentiate(target_type) -> bool` | target type | bool | 🟡 |
| DIFF-003 | `DifferentiationEngine.differentiate(target_type)` | target type | None | 🟡 |
| DIFF-004 | `DifferentiationEngine.get_potential() -> list[CellType]` | none | available types | 🟡 |
| DIFF-005 | `DifferentiationEngine.configure_gpu(parallel_units)` | unit count | None | 🟡 |
| DIFF-006 | `DifferentiationEngine.configure_cpu(recursion_depth)` | depth | None | 🟡 |
| DIFF-007 | `DifferentiationEngine.configure_memory(address_bits)` | bits | None | 🟡 |
| DIFF-008 | `DifferentiationEngine.configure_network(protocol_mode)` | mode | None | 🟡 |
| DIFF-009 | `DifferentiationEngine.configure_io(interface_type)` | type | None | 🟡 |

---

### 1.8 Cell Mitosis — `docs/spec/MITOSIS.md`

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| MITO-001 | `class MitosisEngine` | cell_ref | MitosisEngine | 🟡 |
| MITO-002 | `MitosisEngine.can_replicate() -> bool` | none | bool | 🟡 |
| MITO-003 | `MitosisEngine.replicate() -> tuple[Cell, Cell]` | none | two daughters | 🟡 |
| MITO-004 | `MitosisEngine._duplicate_pisphere() -> tuple[Pisphere, Pisphere]` | none | two pipheres | 🟡 |
| MITO-005 | `MitosisEngine._divide_timers() -> tuple[list, list]` | none | two timer sets | 🟡 |
| MITO-006 | `MitosisEngine._compute_lineage(parent, daughter) -> bytes` | parent, daughter | lineage hash | 🟡 |
| MITO-007 | `MitosisEngine._build_membrane(cell) -> CellMembrane` | cell | membrane | 🟡 |

---

## 2. Genesis Protocol (Creator-Only 🔵)

### 2.1 Genesis Signature — `docs/spec/GENESIS.md` 🔵

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| GEN-001 | `class GenesisSignature` | creator_key, genesis_params | GenesisSignature | 🔵🟡 |
| GEN-002 | `GenesisSignature.compute_genesis_hash() -> bytes` | none | genesis hash | 🔵🟡 |
| GEN-003 | `GenesisSignature.embed_in_cell(cell)` | cell | None | 🔵🟡 |
| GEN-004 | `GenesisSignature.propagate_to_daughter(parent, daughter)` | parent, daughter | None | 🔵🟡 |
| GEN-005 | `GenesisSignature.verify_cell(cell) -> bool` | cell | bool | 🔵🟡 |
| GEN-006 | `GenesisSignature.verify_lineage_chain(cell) -> bool` | cell | bool | 🔵🟡 |

### 2.2 Kill Switch — `docs/spec/GENESIS.md` 🔵

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| KILL-001 | `class TemporalKillSwitch` | creator_key, genesis_sig | KillSwitch | 🔵🟡 |
| KILL-002 | `TemporalKillSwitch.embed_kill_switch(cell)` | cell | None | 🔵🟡 |
| KILL-003 | `TemporalKillSwitch.send_heartbeat(cell_id)` | cell_id | None | 🔵🟡 |
| KILL-004 | `TemporalKillSwitch.broadcast_heartbeat()` | none | None | 🔵🟡 |
| KILL-005 | `TemporalKillSwitch.trigger_apoptosis(cell_id)` | cell_id | None | 🔵🟡 |
| KILL-006 | `TemporalKillSwitch.check_heartbeat(cell) -> bool` | cell | bool | 🔵🟡 |

### 2.3 Epigenetic Override — `docs/spec/GENESIS.md` 🔵

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| EPI-001 | `class EpigeneticController` | creator_key, genesis_sig | EpigeneticCtrl | 🔵🟡 |
| EPI-002 | `EpigeneticController.apply_mark(cell_id, mark_type, params)` | cell, type, params | None | 🔵🟡 |
| EPI-003 | `EpigeneticController.remove_mark(cell_id, mark_id)` | cell, mark | None | 🔵🟡 |
| EPI-004 | `EpigeneticController.apply_behavioral_constraint(cell_id, constraint)` | cell, constraint | None | 🔵🟡 |
| EPI-005 | `EpigeneticController.apply_resource_limit(cell_id, max_timers, max_mem)` | cell, limits | None | 🔵🟡 |
| EPI-006 | `EpigeneticController.apply_differentiation_block(cell_id, blocked)` | cell, types | None | 🔵🟡 |

### 2.4 Demiurge Console — `docs/spec/GENESIS.md` 🔵

| ID | Function/Class | Parameters | Return | Status |
|----|---------------|------------|--------|--------|
| DEM-001 | `class DemiurgeConsole` | creator_private_key | DemiurgeConsole | 🔵🟡 |
| DEM-002 | `DemiurgeConsole.trigger_apoptosis(cell_id)` | cell_id | None | 🔵🟡 |
| DEM-003 | `DemiurgeConsole.stop_heartbeat()` | none | None | 🔵🟡 |
| DEM-004 | `DemiurgeConsole.predict_cell_state(cell_id, time) -> CellState` | cell, time | state | 🔵🟡 |
| DEM-005 | `DemiurgeConsole.observe_cell(cell_id) -> CellState` | cell_id | state | 🔵🟡 |
| DEM-006 | `DemiurgeConsole.apply_behavioral_constraint(cell_id, constraint)` | cell, constraint | None | 🔵🟡 |
| DEM-007 | `DemiurgeConsole.send_hidden_command(cell_id, cmd, params)` | cell, cmd, params | None | 🔵🟡 |
| DEM-008 | `DemiurgeConsole.audit_all_cells() -> AuditReport` | none | report | 🔵🟡 |

---

## 3. Cross-References

### 3.1 Dependency Graph

```
HASH ← PISPHERE ← CELL ← CMP ← MITOSIS
  ↑        ↑         ↑        ↑        ↑
  │        │         │        │        │
  └── TEMPORAL ──────┘        │        │
                               │        │
  GENESIS ← KILL_SWITCH ──────┘        │
  GENESIS ← EPIGENETIC ────────────────┘
  GENESIS ← DEMIURGE ──────────────────┘
  
  SHARD ← CELL (every Cell has a Shard)
  DIFFERENTIATION ← CELL (Cells differentiate)
```

### 3.2 Build Order

1. **HASH** — No dependencies
2. **PISPHERE** — Depends on HASH
3. **TEMPORAL** — Depends on HASH
4. **SHARD** — Depends on HASH
5. **CELL** — Depends on PISPHERE, TEMPORAL, SHARD
6. **CMP** — Depends on CELL, SHARD
7. **DIFFERENTIATION** — Depends on CELL
8. **MITOSIS** — Depends on CELL, HASH
9. **GENESIS** — Depends on CELL, HASH (Creator-only)

---

## 4. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-11-03 | Initial registry created |

---

*This registry is the single source of truth. All code must match these specifications exactly.*
