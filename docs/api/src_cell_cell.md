# `src.cell.cell`

## `CellType`

> Cell differentiation types.

## `CellState`

> Snapshot of Cell state.

## `Cell`

> CELL-001: The fundamental computational unit.
> 
> Each Cell contains:
> - A self-describing shard (complete provenance)
> - A pisphere register lattice (recursive spherical registers)
> - A temporal engine (timer-based computation)
> - A differentiation engine (can become GPU, CPU, etc.)
> - A mitosis engine (self-replication)
> 
> Parameters:
>     cell_type: Initial cell type (default: UNDIFFERENTIATED)
>     pisphere_config: Configuration for pisphere lattice
>     temporal_config: Configuration for temporal engine
> 
> Spec: docs/spec/CELL.md #CELL-001
