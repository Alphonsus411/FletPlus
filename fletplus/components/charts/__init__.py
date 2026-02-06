"""Componentes de gráficos para FletPlus."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

LAZY_IMPORTS = {
    "LineChart": "fletplus.components.charts.line_chart",
}

if TYPE_CHECKING:
    from fletplus.components.charts.line_chart import LineChart

__all__ = ["LineChart"]


def __getattr__(name: str) -> Any:
    if name in LAZY_IMPORTS:
        module = importlib.import_module(LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    return sorted(set(__all__))
