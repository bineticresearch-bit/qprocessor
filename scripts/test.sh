#!/bin/bash
# scripts/test.sh — Run all unit tests
set -e

echo "=== CELLULARIS Test Suite ==="
echo ""

PASS=0
FAIL=0

for test_file in tests/unit/test_*.py; do
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

if [ $FAIL -gt 0 ]; then
    exit 1
fi
