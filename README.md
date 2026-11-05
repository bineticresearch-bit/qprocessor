# QProcessor (CELLULARIS)

A quantum-inspired cellular computation framework with hyperfractal temporal
precision, self-organizing AI, and sheaf-theoretic network sensing.

## What's here

**Cellular computation core** (`src/`)
- `cell/` — self-describing Cells with shards, differentiation, and mitosis
- `pisphere/` — recursive spherical register lattice
- `temporal/` — timer-based computation, quantum gates, echo cascades
- `genesis/` — 7-layer creator control protocol
- `cmp/` — Cell Membrane Protocol (inter-cell communication)
- `hash/` — non-avalanche (similarity-preserving) hash
- `cellular_ai.py` — self-organizing Cellular AI
- `frontier_cellular_ai.py` — learning, self-optimizing AI with natural language
- `network/` — sheaf-theoretic meta-network sensor

**Realtime variant** (`src_realtime/`) — nanosecond-anchored implementations
using `perf_counter_ns` for live measurement.

## Quick start

```bash
# Run all unit tests
bash scripts/test.sh

# Run checkpoint tests (sequential milestones)
bash scripts/checkpoint.sh

# Full build: spec compliance + tests + checkpoints + docs + quality
bash scripts/build.sh

# Reviewer checks
bash scripts/review.sh
```

## Demos

```bash
python3 examples/demo_echo_hyperfractal.py   # ps-scale computed ceiling; measured ~ns floor on std HW
python3 examples/cellular_ai_demo.py         # self-organizing AI
python3 examples/network_sheaf_demo.py       # meta-network reconstruction
```

## Key results

- **Temporal precision:** picosecond-scale *computed* ceiling
  (`Δt_eff = Δt_base × α^N`; e.g. 1 μs base → ~1 ps at N=6) from microsecond
  hardware via hyperfractal echo cascades and the TRIANGULATE echo-phase vernier.
  **Measured floor on standard macOS hardware: ~83–167 ns** — the marquee `ps`
  figure is a formula until TC-TL9 recovers an injected delay within measured σ
  (D³ no-overclaim rule; see `docs/spec/TRIANGULATE.md`, `scripts/benchmark.py`).
- **Network reconstruction:** the sheaf model reconstructs a network to 0.142
  error having measured only ~18% of it (see
  `tests/unit/test_network_sheaf.py`)

## Documentation

- `DEVELOPMENT_SYSTEM.md` — the documentation-driven development (D³) methodology
- `NOVEL_CAPABILITIES.md` — analysis of novel capabilities
- `docs/spec/` — specifications (single source of truth)
- `docs/architecture/` — Cellular AI and Network Sheaf designs
- `docs/cellular_ai/` — Cellular AI system documentation
- `docs/public/` — public-facing documentation

## Development methodology

This project follows **Documentation-Driven Development (D³)**: every function
is specified before implementation, code must match spec exactly, and the
reviewer system verifies compliance. See `DEVELOPMENT_SYSTEM.md`.

## License

Proprietary. All rights reserved.
