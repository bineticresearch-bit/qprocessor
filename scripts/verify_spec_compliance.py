#!/usr/bin/env python3
"""
Spec Compliance Verifier
========================

Verifies that every public function and class in src/ has a docstring, and
that every spec-referenced module imports cleanly. This is step 1 of the
reviewer system (DEVELOPMENT_SYSTEM.md §4.3).

Exit codes:
    0 = compliant
    1 = violations found
"""

import ast
import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def check_docstrings():
    """Every public function/class in src/ must have a docstring."""
    violations = []

    for root, dirs, files in os.walk(os.path.join(ROOT, "src")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fname in sorted(files):
            if not fname.endswith(".py"):
                continue
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, ROOT)
            with open(path) as fh:
                try:
                    tree = ast.parse(fh.read(), filename=path)
                except SyntaxError as e:
                    violations.append(f"{rel}: SYNTAX ERROR {e}")
                    continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                    if node.name.startswith("_"):
                        continue
                    if not ast.get_docstring(node):
                        violations.append(
                            f"{rel}:{node.lineno} — "
                            f"{node.name} missing docstring"
                        )

    return violations


def check_imports():
    """Every module under src/ must import cleanly."""
    failures = []

    for root, dirs, files in os.walk(os.path.join(ROOT, "src")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fname in sorted(files):
            if not fname.endswith(".py") or fname == "__init__.py":
                continue
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, ROOT)
            mod = rel[:-3].replace(os.sep, ".")
            try:
                importlib.import_module(mod)
            except Exception as e:
                failures.append(f"{rel}: IMPORT ERROR {type(e).__name__}: {e}")

    return failures


def main():
    print("=== Spec Compliance Check ===")

    print("[1/2] Checking docstrings...")
    doc_violations = check_docstrings()
    if doc_violations:
        for v in doc_violations:
            print(f"  ✗ {v}")
    else:
        print("  ✓ All public functions and classes documented")

    print("[2/2] Checking imports...")
    import_failures = check_imports()
    if import_failures:
        for v in import_failures:
            print(f"  ✗ {v}")
    else:
        print("  ✓ All modules import cleanly")

    total = len(doc_violations) + len(import_failures)
    print()
    if total:
        print(f"✗ SPEC COMPLIANCE FAILED: {total} violation(s)")
        return 1
    print("✓ SPEC COMPLIANCE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
