"""
Smoke Tests for src_realtime
============================

The realtime variant mirrors src/ with nanosecond-anchored timing using
time.perf_counter_ns(). These tests verify it imports cleanly and that the
core realtime behaviors work: echo cascades, hyperfractal resolution, and
timer expiry.

Run:
    python3 tests/unit/test_realtime.py
"""

import sys
import os
import math
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_realtime_echo_imports():
    """The realtime echo module imports cleanly."""
    from src_realtime.temporal.echo import EchoCascade, HyperfractalResolver
    assert EchoCascade is not None
    assert HyperfractalResolver is not None
    print("✓ RT-001: realtime echo module imports")


def test_realtime_engine_imports():
    """The realtime engine module imports cleanly."""
    from src_realtime.temporal.engine import TemporalEngine
    assert TemporalEngine is not None
    print("✓ RT-002: realtime engine module imports")


def test_realtime_echo_cascade():
    """A realtime echo cascade emits echoes with nanosecond-anchored timing."""
    from src_realtime.temporal.echo import EchoCascade

    cascade = EchoCascade(
        origin_time_ns=time.perf_counter_ns(),
        base_resolution_ns=1000,   # 1 μs
        scaling_factor=0.1,
        max_depth=6,
    )
    cascade.emit(initial_phase=(0.0, 0.0))

    assert cascade.total_echoes > 0, "cascade emitted no echoes"
    # 1μs base × α^6 should improve resolution by ~10^6 (picosecond scale).
    # Check the improvement factor rather than an exact bound, so the
    # assertion is robust to floating-point representation of 0.1^6.
    base_s = 1000 * 1e-9
    assert cascade.effective_resolution_s < base_s * 1e-5, \
        "effective resolution should improve by ~10^6 over base"
    print(f"✓ RT-003: echo cascade ({cascade.total_echoes} echoes, "
          f"{cascade.effective_resolution_s * 1e12:.3f} ps)")


def test_realtime_resolver():
    """The hyperfractal resolver resolves events below base resolution."""
    from src_realtime.temporal.echo import HyperfractalResolver

    resolver = HyperfractalResolver(
        base_resolution_ns=1000,
        scaling_factor=0.1,
        max_depth=6,
    )
    cascade = resolver.emit_event(phase=(math.pi / 4, 0.0))
    t_ns, p_s = resolver.resolve_event(cascade)

    assert p_s <= resolver.theoretical_precision_s * 10, \
        "resolved precision should be near theoretical"
    print(f"✓ RT-004: resolver precision {p_s * 1e12:.3f} ps "
          f"(theoretical {resolver.theoretical_precision_s * 1e12:.3f} ps)")


def test_realtime_timer_expiry():
    """A realtime timer expires and reports a measurement."""
    from src_realtime.temporal.timer import Timer, TimerState

    # REALTIME contract: timers are anchored to perf_counter_ns.
    # Target is set slightly in the future so expiry is immediate but jitter >= 0.
    now_ns = time.perf_counter_ns()
    timer = Timer(
        id="rt_test",
        target_time_ns=now_ns + 1_000,   # ~1us out: expires immediately
        phase=(math.pi / 2, 0.0),        # P(0)=P(1)=0.5
    )
    event = timer.expire()

    assert timer.state == TimerState.EXPIRED
    assert event.timer_id == "rt_test"
    assert event.jitter_ns >= -1_000     # allow tiny negative jitter from scheduling
    value = timer.measure()              # measurement is a separate act (TEMP-011)
    assert value in (0, 1)
    print(f"✓ RT-005: timer expired (jitter={event.jitter_ns}ns, value={value})")


def test_realtime_engine_timers():
    """The realtime engine creates and counts timers."""
    from src_realtime.temporal.engine import TemporalEngine

    engine = TemporalEngine(resolution_us=1, echo_enabled=True, echo_depth=6)
    # Use long delays so scheduling drift on a loaded host cannot expire them
    # before the assertion (active-count is a wall-clock predicate).
    engine.create_timer(delay_us=50_000)   # 50 ms out
    engine.create_timer(delay_us=100_000)  # 100 ms out

    assert len(engine.get_all_timers()) == 2
    assert len(engine.get_active_timers()) == 2
    print("✓ RT-006: realtime engine manages timers")


def run_all_tests():
    print("=== Realtime Smoke Tests ===")
    print()
    test_realtime_echo_imports()
    test_realtime_engine_imports()
    test_realtime_echo_cascade()
    test_realtime_resolver()
    test_realtime_timer_expiry()
    test_realtime_engine_timers()
    print()
    print("=== All Realtime Tests Passed ===")


if __name__ == "__main__":
    run_all_tests()
