#!/bin/bash
# scripts/test_realtime.sh — Run all realtime (src_realtime) unit tests.
# Mirrors scripts/test.sh but targets the nanosecond-anchored variant tree,
# including Tissue / Intent Shard / Portal contract tests.
set -e

echo "=== CELLULARIS Realtime Test Suite ==="
echo ""

PASS=0
FAIL=0

for test_file in tests_realtime/unit/test_*.py; do
    [ -e "$test_file" ] || continue
    name=$(basename "$test_file" .py)
    echo "Running $name..."
    if python3 "$test_file" > /dev/null 2>&1; then
        echo "  ✓ $name PASSED"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $name FAILED"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
