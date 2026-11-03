# `src.cmp.protocol`

## `MessageType`

> CMP-009 through CMP-021: Message types.

## `CMPFrame`

> CMP-001: A Cell Membrane Protocol frame.
> 
> Frame format (36 bytes header + variable payload):
> - Version (4 bits) + Msg Type (4 bits) + Flags (8 bits)
> - Source Cell ID (64 bits)
> - Destination Cell ID (64 bits)
> - Lattice Coordinates (96 bits): depth(8) + theta(44) + phi(44)
> - Timestamp (64 bits, nanoseconds)
> - Phase θ (16 bits) + Phase φ (16 bits) + Shard Hash Ref (32 bits)
> - Payload Length (16 bits) + Payload (variable)
> - CRC-32 Checksum (32 bits)
> 
> Spec: docs/spec/CMP.md #CMP-001
