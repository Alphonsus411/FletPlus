import builtins
import sys

import flet as ft
import pytest

import fletplus.utils.responsive_style as responsive_style_module
from fletplus.styles import Style


class DummyPage:
    def __init__(self, platform: str = "android"):
        self.platform = platform
        self.width = 500
        self.height = 800


def test_responsive_style_propagates_non_import_error(monkeypatch):
    """Se asegura que errores distintos de ImportError no se silencian."""
    utils_module = sys.modules.get("fletplus.utils")

    # Eliminar referencias para forzar una nueva importación
    if utils_module:
        monkeypatch.delattr(utils_module, "device", raising=False)
    monkeypatch.delitem(sys.modules, "fletplus.utils.device", raising=False)
    monkeypatch.delitem(sys.modules, "fletplus.utils.responsive_style", raising=False)

    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if (
            name == "fletplus.utils.device"
            or (name == "fletplus.utils" and "device" in fromlist)
            or (name == "" and "device" in fromlist and level > 0)
        ):
            raise ValueError("boom")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ValueError):
        __import__("fletplus.utils.responsive_style")


def test_responsive_style_device_fallback(monkeypatch):
    """Cuando el módulo de dispositivo no está disponible se usa el fallback local."""
    monkeypatch.setattr(responsive_style_module, "_device_module", None, raising=False)

    rs = responsive_style_module.ResponsiveStyle(
        device={"mobile": Style(text_style=ft.TextStyle(size=33))}
    )

    style = rs.get_style(DummyPage())

    assert style is not None
    assert style.text_style.size == 33


def test_responsive_style_accepts_symbolic_width_breakpoints():
    rs = responsive_style_module.ResponsiveStyle(width={"md": Style(padding=10)})
    page = DummyPage()
    page.width = 900

    style = rs.get_style(page)

    assert style is not None
    assert style.padding == 10


def test_responsive_style_merge_respects_declared_none_fields():
    rs = responsive_style_module.ResponsiveStyle()
    base = Style(padding=10, bgcolor="red")
    override = Style(padding=None)

    merged = rs._merge(base, override)

    assert merged is not None
    assert merged.padding is None
    assert merged.bgcolor == "red"
