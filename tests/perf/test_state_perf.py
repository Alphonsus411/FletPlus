"""Benchmarks ligeros para señales y snapshots con backend nativo."""
from __future__ import annotations

import time
from typing import Iterable

import pytest

from fletplus.state import Signal


def _available_backends() -> Iterable[str]:
    backends = ["python"]
    try:
        from fletplus.state.signal_pr_rs import SignalState, notify, snapshot  # type: ignore
    except Exception:
        SignalState = None
        notify = None
        snapshot = None
    if SignalState is not None and notify is not None and snapshot is not None:
        backends.append("rust")
    return backends


def _python_notify(subscribers: dict[int, callable], value: object) -> None:
    for callback in list(subscribers.values()):
        callback(value)


def _python_snapshot(signals: dict[str, Signal]) -> dict[str, object]:
    return {name: signal.get() for name, signal in signals.items()}


def _run_notify_benchmark(backend: str) -> tuple[float, int]:
    hits = {"count": 0}

    def make_callback() -> callable:
        def _cb(value: object) -> None:
            hits["count"] += 1

        return _cb

    total_callbacks = 100
    iterations = 10_000
    if backend == "python":
        subscribers = {token: make_callback() for token in range(total_callbacks)}
        start = time.perf_counter()
        for _ in range(iterations):
            _python_notify(subscribers, 123)
        elapsed = time.perf_counter() - start
        return elapsed, hits["count"]

    from fletplus.state.signal_pr_rs import SignalState, notify  # type: ignore

    state = SignalState()
    for token in range(total_callbacks):
        state.add(token, make_callback())
    start = time.perf_counter()
    for _ in range(iterations):
        notify(state, 123)
    elapsed = time.perf_counter() - start
    return elapsed, hits["count"]


def _run_snapshot_benchmark(backend: str) -> tuple[float, dict[str, object]]:
    signals = {f"key_{idx}": Signal(idx) for idx in range(200)}
    iterations = 5_000
    if backend == "python":
        snapshot = _python_snapshot(signals)
        start = time.perf_counter()
        for _ in range(iterations):
            snapshot = _python_snapshot(signals)
        elapsed = time.perf_counter() - start
        return elapsed, snapshot

    from fletplus.state.signal_pr_rs import snapshot  # type: ignore

    snapshot_value = snapshot(signals)
    start = time.perf_counter()
    for _ in range(iterations):
        snapshot_value = snapshot(signals)
    elapsed = time.perf_counter() - start
    return elapsed, snapshot_value


@pytest.mark.perf
@pytest.mark.parametrize("backend", _available_backends())
def test_signal_native_benchmarks(backend: str, capsys: pytest.CaptureFixture[str]) -> None:
    python_notify_elapsed, python_notify_hits = _run_notify_benchmark("python")
    python_snapshot_elapsed, python_snapshot = _run_snapshot_benchmark("python")
    metrics: dict[str, float | int] = {
        "python_notify_seconds": python_notify_elapsed,
        "python_notify_hits": python_notify_hits,
        "python_snapshot_seconds": python_snapshot_elapsed,
    }

    if backend == "rust":
        rust_notify_elapsed, rust_notify_hits = _run_notify_benchmark("rust")
        rust_snapshot_elapsed, rust_snapshot = _run_snapshot_benchmark("rust")
        metrics.update(
            {
                "rust_notify_seconds": rust_notify_elapsed,
                "rust_notify_hits": rust_notify_hits,
                "rust_snapshot_seconds": rust_snapshot_elapsed,
            }
        )
        assert rust_notify_hits == python_notify_hits
        assert rust_snapshot == python_snapshot

    print(f"Signal benchmarks: {metrics}")
    captured = capsys.readouterr().out
    assert "Signal benchmarks" in captured
    assert metrics["python_notify_hits"] == 1_000_000
    assert metrics["python_notify_seconds"] > 0
    assert metrics["python_snapshot_seconds"] > 0
    if "rust_notify_seconds" in metrics:
        assert metrics["rust_notify_seconds"] > 0
    if "rust_snapshot_seconds" in metrics:
        assert metrics["rust_snapshot_seconds"] > 0
