from __future__ import annotations

import sys
import types

import pytest


@pytest.fixture(autouse=True)
def state_stub(monkeypatch):
    if "fletplus.state.state" in sys.modules:
        yield
        return

    module = types.ModuleType("fletplus.state.state")
    class _Dummy:
        def __init__(self, *args, **kwargs):  # noqa: ANN001, D401
            """Implementación mínima utilizada solo en tests."""
            self._value = args[0] if args else None

        def __call__(self, *args, **kwargs):  # noqa: ANN001
            return self.get()

        def set(self, *args, **kwargs):  # noqa: ANN001
            if args:
                self._value = args[0]
            return self._value

        def get(self, *args, **kwargs):  # noqa: ANN001
            return self._value

        def subscribe(self, *args, **kwargs):  # noqa: ANN001
            def _unsubscribe():
                return None

            return _unsubscribe

    module.Signal = _Dummy
    module.DerivedSignal = _Dummy
    module.Store = _Dummy
    monkeypatch.setitem(sys.modules, "fletplus.state.state", module)
    yield


@pytest.fixture(autouse=True)
def responsive_manager_stub(monkeypatch):
    if "fletplus.utils.responsive_manager" in sys.modules:
        yield
        return

    module = types.ModuleType("fletplus.utils.responsive_manager")

    class ResponsiveManager:  # noqa: D401
        """Implementación mínima utilizada solo en tests."""

        def __init__(self, *args, callbacks=None, orientation_callbacks=None, **kwargs):  # noqa: ANN001
            self._listeners = []
            self.callbacks = callbacks or {}
            self.orientation_callbacks = orientation_callbacks or {}

        def register(self, *args, **kwargs):  # noqa: ANN001
            return None

        def unregister(self, *args, **kwargs):  # noqa: ANN001
            return None

        def update(self, *args, **kwargs):  # noqa: ANN001
            return None

        def register_styles(self, *args, **kwargs):  # noqa: ANN001
            return None

    module.ResponsiveManager = ResponsiveManager
    monkeypatch.setitem(sys.modules, "fletplus.utils.responsive_manager", module)
    yield


@pytest.fixture
def watchdog_stub(monkeypatch):
    watchdog_module = types.ModuleType("watchdog")
    events_module = types.ModuleType("watchdog.events")
    events_module.FileSystemEvent = object
    events_module.FileSystemEventHandler = object
    observers_module = types.ModuleType("watchdog.observers")
    observers_module.Observer = object
    monkeypatch.setitem(sys.modules, "watchdog", watchdog_module)
    monkeypatch.setitem(sys.modules, "watchdog.events", events_module)
    monkeypatch.setitem(sys.modules, "watchdog.observers", observers_module)
    return watchdog_module
