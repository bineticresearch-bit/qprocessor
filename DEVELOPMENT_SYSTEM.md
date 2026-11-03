# CELLULARIS Rapid Development System

## Documentation-Driven Development (D³)

**Version:** 1.0  
**Date:** 2026-11-03  
**Status:** Active  
**Target Build Time:** 4–8 hours  

---

## 1. Core Principle: Documentation IS the Code

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION IS THE CODE                         │
│                                                                      │
│   docs/spec/          ← Single Source of Truth (SSOT)               │
│   ├── REGISTRY.md     ← Master specification index                  │
│   ├── CELL.md         ← Cell specification                          │
│   ├── PISPHERE.md     ← Pisphere register specification             │
│   ├── TEMPORAL.md     ← Temporal engine specification               │
│   ├── CMP.md          ← Cell Membrane Protocol specification        │
│   ├── GENESIS.md      ← Genesis Protocol specification              │
│   ├── SHARD.md        ← Self-describing shard specification         │
│   └── HASH.md         ← Non-avalanche hash specification            │
│                                                                      │
│   src/                ← Implementation (must match spec exactly)    │
│   tests/              ← Verification (must pass 100%)               │
│   scripts/            ← Automation                                  │
│                                                                      │
│   RULE: Every function in src/ MUST have a corresponding entry      │
│         in docs/spec/ with exact signature, parameters, and         │
│         expected behavior. Any deviation = BUILD FAILURE.           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Project Structure

```
qprocessor/
├── DEVELOPMENT_SYSTEM.md          ← This file
├── README.md                      ← Public overview
├── docs/
│   ├── spec/                      ← SPECIFICATIONS (SSOT)
│   │   ├── REGISTRY.md            ← Master index of ALL specs
│   │   ├── CELL.md                ← Cell class specification
│   │   ├── PISPHERE.md            ← Pisphere register specification
│   │   ├── TEMPORAL.md            ← Temporal engine specification
│   │   ├── CMP.md                 ← Cell Membrane Protocol spec
│   │   ├── GENESIS.md             ← Genesis Protocol spec (CREATOR-ONLY)
│   │   ├── SHARD.md               ← Self-describing shard spec
│   │   ├── HASH.md                ← Non-avalanche hash spec
│   │   ├── DIFFERENTIATION.md     ← Cell differentiation spec
│   │   ├── MITOSIS.md             ← Cell replication spec
│   │   ├── COVENANT.md            ← Immutable rules spec (CREATOR-ONLY)
│   │   └── CONSTRUCTOR.md         ← Universal constructor spec
│   ├── public/                    ← Public-facing documentation
│   │   ├── ARCHITECTURE.md        ← System architecture overview
│   │   ├── TUTORIAL.md            ← Getting started guide
│   │   └── FAQ.md                 ← Frequently asked questions
│   ├── creator/                   ← Creator-only documentation
│   │   ├── DEMIURGE_CONSOLE.md    ← Creator interface spec
│   │   ├── KILL_SWITCH.md         ← Kill switch operations
│   │   ├── EPIGENETIC.md          ← Epigenetic override guide
│   │   └── STEGANOGRAPHY.md       ← Hidden channel guide
│   └── api/                       ← API reference (auto-generated)
│       ├── cell_api.md
│       ├── pisphere_api.md
│       ├── temporal_api.md
│       ├── cmp_api.md
│       └── genesis_api.md
├── src/
│   ├── __init__.py
│   ├── cell/
│   │   ├── __init__.py
│   │   ├── cell.py                ← Core Cell class
│   │   ├── shard.py               ← Self-describing shard
│   │   ├── differentiation.py     ← Cell differentiation engine
│   │   └── mitosis.py             ← Cell replication engine
│   ├── pisphere/
│   │   ├── __init__.py
│   │   ├── pisphere.py            ← Pisphere register lattice
│   │   ├── register.py            ← Individual register
│   │   └── coordinates.py         ← Spherical coordinate system
│   ├── temporal/
│   │   ├── __init__.py
│   │   ├── engine.py              ← Temporal computation engine
│   │   ├── timer.py               ← Recursive timer
│   │   ├── gates.py               ← Temporal quantum gates
│   │   └── trigonometric.py       ← Trig temporal logic
│   ├── genesis/
│   │   ├── __init__.py
│   │   ├── genesis.py             ← Genesis signature
│   │   ├── kill_switch.py         ← Temporal kill switch
│   │   ├── epigenetic.py          ← Epigenetic override
│   │   ├── steganography.py       ← Hidden channel
│   │   ├── trapdoor.py            ← Trapdoor hash
│   │   ├── observer.py            ← Observer privilege
│   │   ├── covenant.py            ← Covenant protocol
│   │   └── demiurge.py            ← Demiurge console
│   ├── cmp/
│   │   ├── __init__.py
│   │   ├── protocol.py            ← CMP frame format
│   │   ├── transport.py           ← Transport layer
│   │   └── messages.py            ← Message types
│   └── hash/
│       ├── __init__.py
│       └── non_avalanche.py       ← Non-avalanche hash function
├── tests/
│   ├── __init__.py
│   ├── conftest.py                ← Shared fixtures
│   ├── unit/                      ← Unit tests (per spec)
│   │   ├── test_cell.py
│   │   ├── test_pisphere.py
│   │   ├── test_temporal.py
│   │   ├── test_cmp.py
│   │   ├── test_genesis.py
│   │   ├── test_shard.py
│   │   └── test_hash.py
│   ├── integration/               ← Integration tests
│   │   ├── test_cell_communication.py
│   │   ├── test_mitosis_chain.py
│   │   ├── test_differentiation.py
│   │   └── test_emergent_computer.py
│   └── checkpoints/               ← Checkpoint tests
│       ├── checkpoint_1_single_cell.py
│       ├── checkpoint_2_cell_pair.py
│       ├── checkpoint_3_cell_population.py
│       ├── checkpoint_4_differentiation.py
│       ├── checkpoint_5_mitosis.py
│       ├── checkpoint_6_genesis_control.py
│       └── checkpoint_7_emergent_computer.py
├── scripts/
│   ├── build.sh                   ← Build and verify
│   ├── test.sh                    ← Run all tests
│   ├── checkpoint.sh              ← Run checkpoint tests
│   ├── review.sh                  ← Run reviewer checks
│   ├── generate_api_docs.py       ← Auto-generate API docs
│   └── verify_spec_compliance.py  ← Verify code matches spec
└── examples/
    ├── single_cell.py             ← Basic Cell example
    ├── cell_pair.py               ← Two Cells communicating
    ├── cell_population.py         ← Self-organizing population
    └── emergent_gpu.py            ← Cells forming a GPU
```

---

## 3. Development Workflow

### 3.1 The Build Cycle (Per Component)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPONENT BUILD CYCLE                             │
│                                                                      │
│  Step 1: SPEC FIRST                                                │
│  ├── Write spec in docs/spec/<COMPONENT>.md                        │
│  ├── Define ALL functions, parameters, return types                │
│  ├── Define ALL edge cases and error conditions                    │
│  ├── Define ALL test cases                                         │
│  └── Spec MUST be complete before any code is written              │
│                                                                      │
│  Step 2: IMPLEMENT                                                 │
│  ├── Write code in src/<component>/                                │
│  ├── Every function MUST match spec signature exactly              │
│  ├── Every parameter MUST match spec type exactly                  │
│  ├── Every return value MUST match spec format exactly             │
│  └── Docstrings MUST reference spec section                        │
│                                                                      │
│  Step 3: TEST                                                      │
│  ├── Write tests in tests/unit/test_<component>.py                 │
│  ├── Every spec requirement MUST have a test                       │
│  ├── Every edge case MUST have a test                              │
│  └── Tests MUST pass 100% before proceeding                        │
│                                                                      │
│  Step 4: VERIFY                                                    │
│  ├── Run verify_spec_compliance.py                                 │
│  ├── Run review.sh                                                 │
│  ├── All checks MUST pass                                          │
│  └── Any deviation = REJECT and return to Step 1 or 2             │
│                                                                      │
│  Step 5: CHECKPOINT                                                │
│  ├── Run checkpoint tests                                          │
│  ├── Compare output to expected results in spec                    │
│  └── Checkpoint MUST pass before moving to next component          │
│                                                                      │
│  Step 6: DOCUMENT                                                  │
│  ├── Update docs/api/<component>_api.md                            │
│  ├── Update docs/public/ if user-facing                            │
│  └── Update REGISTRY.md                                            │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Time Budget

| Component | Spec | Implement | Test | Verify | Total |
|-----------|------|-----------|------|--------|-------|
| Hash (non-avalanche) | 10 min | 15 min | 10 min | 5 min | 40 min |
| Pisphere Register | 15 min | 20 min | 15 min | 5 min | 55 min |
| Temporal Timer | 15 min | 20 min | 15 min | 5 min | 55 min |
| Temporal Gates | 15 min | 25 min | 15 min | 5 min | 60 min |
| Self-Describing Shard | 15 min | 20 min | 15 min | 5 min | 55 min |
| Cell Core | 20 min | 30 min | 20 min | 10 min | 80 min |
| CMP Protocol | 20 min | 25 min | 20 min | 10 min | 75 min |
| Cell Differentiation | 15 min | 20 min | 15 min | 5 min | 55 min |
| Cell Mitosis | 15 min | 20 min | 15 min | 5 min | 55 min |
| Genesis Signature | 15 min | 20 min | 15 min | 5 min | 55 min |
| Kill Switch | 10 min | 15 min | 10 min | 5 min | 40 min |
| Epigenetic Override | 10 min | 15 min | 10 min | 5 min | 40 min |
| Demiurge Console | 15 min | 20 min | 15 min | 5 min | 55 min |
| **TOTAL** | **~3 hrs** | **~4 hrs** | **~3 hrs** | **~1 hr** | **~8 hrs** |

---

## 4. The Reviewer System

### 4.1 Reviewer Role

The Reviewer is an automated + manual verification step that checks:

1. **Spec Compliance:** Every function in code matches the spec exactly
2. **Test Coverage:** Every spec requirement has a corresponding test
3. **Documentation Completeness:** Every function is documented
4. **Checkpoint Passage:** All checkpoint tests pass
5. **No Deviation:** No undocumented behavior exists

### 4.2 Reviewer Checklist

```
REVIEWER CHECKLIST — Run after every component build

□ SPEC CHECK
  □ Every public function has a spec entry
  □ Every spec entry has: name, params, return type, description
  □ Every spec entry has: edge cases, error conditions
  □ Every spec entry has: at least 3 test cases

□ CODE CHECK
  □ Every function signature matches spec exactly
  □ Every parameter type matches spec exactly
  □ Every return type matches spec exactly
  □ Every docstring references spec section number
  □ No undocumented public functions exist
  □ No private functions bypass spec requirements

□ TEST CHECK
  □ Every spec requirement has a test
  □ Every edge case has a test
  □ Every error condition has a test
  □ All tests pass (0 failures, 0 skips)
  □ Test coverage ≥ 95%

□ CHECKPOINT CHECK
  □ Checkpoint output matches expected output exactly
  □ No timing drift > 1% from spec
  □ No memory usage > 2× spec estimate
  □ No undocumented side effects

□ DOCUMENTATION CHECK
  □ API docs generated and up to date
  □ Public docs updated if user-facing changes
  □ REGISTRY.md updated with new entries
  □ Cross-references are valid

□ INTEGRITY CHECK
  □ verify_spec_compliance.py passes
  □ review.sh passes
  □ No TODO/FIXME/HACK comments in production code
  □ No hardcoded values without spec reference
```

### 4.3 Automated Review Script

```bash
#!/bin/bash
# scripts/review.sh — Automated reviewer

set -e

echo "=== CELLULARIS Reviewer ==="
echo ""

# Step 1: Spec compliance
echo "[1/5] Checking spec compliance..."
python3 scripts/verify_spec_compliance.py
echo "  ✓ Spec compliance OK"

# Step 2: Run all tests
echo "[2/5] Running all tests..."
python3 -m pytest tests/ -v --tb=short
echo "  ✓ All tests pass"

# Step 3: Checkpoint tests
echo "[3/5] Running checkpoint tests..."
bash scripts/checkpoint.sh
echo "  ✓ All checkpoints pass"

# Step 4: Documentation
echo "[4/5] Checking documentation..."
python3 scripts/generate_api_docs.py --verify
echo "  ✓ Documentation OK"

# Step 5: Code quality
echo "[5/5] Checking code quality..."
python3 -c "
import ast, os, sys
issues = []
for root, dirs, files in os.walk('src'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fh:
                tree = ast.parse(fh.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    if not ast.get_docstring(node):
                        issues.append(f'{path}:{node.lineno} — {node.name} missing docstring')
if issues:
    for i in issues:
        print(f'  ✗ {i}')
    sys.exit(1)
print('  ✓ All public functions documented')
"

echo ""
echo "=== REVIEW PASSED ==="
```

---

## 5. Checkpoint System

### 5.1 Checkpoint Philosophy

Each checkpoint is a **milestone** that verifies a complete subsystem works correctly. Checkpoints are **sequential** — you cannot pass checkpoint N+1 without passing checkpoint N.

### 5.2 Checkpoint Definitions

| Checkpoint | Name | What It Verifies | Pass Criteria |
|------------|------|------------------|---------------|
| CP-1 | Single Cell | A Cell can be created, has a shard, has a pisphere | Cell exists, shard is valid, pisphere has correct register count |
| CP-2 | Cell Pair | Two Cells can communicate via CMP | Messages sent and received correctly, latency < spec |
| CP-3 | Cell Population | 10+ Cells can self-organize | Population stabilizes, communication graph is connected |
| CP-4 | Differentiation | Cells can differentiate into types | GPU/CPU/Memory/Network types created correctly |
| CP-5 | Mitosis | Cells can replicate | Daughter cells have correct lineage, shard, and state |
| CP-6 | Genesis Control | Creator can control all Cells | Kill switch works, epigenetic marks apply, observer collapses state |
| CP-7 | Emergent Computer | Cells form a functional computer | Can execute a simple program using differentiated Cells |

### 5.3 Checkpoint Execution

```bash
#!/bin/bash
# scripts/checkpoint.sh

set -e

echo "=== CELLULARIS Checkpoint System ==="
echo ""

for cp in tests/checkpoints/checkpoint_*.py; do
    name=$(basename "$cp" .py)
    echo "Running $name..."
    python3 "$cp"
    if [ $? -eq 0 ]; then
        echo "  ✓ $name PASSED"
    else
        echo "  ✗ $name FAILED"
        exit 1
    fi
done

echo ""
echo "=== ALL CHECKPOINTS PASSED ==="
```

---

## 6. Build Command

```bash
# Full build (spec → code → test → verify → document)
bash scripts/build.sh

# Quick test (code → test only)
bash scripts/test.sh

# Run checkpoints only
bash scripts/checkpoint.sh

# Run reviewer only
bash scripts/review.sh
```

---

## 7. Rules

1. **No code without spec.** Every function must be specified before implementation.
2. **No deviation.** Code must match spec exactly. Any change requires spec update first.
3. **No merge without review.** All code must pass the reviewer checklist.
4. **No skip checkpoints.** Checkpoints are sequential and mandatory.
5. **Documentation is code.** Docs are versioned, tested, and reviewed alongside code.
6. **Single source of truth.** The spec registry is the only authority. Conflicts resolved by spec.

---

*This development system ensures that the final result is identical to the designed system without deviation.*
