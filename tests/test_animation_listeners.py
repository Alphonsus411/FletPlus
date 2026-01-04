from __future__ import annotations

import gc
from typing import Iterable

import pytest

from fletplus.animation import AnimationController


def _available_backends() -> Iterable[str]:
    backends = ["python"]
    try:
        from fletplus.animation.listeners_pr_rs import ListenerContainer  # type: ignore
    except Exception:
        try:
            from fletplus.animation.listeners_rs import ListenerContainer  # type: ignore
        except Exception:
            ListenerContainer = None
    else:
        # Pyright inference workaround
        ListenerContainer = ListenerContainer
    if ListenerContainer is not None:
        backends.append("rust")
    return backends


@pytest.mark.parametrize("backend", _available_backends())
def test_listener_unsubscribes_and_drops(backend: str) -> None:
    controller = AnimationController(backend=backend)
    events: list[tuple[str, str]] = []

    class Handler:
        def __init__(self, label: str) -> None:
            self.label = label

        def __call__(self, name: str) -> None:
            events.append((self.label, name))

    handler = Handler("primary")
    unsubscribe = controller.add_listener("demo", handler)

    controller.trigger("demo")
    unsubscribe()

    controller.trigger("demo")
    del handler
    gc.collect()
    controller.trigger("demo")

    assert events == [("primary", "demo")]


@pytest.mark.parametrize("backend", _available_backends())
def test_trigger_many_tracks_fired_and_cleanups(backend: str) -> None:
    controller = AnimationController(backend=backend)
    replay_hits: list[str] = []

    def listener(name: str) -> None:
        replay_hits.append(name)

    controller.trigger_many(["alpha", "beta", "gamma"])
    controller.add_listener("beta", listener, replay_if_fired=True)
    controller.remove_listener("beta", listener)
    controller.trigger_many(["alpha", "beta"])

    assert set(replay_hits) == {"beta"}
    assert controller.has_fired("gamma")
    assert controller.has_fired("alpha")
    assert controller.has_fired("beta")
