#!/bin/bash
# scripts/build.sh — Full build: verify tests, review, checkpoints
set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           CELLULARIS Build System v1.0                   ║"
echo "║   Documentation-Driven Development (D³)                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")/.."

# Step 1: Run all tests (standard + realtime)
echo "━━━ Step 1: Unit Tests (standard) ━━━"
bash scripts/test.sh

echo ""
echo "━━━ Step 1b: Unit Tests (realtime / Tissue + Intent Shard + Portal) ━━━"
bash scripts/test_realtime.sh
echo ""

# Step 2: Run reviewer
echo "━━━ Step 2: Reviewer Checks ━━━"
bash scripts/review.sh
echo ""

# Step 3: Run checkpoints
echo "━━━ Step 3: Checkpoint Tests ━━━"
bash scripts/checkpoint.sh
echo ""

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              ✓ BUILD SUCCESSFUL                          ║"
echo "║   All tests passed. All checkpoints passed.              ║"
echo "║   Code matches specification. No deviation detected.     ║"
echo "╚═══════════════════════════════════════════════════════════╝"
