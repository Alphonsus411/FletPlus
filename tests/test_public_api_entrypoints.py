from __future__ import annotations

import importlib
import sys
from pathlib import Path

import flet as ft

from fletplus import FletPlusApp
from fletplus.core_legacy import FletPlusApp as LegacyFletPlusApp
from fletplus_demo import main as demo_main
from fletplus_demo.app import create_app


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


def test_public_entrypoints_use_real_modules_without_stubs():
    sys.modules.pop("fletplus", None)
    module = importlib.import_module("fletplus")

    assert module.__name__ == "fletplus"
    assert Path(module.__file__).name == "__init__.py"
    assert module.FletPlusApp is LegacyFletPlusApp


def test_public_import_supports_demo_construction():
    page = DummyPage()

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
