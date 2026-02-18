"""Prueba mínima para validar versiones objetivo de Flet en CI."""

from __future__ import annotations

import os
from importlib import metadata

import flet as ft


ALLOWED_FLET_MINOR = {"0.27", "0.28"}


def _read_flet_version() -> str:
    version = getattr(ft, "__version__", "")
    if version:
        return version
    return metadata.version("flet")


def test_flet_version_in_supported_matrix() -> None:
    expected_minor = os.getenv("FLET_MATRIX_EXPECTED_MINOR")
    version = _read_flet_version()
    parts = version.split(".")
    current_minor = ".".join(parts[:2]) if len(parts) >= 2 else version

    if expected_minor:
        assert current_minor == expected_minor
    else:
        assert current_minor in ALLOWED_FLET_MINOR


def test_flet_matrix_sensitive_contracts_still_exist() -> None:
    assert hasattr(ft, "NavigationDrawer")
    assert hasattr(ft, "PageTransitionsTheme")
    assert hasattr(ft.Page, "window")
    assert hasattr(ft.Page, "update")

    update_async = getattr(ft.Page, "update_async", None)
    if update_async is not None:
        assert callable(update_async)
