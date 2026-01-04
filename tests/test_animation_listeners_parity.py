from __future__ import annotations

import gc

import pytest

from fletplus.animation.controller import _PythonListenerContainer, _RustListenerContainer

try:
    from fletplus.animation.listeners_pr_rs import ListenerContainer as _NativeListener  # type: ignore
except Exception:  # pragma: no cover - backend opcional
    _NativeListener = None


def _record(label: str, sink: list[tuple[str, str]]):
    def _cb(name: str) -> None:
        sink.append((label, name))

    return _cb


@pytest.fixture()
def containers() -> tuple[_PythonListenerContainer, _RustListenerContainer]:  # type: ignore[type-arg]
    if _NativeListener is None:
        pytest.skip("Extensión listeners_pr_rs no disponible en el entorno actual")

    return _PythonListenerContainer(), _RustListenerContainer(_NativeListener)


def test_replay_and_order_match(containers: tuple[_PythonListenerContainer, _RustListenerContainer]) -> None:  # type: ignore[type-arg]
    python_container, rust_container = containers
    events_py: list[tuple[str, str]] = []
    events_rs: list[tuple[str, str]] = []

    python_container.trigger("boot")
    rust_container.trigger("boot")

    python_container.add_listener("boot", _record("late", events_py), replay_if_fired=True)
    rust_container.add_listener("boot", _record("late", events_rs), replay_if_fired=True)

    python_container.add_listener("boot", _record("first", events_py))
    rust_container.add_listener("boot", _record("first", events_rs))

    python_container.trigger("boot")
    rust_container.trigger("boot")

    assert events_py == events_rs == [("late", "boot"), ("late", "boot"), ("first", "boot")]
    assert python_container.fired() == rust_container.fired()


def test_cleanup_drops_dead_callbacks(containers: tuple[_PythonListenerContainer, _RustListenerContainer]) -> None:  # type: ignore[type-arg]
    python_container, rust_container = containers
    events_py: list[tuple[str, str]] = []
    events_rs: list[tuple[str, str]] = []

    class Handler:
        def __init__(self, label: str, sink: list[tuple[str, str]]) -> None:
            self.label = label
            self.sink = sink

        def __call__(self, name: str) -> None:  # pragma: no cover - llamado desde Rust
            self.sink.append((self.label, name))

    alive_py = Handler("alive", events_py)
    alive_rs = Handler("alive", events_rs)

    python_container.add_listener("tick", alive_py)
    rust_container.add_listener("tick", alive_rs)

    temporary_py = Handler("temporary", events_py)
    temporary_rs = Handler("temporary", events_rs)

    python_container.add_listener("tick", temporary_py)
    rust_container.add_listener("tick", temporary_rs)

    python_container.trigger("tick")
    rust_container.trigger("tick")

    assert events_py == events_rs == [("alive", "tick"), ("temporary", "tick")]

    del temporary_py, temporary_rs
    gc.collect()

    events_py.clear()
    events_rs.clear()

    python_container.trigger("tick")
    rust_container.trigger("tick")

    assert events_py == events_rs == [("alive", "tick")]


def test_trigger_many_tracks_state(containers: tuple[_PythonListenerContainer, _RustListenerContainer]) -> None:  # type: ignore[type-arg]
    python_container, rust_container = containers
    events_py: list[tuple[str, str]] = []
    events_rs: list[tuple[str, str]] = []

    python_container.add_listener("alpha", _record("a1", events_py))
    rust_container.add_listener("alpha", _record("a1", events_rs))
    python_container.add_listener("beta", _record("b1", events_py))
    rust_container.add_listener("beta", _record("b1", events_rs))

    python_container.trigger_many(["alpha", "beta", "alpha"])
    rust_container.trigger_many(["alpha", "beta", "alpha"])

    assert events_py == events_rs == [
        ("a1", "alpha"),
        ("b1", "beta"),
        ("a1", "alpha"),
    ]
    assert python_container.fired() == rust_container.fired()
