"""
Unit Tests for Lane Framing — LANE-001 through LANE-008

Spec Reference: docs/spec/LANE-ISA.md §6 (TC-L1, TC-L2, TC-L3)
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.lane.framing import (
    LaneFrame, TrainAssembler, ReassemblyPolicy, AssemblerState,
    TruncatedLaneError, IncompleteTrainError, DATAGRAM_SIZE, LANE_PAYLOAD_SIZE,
)


def _lane(k: int, n: int, tag: bytes, train_id=0xA11CE):
    # Place op-data AFTER the temporal preamble so LaneFrame keeps it intact.
    pre = b"\x00" * LaneFrame.TEMPORAL_PREAMBLE
    payload = (pre + tag + bytes(40 - len(pre) - len(tag)))[:LANE_PAYLOAD_SIZE]
    return LaneFrame(lane_index=k, train_id=train_id, total_lanes=n,
                     payload_40b=payload)


def test_tc_l1_exact_reassembly():
    """TC-L1: A 3-lane train reassembles to the exact logical header bytes."""
    n = 3
    frames = [_lane(k, n, f"LANE{k}-PAYLOAD-".encode()) for k in range(n)]

    policy = ReassemblyPolicy(window_ns=25_000_000)
    expected = b""
    for fr in frames:
        asm = policy.get_or_create(fr)
        state = asm.feed(fr)
        expected += fr.payload_40b

    completed = policy.collect_completed()
    assert len(completed) == 1, f"expected 1 completed header, got {len(completed)}"
    P = LaneFrame.TEMPORAL_PREAMBLE
    # Compare the op-data region (after each lane's temporal preamble).
    for k in range(n):
        got_op = completed[0][k*40 + P:(k+1)*40]
        exp_op = expected[k*40 + P:(k+1)*40]
        assert got_op == exp_op, f"lane {k} op-data mismatch after reassembly"
    assert len(completed[0]) == n * LANE_PAYLOAD_SIZE
    print(f"✓ TC-L1: 3-lane train reassembled exactly ({n*LANE_PAYLOAD_SIZE} bytes)")


def test_tc_l2_out_of_order_arrival():
    """TC-L2: Out-of-order arrival (2,0,1) still completes; execution order is
    lane order, not arrival order."""
    n = 3
    frames = [_lane(k, n, f"OP{k}-EXEC-".encode()) for k in range(n)]

    policy = ReassemblyPolicy(window_ns=25_000_000)
    asm = None
    # Arrival order: lane 2 first, then 0, then 1.
    for k in (2, 0, 1):
        asm = policy.get_or_create(frames[k])
        state = asm.feed(frames[k])

    assert asm.state == AssemblerState.COMPLETE
    header = asm.reassembled_header()

    # Op data sits after the 12-byte temporal preamble (LaneFrame.TEMPORAL_PREAMBLE).
    P = LaneFrame.TEMPORAL_PREAMBLE
    exec_log = [header[k*40 + P:(k*40 + P) + 6].decode().rstrip("\x00") for k in range(n)]
    assert exec_log == ["OP0-EX", "OP1-EX", "OP2-EX"], f"exec order wrong: {exec_log}"

    # Header bytes are lane-index ordered, not arrival-order.
    assert header[P:P+6] == b"OP0-EX" and header[80 + P:80 + P + 6] == b"OP2-EX"
    print("✓ TC-L2: out-of-order (2,0,1) → COMPLETE; execution in lane order")


def test_tc_l3_missing_lane_expiry():
    """TC-L3: Missing lane 1 → window expiry → EXPIRED + ResidualEvent naming missing=[1]."""
    n = 3
    frames = [_lane(k, n, f"DATA{k}-".encode()) for k in range(n)]

    # Tiny window so expiry is immediate and deterministic.
    policy = ReassemblyPolicy(window_ns=2_000_000)  # 2 ms
    asm = None
    for k in (0, 2):          # lane 1 never arrives
        asm = policy.get_or_create(frames[k])
        state = asm.feed(frames[k])

    assert asm.state == AssemblerState.PARTIAL, "should still be PARTIAL inside window"
    try:
        asm.reassembled_header()
        raise AssertionError("expected IncompleteTrainError")
    except IncompleteTrainError:
        pass

    time.sleep(0.003)  # cross the 2 ms window
    state = asm.feed(frames[0])   # re-feed wakes expiry check
    assert state == AssemblerState.EXPIRED, f"expected EXPIRED, got {state}"

    residuals = policy.collect_expired()
    assert len(residuals) == 1, f"expected 1 residual, got {len(residuals)}"
    ev = residuals[0]
    assert list(ev.missing_lanes) == [1], f"missing lanes wrong: {ev.missing_lanes}"
    assert ev.train_id == frames[0].train_id
    assert ev.residual_magnitude >= 0.0
    print(f"✓ TC-L3: missing lane → EXPIRED, residual names missing=[{list(ev.missing_lanes)}], "
          f"|res|={ev.residual_magnitude:.2f}")


def test_frame_wire_roundtrip():
    """LANE-002/003: serialize→deserialize round-trips all fields; short/CRC-corrupt rejected."""
    fr = _lane(1, 4, "ROUNDTRIP-PAYLOAD".encode(), train_id=0xDEADBEEF)
    data = fr.serialize()
    assert len(data) == DATAGRAM_SIZE == 60

    back = LaneFrame.deserialize(data)
    assert back.lane_index == 1 and back.total_lanes == 4
    assert back.train_id == 0xDEADBEEF
    assert back.payload_40b == fr.payload_40b
    assert back.phase_theta == fr.phase_theta

    # Truncated datagram → TruncatedLaneError (LANE-003).
    try:
        LaneFrame.deserialize(data[:20])
        raise AssertionError("expected TruncatedLaneError")
    except TruncatedLaneError:
        pass

    # Corrupted CRC → rejected.
    bad = bytearray(data); bad[-1] ^= 0xFF
    try:
        LaneFrame.deserialize(bytes(bad))
        raise AssertionError("expected CRC rejection")
    except TruncatedLaneError:
        pass
    print(f"✓ wire round-trip ({DATAGRAM_SIZE}B datagram, CRC enforced)")


def run_all_tests():
    print("=== Lane Framing Tests ===\n")
    test_tc_l1_exact_reassembly()
    test_tc_l2_out_of_order_arrival()
    test_tc_l3_missing_lane_expiry()
    test_frame_wire_roundtrip()
    print("\n=== All Lane Framing Tests Passed ===")


if __name__ == "__main__":
    run_all_tests()
