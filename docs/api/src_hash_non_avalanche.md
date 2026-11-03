# `src.hash.non_avalanche`

## `non_avalanche_hash`

> HASH-001: Compute a non-avalanche hash.
> 
> Unlike avalanche hashes (SHA-256), similar inputs produce similar outputs.
> If parent_hash is provided, the output is influenced by the parent,
> preserving lineage relationships.
> 
> Parameters:
>     data: The data to hash (bytes)
>     parent_hash: Optional parent hash for lineage preservation (32 bytes)
> 
> Returns:
>     32-byte hash value
> 
> Spec: docs/spec/HASH.md #HASH-001
> 
> Test Cases:
>     - TC1: Same input → same output (deterministic)
>     - TC2: Similar input → similar output (non-avalanche)
>     - TC3: With parent → output influenced by parent
>     - TC4: Different parent → different output
>     - TC5: Empty data → valid hash

## `compute_similarity`

> HASH-002: Compute similarity between two hashes.
> 
> Uses normalized Hamming distance to measure how similar two hashes are.
> Returns a value in [0.0, 1.0] where 1.0 = identical.
> 
> Parameters:
>     hash_a: First hash (32 bytes)
>     hash_b: Second hash (32 bytes)
> 
> Returns:
>     Similarity score in [0.0, 1.0]
> 
> Spec: docs/spec/HASH.md #HASH-002
> 
> Test Cases:
>     - TC1: Same hash → similarity = 1.0
>     - TC2: Completely different → similarity ≈ 0.0
>     - TC3: Slightly different → similarity > 0.5
>     - TC4: Different lengths → raise ValueError

## `verify_lineage`

> HASH-003: Verify that a child hash is derived from a parent hash.
> 
> Checks that the child hash has sufficient similarity to the parent
> to be considered a legitimate descendant.
> 
> Parameters:
>     child_hash: The child's hash (32 bytes)
>     parent_hash: The parent's hash (32 bytes)
> 
> Returns:
>     True if lineage is valid, False otherwise
> 
> Spec: docs/spec/HASH.md #HASH-003
> 
> Test Cases:
>     - TC1: Valid parent-child → True
>     - TC2: Random hashes → False
>     - TC3: Same hash → True (self-lineage)

## `hash_with_position`

> HASH-004: Compute a hash that encodes spatial position.
> 
> The hash incorporates lattice coordinates (depth, theta, phi) so that
> registers at different positions have different hashes even with same data.
> 
> Parameters:
>     data: The data to hash (bytes)
>     lattice_coords: Tuple of (depth, theta, phi)
> 
> Returns:
>     32-byte position-aware hash
> 
> Spec: docs/spec/HASH.md #HASH-004
> 
> Test Cases:
>     - TC1: Same data, different position → different hash
>     - TC2: Same data, same position → same hash
>     - TC3: Different data, same position → different hash

## `hash_with_temporal`

> HASH-005: Compute a hash that encodes temporal information.
> 
> The hash incorporates a nanosecond timestamp so that the same data
> at different times produces different hashes.
> 
> Parameters:
>     data: The data to hash (bytes)
>     timestamp_ns: Timestamp in nanoseconds
> 
> Returns:
>     32-byte time-aware hash
> 
> Spec: docs/spec/HASH.md #HASH-005
> 
> Test Cases:
>     - TC1: Same data, different time → different hash
>     - TC2: Same data, same time → same hash
>     - TC3: Different data, same time → different hash
