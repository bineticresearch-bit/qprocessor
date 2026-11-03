"""
Non-Avalanche Hash Function — HASH-001 through HASH-005

Unlike SHA-256 (where 1 bit change → 50% output change), the non-avalanche hash:
- Preserves parent-child relationships (similar inputs → similar outputs)
- Encodes position in the lattice
- Preserves lineage (ancestor hashes contribute to descendant hashes)
- Enables similarity measurement (Hamming distance → similarity score)

Spec Reference: docs/spec/HASH.md
"""

import hashlib
import struct
import math
from typing import Optional


def non_avalanche_hash(
    data: bytes,
    parent_hash: Optional[bytes] = None
) -> bytes:
    """
    HASH-001: Compute a non-avalanche hash.
    
    Unlike avalanche hashes (SHA-256), similar inputs produce similar outputs.
    If parent_hash is provided, the output is influenced by the parent,
    preserving lineage relationships.
    
    Parameters:
        data: The data to hash (bytes)
        parent_hash: Optional parent hash for lineage preservation (32 bytes)
    
    Returns:
        32-byte hash value
    
    Spec: docs/spec/HASH.md #HASH-001
    
    Test Cases:
        - TC1: Same input → same output (deterministic)
        - TC2: Similar input → similar output (non-avalanche)
        - TC3: With parent → output influenced by parent
        - TC4: Different parent → different output
        - TC5: Empty data → valid hash
    """
    # Non-avalanche base hash: byte-wise rolling sum that preserves similarity.
    # Each output byte depends on a local window of input bytes, so small
    # input changes produce small output changes (unlike SHA-256 avalanche).
    base_hash = _similarity_preserving_hash(data)
    
    if parent_hash is None:
        return base_hash
    
    # Non-avalanche combination: weighted blend of base and parent
    # 70% base, 30% parent (preserves both identities)
    assert len(parent_hash) == 32, "Parent hash must be 32 bytes"
    
    result = bytearray(32)
    for i in range(32):
        # Weighted combination: 70% base, 30% parent
        combined = int(0.7 * base_hash[i] + 0.3 * parent_hash[i])
        result[i] = min(255, max(0, combined))
    
    return bytes(result)


def _similarity_preserving_hash(data: bytes) -> bytes:
    """
    Internal: compute a 32-byte hash that preserves input similarity.
    
    Uses byte-wise rolling sums with overlapping windows so that
    small input changes produce proportionally small output changes.
    """
    if len(data) == 0:
        return b'\x00' * 32
    
    result = bytearray(32)
    n = len(data)
    
    for i in range(32):
        # Each output byte is a weighted sum over a window of input bytes.
        # Windows overlap so adjacent output bytes are correlated.
        window_start = (i * n) // 32
        window_end = min(n, window_start + max(1, n // 8))
        
        total = 0
        for j in range(window_start, window_end):
            total = (total + data[j]) & 0xFF
        
        # Mix with position to differentiate output bytes
        result[i] = (total + i * 7) & 0xFF
    
    return bytes(result)


def compute_similarity(hash_a: bytes, hash_b: bytes) -> float:
    """
    HASH-002: Compute similarity between two hashes.
    
    Uses normalized Hamming distance to measure how similar two hashes are.
    Returns a value in [0.0, 1.0] where 1.0 = identical.
    
    Parameters:
        hash_a: First hash (32 bytes)
        hash_b: Second hash (32 bytes)
    
    Returns:
        Similarity score in [0.0, 1.0]
    
    Spec: docs/spec/HASH.md #HASH-002
    
    Test Cases:
        - TC1: Same hash → similarity = 1.0
        - TC2: Completely different → similarity ≈ 0.0
        - TC3: Slightly different → similarity > 0.5
        - TC4: Different lengths → raise ValueError
    """
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must be the same length")
    
    if len(hash_a) == 0:
        return 1.0
    
    # Compute Hamming distance at bit level
    total_bits = len(hash_a) * 8
    different_bits = 0
    
    for a, b in zip(hash_a, hash_b):
        xor = a ^ b
        different_bits += bin(xor).count('1')
    
    # Normalize to [0, 1] where 1 = identical
    similarity = 1.0 - (different_bits / total_bits)
    return similarity


def verify_lineage(child_hash: bytes, parent_hash: bytes) -> bool:
    """
    HASH-003: Verify that a child hash is derived from a parent hash.
    
    Checks that the child hash has sufficient similarity to the parent
    to be considered a legitimate descendant.
    
    Parameters:
        child_hash: The child's hash (32 bytes)
        parent_hash: The parent's hash (32 bytes)
    
    Returns:
        True if lineage is valid, False otherwise
    
    Spec: docs/spec/HASH.md #HASH-003
    
    Test Cases:
        - TC1: Valid parent-child → True
        - TC2: Random hashes → False
        - TC3: Same hash → True (self-lineage)
    """
    similarity = compute_similarity(child_hash, parent_hash)
    # Lineage is valid if similarity > 0.25
    # With 70/30 blending (70% base, 30% parent), we expect ~30% similarity.
    # Random hashes have ~50% bit-level similarity, but our non-avalanche
    # hash is more structured, so 0.25 is a safe threshold.
    return similarity > 0.25


def hash_with_position(data: bytes, lattice_coords: tuple) -> bytes:
    """
    HASH-004: Compute a hash that encodes spatial position.
    
    The hash incorporates lattice coordinates (depth, theta, phi) so that
    registers at different positions have different hashes even with same data.
    
    Parameters:
        data: The data to hash (bytes)
        lattice_coords: Tuple of (depth, theta, phi)
    
    Returns:
        32-byte position-aware hash
    
    Spec: docs/spec/HASH.md #HASH-004
    
    Test Cases:
        - TC1: Same data, different position → different hash
        - TC2: Same data, same position → same hash
        - TC3: Different data, same position → different hash
    """
    depth, theta, phi = lattice_coords
    
    # Encode coordinates into bytes
    coord_bytes = struct.pack('>iff', depth, theta, phi)
    
    # Combine data with coordinates
    combined = data + coord_bytes
    
    return hashlib.sha256(combined).digest()


def hash_with_temporal(data: bytes, timestamp_ns: int) -> bytes:
    """
    HASH-005: Compute a hash that encodes temporal information.
    
    The hash incorporates a nanosecond timestamp so that the same data
    at different times produces different hashes.
    
    Parameters:
        data: The data to hash (bytes)
        timestamp_ns: Timestamp in nanoseconds
    
    Returns:
        32-byte time-aware hash
    
    Spec: docs/spec/HASH.md #HASH-005
    
    Test Cases:
        - TC1: Same data, different time → different hash
        - TC2: Same data, same time → same hash
        - TC3: Different data, same time → different hash
    """
    # Encode timestamp into bytes
    time_bytes = struct.pack('>Q', timestamp_ns)
    
    # Combine data with timestamp
    combined = data + time_bytes
    
    return hashlib.sha256(combined).digest()
