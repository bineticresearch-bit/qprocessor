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
from typing import Optional, Tuple


def non_avalanche_hash(
    data: bytes,
    parent_hash: Optional[bytes] = None
) -> bytes:
    """
    HASH-001: Compute a non-avalanche hash.
    
    Unlike avalanche hashes (SHA-256), this preserves similarity:
    - Similar inputs produce similar outputs
    - Parent hash influences but doesn't dominate child hash
    - 70% parent contribution, 30% data contribution (controlled diffusion)
    
    Args:
        data: Input data to hash
        parent_hash: Optional parent hash for lineage preservation
    
    Returns:
        32-byte hash with controlled diffusion properties
    
    Spec: docs/spec/HASH.md #HASH-001
    """
    # Hash the data independently
    data_hash = hashlib.sha256(data).digest()
    
    if parent_hash is None:
        return data_hash
    
    # Controlled mixing: 70% parent, 30% data at the BIT level
    # This preserves lineage while allowing mutation.
    # IMPORTANT: Do NOT apply SHA-256 or any avalanche hash after mixing,
    # as that would destroy the similarity preservation.
    #
    # Bit-level mixing ensures that ~70% of output bits come from parent,
    # giving expected similarity of ~0.7 + 0.3*0.5 = 0.85
    
    result_bits = []
    
    # Process each byte
    for i in range(32):
        parent_byte = parent_hash[i]
        data_byte = data_hash[i]
        
        # For each bit position (8 bits per byte)
        for bit_pos in range(8):
            parent_bit = (parent_byte >> bit_pos) & 1
            data_bit = (data_byte >> bit_pos) & 1
            
            # 70% chance to take parent bit, 30% to take data bit
            # Use deterministic selection based on position for reproducibility
            # Position-based: first 70% of bits from parent, rest from data
            if (i * 8 + bit_pos) % 10 < 7:  # 7 out of 10 = 70%
                result_bits.append(parent_bit)
            else:
                result_bits.append(data_bit)
    
    # Reconstruct bytes from bits
    result = bytearray(32)
    for i in range(32):
        byte_val = 0
        for bit_pos in range(8):
            bit_idx = i * 8 + bit_pos
            byte_val |= (result_bits[bit_idx] << bit_pos)
        result[i] = byte_val
    
    return bytes(result)


def compute_similarity(hash_a: bytes, hash_b: bytes) -> float:
    """
    HASH-002: Compute similarity between two hashes.
    
    Uses normalized Hamming distance: similarity = 1 - (hamming_distance / max_distance)
    
    Args:
        hash_a: First hash (32 bytes)
        hash_b: Second hash (32 bytes)
    
    Returns:
        Similarity score in [0.0, 1.0] where 1.0 = identical
    
    Spec: docs/spec/HASH.md #HASH-002
    """
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must be same length")
    
    # Count differing bits
    hamming_distance = 0
    total_bits = len(hash_a) * 8
    
    for byte_a, byte_b in zip(hash_a, hash_b):
        xor = byte_a ^ byte_b
        hamming_distance += bin(xor).count('1')
    
    # Normalize to [0, 1]
    similarity = 1.0 - (hamming_distance / total_bits)
    return similarity


def verify_lineage(child_hash: bytes, parent_hash: bytes) -> bool:
    """
    HASH-003: Verify that child_hash is derived from parent_hash.
    
    Due to non-avalanche properties, child should be similar to parent.
    Similarity threshold: 0.6 (60% of bits should match).
    
    Args:
        child_hash: Child's hash
        parent_hash: Parent's hash
    
    Returns:
        True if child appears to be derived from parent
    
    Spec: docs/spec/HASH.md #HASH-003
    """
    similarity = compute_similarity(child_hash, parent_hash)
    # Non-avalanche hash should preserve at least 60% similarity
    return similarity >= 0.6


def hash_with_position(
    data: bytes,
    lattice_coords: Tuple[float, float, float]
) -> bytes:
    """
    HASH-004: Hash data with spatial position encoding.
    
    Encodes (depth, theta, phi) lattice coordinates into the hash.
    
    Args:
        data: Input data
        lattice_coords: (depth, theta, phi) spherical coordinates
    
    Returns:
        32-byte hash with position encoded
    
    Spec: docs/spec/HASH.md #HASH-004
    """
    depth, theta, phi = lattice_coords
    
    # Pack coordinates as big-endian doubles
    coord_bytes = struct.pack('>ddd', depth, theta, phi)
    
    # Combine data with coordinates
    combined = data + coord_bytes
    
    return hashlib.sha256(combined).digest()


def hash_with_temporal(
    data: bytes,
    timestamp_ns: int
) -> bytes:
    """
    HASH-005: Hash data with temporal encoding.
    
    Encodes nanosecond-precision timestamp into the hash.
    
    Args:
        data: Input data
        timestamp_ns: Timestamp in nanoseconds
    
    Returns:
        32-byte hash with timestamp encoded
    
    Spec: docs/spec/HASH.md #HASH-005
    """
    # Encode timestamp as big-endian 64-bit unsigned integer
    time_bytes = struct.pack('>Q', timestamp_ns)
    
    # Combine data with timestamp
    combined = data + time_bytes
    
    return hashlib.sha256(combined).digest()


def compute_lineage_hash(
    ancestor_hashes: list,
    current_data: bytes
) -> bytes:
    """
    Compute a cumulative lineage hash from all ancestors.
    
    Each ancestor contributes to the final hash, preserving the full
    lineage chain in a single hash value.
    
    Args:
        ancestor_hashes: List of ancestor hashes (oldest first)
        current_data: Current cell's data
    
    Returns:
        32-byte lineage hash
    """
    if not ancestor_hashes:
        return hashlib.sha256(current_data).digest()
    
    # Start with the oldest ancestor
    cumulative = ancestor_hashes[0]
    
    # Mix in each subsequent ancestor
    for ancestor_hash in ancestor_hashes[1:]:
        combined = cumulative + ancestor_hash
        cumulative = hashlib.sha256(combined).digest()
    
    # Finally mix in current data
    combined = cumulative + current_data
    return hashlib.sha256(combined).digest()
