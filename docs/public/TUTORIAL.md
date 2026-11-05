# Getting Started Tutorial

This tutorial walks through the core QProcessor concepts with runnable
examples.

## Prerequisites

- Python 3.9+
- No external dependencies required

## 1. Your First Cell

A Cell is the fundamental computational unit. Every Cell carries a
self-describing shard, a pisphere register lattice, and a temporal engine.

```python
from src.cell.cell import Cell, CellType

cell = Cell()
print(cell)                    # Cell(id=..., type=undifferentiated, gen=0, alive=True)
print(cell.is_alive())         # True
print(cell.get_shard())        # the self-describing shard
```

## 2. Differentiation

Cells specialize into types: GPU, CPU, MEMORY, NETWORK, IO.

```python
cell.differentiate(CellType.CPU)
print(cell.get_type())         # CellType.CPU
```

## 3. Mitosis (Self-Replication)

A Cell replicates into two daughter cells with tracked lineage. The original
undergoes apoptosis after mitosis.

```python
d1, d2 = cell.mitosis()
print(d1.get_generation())     # 1
print(cell.is_alive())         # False — the parent died
```

## 4. Temporal Precision

The temporal engine manages timers. With echo cascades enabled, each timer
achieves hyperfractal precision: `Δt_effective = Δt_base × α^N`.

```python
from src.temporal.engine import TemporalEngine

engine = TemporalEngine(resolution_us=1, echo_enabled=True, echo_depth=6)
timer = engine.create_timer(delay_us=100, phase=(0.0, 0.0))
print(engine.resolve_all_echoes().best_precision_s)   # ~1e-14 s (10 fs)
```

## 5. Cellular AI

The Cellular AI combines cells into a self-organizing system with
perception, reasoning, memory, and action roles.

```python
from src.cellular_ai import CellularAI, CellRole

ai = CellularAI()
ai.create_cell(CellRole.PERCEPTION)
ai.create_cell(CellRole.REASONING)
ai.create_cell(CellRole.MEMORY)
ai.create_cell(CellRole.ACTION)

output = ai.think({"type": "sensor", "value": 42})
print(ai.get_temporal_analysis())   # ps-scale computed ceiling (measured ~ns floor)
```

## 6. Network Sheaf

The network sheaf models the global network from public observation planes,
reconstructing it from the residual.

```python
from src.network.sensor import GlobalNetworkSensor
from src.network.sheaf import NetworkSheaf

sensor = GlobalNetworkSensor(sheaf=NetworkSheaf())
report = sensor.sense()         # one sensing cycle
print(sensor.status())          # convergence status
```

## Running the Test Suite

```bash
bash scripts/test.sh           # all unit tests
bash scripts/checkpoint.sh     # sequential milestone tests
bash scripts/review.sh         # full reviewer system
```

## Next Steps

- `docs/public/ARCHITECTURE.md` — system architecture
- `docs/public/FAQ.md` — common questions
- `docs/spec/REGISTRY.md` — master specification index
- `examples/` — runnable demonstrations
