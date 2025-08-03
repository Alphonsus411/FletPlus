import builtins
import sys

import pytest


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
        if name == "fletplus.utils.device" or (name == "fletplus.utils" and "device" in fromlist):
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
