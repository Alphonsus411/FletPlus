"""Benchmarks ligeros para listeners gestionados por AnimationController."""
from __future__ import annotations

import time
from typing import Iterable

import pytest

from fletplus.animation import AnimationController


def _available_backends() -> Iterable[str]:
    backends = ["python"]
    try:
        from fletplus.animation.listeners_rs import ListenerContainer  # type: ignore
    except Exception:
        ListenerContainer = None
    if ListenerContainer is not None:
        backends.append("rust")
    return backends


def _run_benchmark(backend: str) -> tuple[float, int]:
    controller = AnimationController(backend=backend)
    hits = {"count": 0}

    def make_listener() -> callable:
        def _cb(name: str) -> None:
            hits["count"] += 1

        return _cb

    subscriptions = [controller.add_listener("tick", make_listener()) for _ in range(100)]
    start = time.perf_counter()
    for _ in range(10_000):
        controller.trigger("tick")
    elapsed = time.perf_counter() - start
    for unsub in subscriptions:
        unsub()
    return elapsed, hits["count"]


@pytest.mark.perf
@pytest.mark.parametrize("backend", _available_backends())
def test_animation_listener_benchmarks(backend: str, capsys: pytest.CaptureFixture[str]) -> None:
    python_elapsed, python_hits = _run_benchmark("python")
    metrics: dict[str, float | int] = {
        "python_seconds": python_elapsed,
        "python_hits": python_hits,
    }

    if backend == "rust":
        rust_elapsed, rust_hits = _run_benchmark("rust")
        metrics.update({"rust_seconds": rust_elapsed, "rust_hits": rust_hits})
        assert rust_hits == python_hits

    print(f"Animation listeners benchmark: {metrics}")
    captured = capsys.readouterr().out
    assert "Animation listeners benchmark" in captured
    assert metrics["python_hits"] == 1_000_000
    assert metrics["python_seconds"] > 0
    if "rust_seconds" in metrics:
        assert metrics["rust_seconds"] > 0
