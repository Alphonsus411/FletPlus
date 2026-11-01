from __future__ import annotations

import importlib
import sys
import warnings
from pathlib import Path

import flet as ft
import pytest

import fletplus
from fletplus import (
    FletPlusApp,
    RenderStrategy,
    enable_compat_patches,
)
from fletplus.core_legacy import FletPlusApp as LegacyFletPlusApp
from fletplus.core_legacy import FloatingMenuOptions as LegacyFloatingMenuOptions
from fletplus.core_legacy import (
    ResponsiveNavigationConfig as LegacyResponsiveNavigationConfig,
)
from fletplus_demo import main as demo_main
from fletplus_demo.app import create_app

pytestmark = pytest.mark.domain_legacy


class DummyPage:
    def __init__(self, platform: str = "web"):
        self.platform = platform
        self.title = ""
        self.controls = []
        self.theme = None
        self.theme_mode = None
        self.scroll = None
        self.horizontal_alignment = None
        self.updated = False
        self.update_calls = 0
        self.client_storage = None
        self.user = "Demo"
        self.locale = "es-ES"

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        self.updated = True
        self.update_calls += 1


def test_public_fletplus_app_alias_targets_legacy_contract():
    assert FletPlusApp is LegacyFletPlusApp


def test_public_responsive_navigation_options_alias_legacy_contract():
    from fletplus import FloatingMenuOptions, ResponsiveNavigationConfig

    assert FloatingMenuOptions is LegacyFloatingMenuOptions
    assert ResponsiveNavigationConfig is LegacyResponsiveNavigationConfig


def test_public_entrypoints_use_real_modules_without_stubs():
    sys.modules.pop("fletplus", None)
    module = importlib.import_module("fletplus")

    assert module.__name__ == "fletplus"
    assert Path(module.__file__).name == "__init__.py"
    assert module.FletPlusApp is LegacyFletPlusApp


def test_public_import_supports_demo_construction():
    page = DummyPage()
    enable_compat_patches(force=True)

    app = create_app(page)

    assert isinstance(app, FletPlusApp)
    assert isinstance(app.content_container.content, ft.Control)
    assert app.router.current_path in {"/", "/inicio"}
    app.dispose()


def test_demo_entrypoint_main_remains_compatible(monkeypatch):
    called = {"run": False}

    def fake_run(argv=None):
        called["run"] = True
        assert argv is None

    monkeypatch.setattr("fletplus_demo.run", fake_run)

    demo_main()

    assert called["run"] is True


def test_public_rendering_entrypoints_are_importable():
    from fletplus.rendering import WebRenderStrategy

    assert issubclass(WebRenderStrategy, RenderStrategy)


def _deprecation_messages(captured) -> list[str]:
    return [
        str(item.message)
        for item in captured
        if issubclass(item.category, DeprecationWarning)
    ]


@pytest.mark.parametrize(
    "alias", ["FloatingMenuOptions", "ResponsiveNavigationConfig"]
)
def test_legacy_facade_alias_emits_deprecation_warning(monkeypatch, alias):
    facade = sys.modules["fletplus"]
    legacy_module = importlib.import_module("fletplus.core_legacy")
    # La fachada cachea el alias en ``globals()``; se invalida para forzar la
    # resolución diferida y poder observar el aviso.
    monkeypatch.delitem(facade.__dict__, alias, raising=False)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", DeprecationWarning)
        value = getattr(facade, alias)

    assert value is getattr(legacy_module, alias)

    messages = _deprecation_messages(captured)
    assert len(messages) == 1, messages
    assert f"fletplus.{alias}" in messages[0]
    assert f"from fletplus.core_legacy import {alias}" in messages[0]


def test_official_fletplus_app_alias_does_not_warn(monkeypatch):
    facade = sys.modules["fletplus"]
    monkeypatch.delitem(facade.__dict__, "FletPlusApp", raising=False)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", DeprecationWarning)
        value = facade.FletPlusApp

    assert value is LegacyFletPlusApp
    assert _deprecation_messages(captured) == []


def test_recommended_legacy_imports_do_not_warn():
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", DeprecationWarning)
        from fletplus.core_legacy import (
            FloatingMenuOptions,
            ResponsiveNavigationConfig,
        )

    assert FloatingMenuOptions is LegacyFloatingMenuOptions
    assert ResponsiveNavigationConfig is LegacyResponsiveNavigationConfig
    assert _deprecation_messages(captured) == []
