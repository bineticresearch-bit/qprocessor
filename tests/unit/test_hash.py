"""
Unit Tests for Non-Avalanche Hash — HASH-001 through HASH-005

Spec Reference: docs/spec/HASH.md
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.hash.non_avalanche import (
    non_avalanche_hash,
    compute_similarity,
    verify_lineage,
    hash_with_position,
    hash_with_temporal,
)


def test_hash_001_deterministic():
    """HASH-001 TC1: Same input → same output."""
    data = b"hello world"
    h1 = non_avalanche_hash(data)
    h2 = non_avalanche_hash(data)
    assert h1 == h2, "Same input must produce same output"
    print("  ✓ HASH-001 TC1: Deterministic")


def test_hash_001_with_parent():
    """HASH-001 TC3: With parent → output influenced by parent."""
    data = b"child data"
    parent = b'\x01' * 32
    h_no_parent = non_avalanche_hash(data)
    h_with_parent = non_avalanche_hash(data, parent)
    assert h_no_parent != h_with_parent, "Parent must influence output"
    print("  ✓ HASH-001 TC3: Parent influences output")


def test_hash_001_non_avalanche():
    """HASH-001 TC2: Similar input → similar output."""
    data_a = b"hello world"
    data_b = b"hello worlD"  # 1 bit different
    parent = b'\x42' * 32
    
    h_a = non_avalanche_hash(data_a, parent)
    h_b = non_avalanche_hash(data_b, parent)
    
    sim = compute_similarity(h_a, h_b)
    # Non-avalanche: similar inputs should have similarity > 0.5
    assert sim > 0.5, f"Similar inputs should have high similarity, got {sim}"
    print(f"  ✓ HASH-001 TC2: Non-avalanche (similarity={sim:.3f})")


def test_hash_002_same_hash():
    """HASH-002 TC1: Same hash → similarity = 1.0."""
    h = non_avalanche_hash(b"test")
    sim = compute_similarity(h, h)
    assert sim == 1.0, f"Same hash should have similarity 1.0, got {sim}"
    print("  ✓ HASH-002 TC1: Same hash → 1.0")


def test_hash_002_different_length():
    """HASH-002 TC4: Different lengths → ValueError."""
    try:
        compute_similarity(b'\x00' * 32, b'\x00' * 16)
        assert False, "Should raise ValueError"
    except ValueError:
        print("  ✓ HASH-002 TC4: Different lengths → ValueError")


def test_hash_003_valid_lineage():
    """HASH-003 TC1: Valid parent-child → True."""
    parent = b'\x42' * 32
    child = non_avalanche_hash(b"child data", parent)
    assert verify_lineage(child, parent), "Valid lineage should verify"
    print("  ✓ HASH-003 TC1: Valid lineage → True")


def test_hash_003_self_lineage():
    """HASH-003 TC3: Same hash → True."""
    h = non_avalanche_hash(b"test")
    assert verify_lineage(h, h), "Self-lineage should verify"
    print("  ✓ HASH-003 TC3: Self-lineage → True")


def test_hash_004_position_aware():
    """HASH-004 TC1: Same data, different position → different hash."""
    data = b"register data"
    h1 = hash_with_position(data, (0, 0.0, 0.0))
    h2 = hash_with_position(data, (1, 1.0, 2.0))
    assert h1 != h2, "Different positions should produce different hashes"
    print("  ✓ HASH-004 TC1: Position-aware hash")


def test_hash_005_temporal_aware():
    """HASH-005 TC1: Same data, different time → different hash."""
    data = b"temporal data"
    h1 = hash_with_temporal(data, 1000000)
    h2 = hash_with_temporal(data, 2000000)
    assert h1 != h2, "Different times should produce different hashes"
    print("  ✓ HASH-005 TC1: Temporal-aware hash")


if __name__ == "__main__":
    print("=== Non-Avalanche Hash Tests ===")
    test_hash_001_deterministic()
    test_hash_001_with_parent()
    test_hash_001_non_avalanche()
    test_hash_002_same_hash()
    test_hash_002_different_length()
    test_hash_003_valid_lineage()
    test_hash_003_self_lineage()
    test_hash_004_position_aware()
    test_hash_005_temporal_aware()
    print("\n=== ALL HASH TESTS PASSED ===")
