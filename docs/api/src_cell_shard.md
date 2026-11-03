# `src.cell.shard`

## `IdentitySection`

> SHARD-002: Who am I?

## `PositionSection`

> SHARD-003: Where am I relative to the whole?

## `LineageSection`

> SHARD-004: Where did I come from?

## `OperationsSection`

> SHARD-005: What have I done?

## `TemporalSection`

> SHARD-006: When do I matter?

## `ReceiptsSection`

> SHARD-007: Proof of my computations.

## `HistorySection`

> SHARD-008: My complete timeline.

## `CapabilitySection`

> SHARD-009: What can I become?

## `SelfDescribingShard`

> SHARD-001: The Self-Describing Shard.
> 
> Every Cell carries a complete self-description that includes:
> - Identity: Who am I?
> - Position: Where am I?
> - Lineage: Where did I come from?
> - Operations: What have I done?
> - Temporal: When do I matter?
> - Receipts: Proof of computations
> - History: Complete timeline
> - Capability: What can I become?
> - Self-Reference: Hash of myself (quine property)
> 
> Parameters:
>     cell_id: Unique cell identifier
>     lattice_coords: Position in the lattice (depth, theta, phi)
>     lineage: Optional parent lineage info
> 
> Spec: docs/spec/SHARD.md #SHARD-001
