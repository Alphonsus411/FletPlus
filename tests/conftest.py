from __future__ import annotations

import sys
import types


def _ensure_state_stub() -> None:
    if "fletplus.state.state" in sys.modules:
        return

    module = types.ModuleType("fletplus.state.state")

    class _Dummy:
        def __init__(self, *args, **kwargs):  # noqa: ANN001, D401
            """Implementación mínima utilizada solo en tests."""

        def __call__(self, *args, **kwargs):  # noqa: ANN001
            return self

        def set(self, *args, **kwargs):  # noqa: ANN001
            return None

    module.Signal = _Dummy
    module.DerivedSignal = _Dummy
    module.Store = _Dummy
    sys.modules["fletplus.state.state"] = module


def _ensure_responsive_manager_stub() -> None:
    if "fletplus.utils.responsive_manager" in sys.modules:
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
    sys.modules["fletplus.utils.responsive_manager"] = module


_ensure_state_stub()
_ensure_responsive_manager_stub()
