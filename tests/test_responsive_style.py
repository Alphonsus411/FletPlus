import builtins
import sys

import flet as ft
import pytest

from fletplus.styles import Style
import fletplus.utils.responsive_style as responsive_style_module


class DummyPage:
    def __init__(self, platform: str = "android"):
        self.platform = platform
        self.width = 500
        self.height = 800


def test_responsive_style_propagates_non_import_error(monkeypatch):
    """Se asegura que errores distintos de ImportError no se silencian."""
    # Guardar módulos originales para restaurar posteriormente
    utils_module = sys.modules.get("fletplus.utils")
    device_module = sys.modules.get("fletplus.utils.device")
    responsive_module = sys.modules.get("fletplus.utils.responsive_style")

    # Eliminar referencias para forzar una nueva importación
    if utils_module and hasattr(utils_module, "device"):
        delattr(utils_module, "device")
    sys.modules.pop("fletplus.utils.device", None)
    sys.modules.pop("fletplus.utils.responsive_style", None)

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

    # Restaurar entorno para otros tests
    monkeypatch.setattr(builtins, "__import__", original_import)
    if utils_module and device_module:
        setattr(utils_module, "device", device_module)
        sys.modules["fletplus.utils.device"] = device_module
    if responsive_module:
        sys.modules["fletplus.utils.responsive_style"] = responsive_module


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
