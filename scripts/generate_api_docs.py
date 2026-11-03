#!/usr/bin/env python3
"""
API Documentation Generator
===========================

Generates API reference documentation for every public function and class
in src/, and verifies that generated docs are present. This is step 4 of
the reviewer system (DEVELOPMENT_SYSTEM.md §4.3).

Usage:
    python3 scripts/generate_api_docs.py           # generate docs
    python3 scripts/generate_api_docs.py --verify  # verify docs exist

Exit codes:
    0 = ok
    1 = verification failed
"""

import argparse
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(ROOT, "docs", "api")


def collect_symbols():
    """Collect public functions and classes per module under src/."""
    modules = {}

    for root, dirs, files in os.walk(os.path.join(ROOT, "src")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fname in sorted(files):
            if not fname.endswith(".py"):
                continue
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, ROOT)
            mod_name = rel[:-3].replace(os.sep, ".")

            with open(path) as fh:
                try:
                    tree = ast.parse(fh.read(), filename=path)
                except SyntaxError:
                    continue

            symbols = []
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                    if node.name.startswith("_"):
                        continue
                    doc = ast.get_docstring(node) or "(no docstring)"
                    symbols.append((node.name, doc))
            if symbols:
                modules[mod_name] = symbols

    return modules


def render_module(mod_name, symbols):
    """Render one module's API reference as markdown."""
    lines = [f"# `{mod_name}`", ""]
    for name, doc in symbols:
        lines.append(f"## `{name}`")
        lines.append("")
        for ln in doc.strip().splitlines():
            lines.append(f"> {ln}")
        lines.append("")
    return "\n".join(lines)


def generate():
    """Generate API docs for all modules."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    modules = collect_symbols()

    written = []
    for mod_name, symbols in sorted(modules.items()):
        out = os.path.join(DOCS_DIR, f"{mod_name.replace('.', '_')}.md")
        with open(out, "w") as fh:
            fh.write(render_module(mod_name, symbols))
        written.append(os.path.relpath(out, ROOT))

    print(f"✓ Generated {len(written)} API doc file(s) in docs/api/")
    return 0


def verify():
    """Verify that API docs exist and are non-empty."""
    if not os.path.isdir(DOCS_DIR):
        print("✗ docs/api/ does not exist — run without --verify first")
        return 1

    docs = [f for f in os.listdir(DOCS_DIR) if f.endswith(".md")]
    if not docs:
        print("✗ docs/api/ is empty — run without --verify first")
        return 1

    empty = []
    for f in sorted(docs):
        path = os.path.join(DOCS_DIR, f)
        if os.path.getsize(path) == 0:
            empty.append(f)

    if empty:
        for f in empty:
            print(f"  ✗ {f} is empty")
        return 1

    print(f"✓ {len(docs)} API doc file(s) present and non-empty")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true",
                        help="verify docs exist rather than generate")
    args = parser.parse_args()

    print("=== API Documentation ===")
    return verify() if args.verify else generate()


if __name__ == "__main__":
    sys.exit(main())
