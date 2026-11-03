#!/bin/bash
# scripts/checkpoint.sh — Run checkpoint tests sequentially
set -e

echo "=== CELLULARIS Checkpoint System ==="
echo ""

for cp in tests/checkpoints/checkpoint_*.py; do
    name=$(basename "$cp" .py)
    echo "Running $name..."
    if python3 "$cp" > /dev/null 2>&1; then
        echo "  ✓ $name PASSED"
    else
        echo "  ✗ $name FAILED"
        exit 1
    fi
done

echo ""
echo "=== ALL CHECKPOINTS PASSED ==="
