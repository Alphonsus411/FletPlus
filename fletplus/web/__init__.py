"""Funciones utilitarias para habilitar PWA en FletPlus."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

LAZY_IMPORTS = {
    "generate_manifest": "fletplus.web.pwa",
    "generate_service_worker": "fletplus.web.pwa",
    "register_pwa": "fletplus.web.pwa",
}

if TYPE_CHECKING:
    from fletplus.web.pwa import (
        generate_manifest,
        generate_service_worker,
        register_pwa,
    )

__all__ = [
    "generate_manifest",
    "generate_service_worker",
    "register_pwa",
]


def __getattr__(name: str) -> Any:
    if name in LAZY_IMPORTS:
        module = importlib.import_module(LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    return sorted(set(__all__))
