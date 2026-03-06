"""Tests para activación explícita de parches legacy de compatibilidad."""

from __future__ import annotations

import importlib

import flet as ft


class _LegacyTextButton:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class _LegacyIcon:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class _ModernTextButton:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def test_import_fletplus_no_aplica_side_effects_globales(monkeypatch):
    monkeypatch.setattr(ft, "TextButton", _LegacyTextButton)
    monkeypatch.setattr(ft, "_fletplus_patched_controls", False, raising=False)

    module = importlib.import_module("fletplus")
    importlib.reload(module)

    button = ft.TextButton(text="Sin parche", color="blue")
    assert button.kwargs == {"text": "Sin parche", "color": "blue"}
    assert getattr(ft, "_fletplus_patched_controls", False) is False


def test_enable_compat_patches_aplica_parches_legacy(monkeypatch):
    monkeypatch.setattr(ft, "TextButton", _LegacyTextButton)
    monkeypatch.setattr(ft, "Icon", _LegacyIcon)
    monkeypatch.setattr(ft, "_fletplus_patched_controls", False, raising=False)

    module = importlib.import_module("fletplus")
    importlib.reload(module)
    enabled = module.enable_compat_patches(force=True)

    legacy_button = ft.TextButton(text="Legacy", color="red")
    legacy_icon = ft.Icon(icon="settings", color="red")

    assert enabled is True
    assert legacy_button.kwargs == {"content": "Legacy", "color": "red"}
    assert legacy_icon.args == ("settings",)


def test_enable_compat_patches_respeta_bandera_de_entorno(monkeypatch):
    monkeypatch.setenv("FLETPLUS_ENABLE_LEGACY_PATCHES", "0")
    monkeypatch.setattr(ft, "TextButton", _LegacyTextButton)
    monkeypatch.setattr(ft, "_fletplus_patched_controls", False, raising=False)

    module = importlib.import_module("fletplus")
    importlib.reload(module)

    assert module.enable_compat_patches() is False




def test_enable_compat_patches_se_activa_por_entorno(monkeypatch):
    monkeypatch.setenv("FLETPLUS_ENABLE_LEGACY_PATCHES", "1")
    monkeypatch.setattr(ft, "TextButton", _LegacyTextButton)
    monkeypatch.setattr(ft, "_fletplus_patched_controls", False, raising=False)

    module = importlib.import_module("fletplus")
    importlib.reload(module)

    assert module.enable_compat_patches() is True
    patched = ft.TextButton(text="Legacy")
    assert patched.kwargs == {"content": "Legacy"}

def test_compat_patch_no_rompe_api_moderna(monkeypatch):
    monkeypatch.setattr(ft, "TextButton", _ModernTextButton)
    monkeypatch.setattr(ft, "_fletplus_patched_controls", False, raising=False)

    module = importlib.import_module("fletplus")
    importlib.reload(module)
    module.enable_compat_patches(force=True)

    button = ft.TextButton(content="Contenido moderno", style="outlined")
    assert button.kwargs == {"content": "Contenido moderno", "style": "outlined"}


def test_enable_compat_patches_registra_warning_si_falla_un_parche(monkeypatch, caplog):
    monkeypatch.setattr(ft, "_fletplus_patched_controls", False, raising=False)

    module = importlib.import_module("fletplus.utils.flet_compat_patch")
    importlib.reload(module)

    def _boom() -> None:
        raise TypeError("patch failed")

    monkeypatch.setattr(module, "_patch_page_size_aliases", _boom)
    caplog.set_level("WARNING")

    assert module.enable_compat_patches(force=True) is True
    assert any("Fallo en parche legacy _patch_page_size_aliases" in r.message for r in caplog.records)
