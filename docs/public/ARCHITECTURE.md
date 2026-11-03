# Architecture Overview

QProcessor (CELLULARIS) is a quantum-inspired cellular computation framework.
This document describes the system architecture at a high level.

## System Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Applications                                                │
│  Cellular AI · Frontier AI · Network Sheaf Sensor            │
├─────────────────────────────────────────────────────────────┤
│  Computation Core                                            │
│  Cell · Shard · Pisphere · Temporal Engine · CMP             │
├─────────────────────────────────────────────────────────────┤
│  Foundations                                                 │
│  Non-Avalanche Hash · Genesis Protocol · Echo Cascades       │
└─────────────────────────────────────────────────────────────┘
```

### Foundations

- **Non-Avalanche Hash** (`src/hash/`) — a similarity-preserving hash. Unlike
  SHA-256, similar inputs produce similar outputs, which makes lineage
  verification and metric-space embedding possible.
- **Genesis Protocol** (`src/genesis/`) — seven layers of creator control:
  genesis signature, epigenetic override, temporal kill switch, steganographic
  channel, trapdoor hash, observer privilege, and covenant protocol.
- **Echo Cascades** (`src/temporal/echo.py`) — hyperfractal temporal
  precision: `Δt_effective = Δt_base × α^N`, achieving picosecond resolution
  from microsecond hardware.

### Computation Core

- **Cell** (`src/cell/cell.py`) — the fundamental computational unit. Each
  Cell carries a self-describing shard, a pisphere register lattice, and a
  temporal engine. Cells differentiate into specialized types and replicate
  through mitosis.
- **Self-Describing Shard** (`src/cell/shard.py`) — nine sections (identity,
  position, lineage, operations, temporal significance, receipts, history,
  capability, self-reference) giving every Cell complete provenance.
- **Pisphere** (`src/pisphere/`) — a recursive spherical register lattice.
  Each register is itself a sphere; depth D holds `(B^(D+1) - 1) / (B - 1)`
  registers.
- **Temporal Engine** (`src/temporal/`) — timer-based computation where time
  *is* the computation. Quantum gates map to temporal operations on timers.
- **CMP** (`src/cmp/`) — the Cell Membrane Protocol for inter-cell
  communication.

### Applications

- **Cellular AI** (`src/cellular_ai.py`) — a self-organizing AI whose cells
  differentiate into perception, reasoning, memory, and action roles, with
  self-repair through mitosis and full decision provenance.
- **Frontier Cellular AI** (`src/frontier_cellular_ai.py`) — adds learning
  from experience, self-optimization, capability expansion, and a natural
  language interface.
- **Network Sheaf** (`src/network/`) — models the global network as a sheaf
  (fiber bundle) over public observation planes, reconstructing it from the
  residual via active inference.

## Realtime Variant

`src_realtime/` mirrors `src/` with nanosecond-anchored implementations using
`time.perf_counter_ns()` for live measurement rather than simulation.

## Development Methodology

The project follows Documentation-Driven Development (D³): specifications in
`docs/spec/` are the single source of truth, code must match spec exactly,
and the reviewer system (`scripts/review.sh`) verifies compliance. See
`DEVELOPMENT_SYSTEM.md`.

## Further Reading

- `docs/spec/REGISTRY.md` — master specification index
- `docs/architecture/CellularAI.md` — Cellular AI design
- `docs/architecture/SheafFusion.md` — Network Sheaf design
- `docs/cellular_ai/README.md` — Cellular AI documentation
- `NOVEL_CAPABILITIES.md` — analysis of novel capabilities
