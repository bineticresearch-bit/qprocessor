#!/bin/bash
# scripts/review.sh — Automated reviewer checks
set -e

echo "=== CELLULARIS Reviewer ==="
echo ""

# Step 1: Run all tests
echo "[1/3] Running all tests..."
bash scripts/test.sh
echo "  ✓ All tests pass"

# Step 2: Check documentation exists
echo "[2/3] Checking documentation..."
for spec in docs/spec/REGISTRY.md docs/spec/HASH.md docs/spec/PISPHERE.md docs/spec/TEMPORAL.md docs/spec/SHARD.md docs/spec/CELL.md docs/spec/CMP.md docs/spec/GENESIS.md; do
    if [ ! -f "$spec" ]; then
        echo "  ✗ Missing spec: $spec"
        exit 1
    fi
done
echo "  ✓ All specs present"

# Step 3: Check code quality
echo "[3/3] Checking code quality..."
python3 -c "
import ast, os, sys
issues = []
for root, dirs, files in os.walk('src'):
    for f in files:
        if f.endswith('.py') and f != '__init__.py':
            path = os.path.join(root, f)
            with open(path) as fh:
                tree = ast.parse(fh.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    if not ast.get_docstring(node):
                        issues.append(f'{path}:{node.lineno} — {node.name} missing docstring')
if issues:
    for i in issues[:10]:
        print(f'  ✗ {i}')
    if len(issues) > 10:
        print(f'  ... and {len(issues) - 10} more')
    sys.exit(1)
print('  ✓ All public functions documented')
"

echo ""
echo "=== REVIEW PASSED ==="
