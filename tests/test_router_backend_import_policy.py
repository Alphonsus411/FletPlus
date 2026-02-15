from __future__ import annotations

import importlib
import sys

import pytest


ROUTER_MODULE = "fletplus.router.router"
BACKEND_MODULES = {
    "fletplus.router.router_pr",
    "fletplus.router.router_rs",
    "fletplus.router.router_cy",
}


def _drop_router_modules() -> None:
    for module_name in [ROUTER_MODULE, *BACKEND_MODULES]:
        sys.modules.pop(module_name, None)


def test_router_import_fallback_when_native_modules_are_missing(monkeypatch):
    original_import_module = importlib.import_module

    def fake_import_module(name, package=None):
        if package == "fletplus.router" and name in {".router_pr", ".router_rs", ".router_cy"}:
            raise ModuleNotFoundError(f"No module named '{name}'")
        return original_import_module(name, package)

    _drop_router_modules()
    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    with pytest.warns(RuntimeWarning, match="Backends nativos del router no disponibles"):
        router_mod = importlib.import_module(ROUTER_MODULE)

    assert router_mod._router_pr is None
    assert router_mod._router_rs is None
    assert router_mod._router_cy is None

    _drop_router_modules()


def test_router_import_raises_on_unexpected_backend_error(monkeypatch):
    original_import_module = importlib.import_module

    def fake_import_module(name, package=None):
        if package == "fletplus.router" and name == ".router_pr":
            raise RuntimeError("unexpected backend crash")
        return original_import_module(name, package)

    _drop_router_modules()
    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    with pytest.raises(RuntimeError, match="unexpected backend crash"):
        importlib.import_module(ROUTER_MODULE)

    _drop_router_modules()
