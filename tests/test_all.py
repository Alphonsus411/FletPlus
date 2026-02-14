"""Meta-pruebas ligeras para contrato público e importabilidad.

Este módulo **no** ejecuta funciones ``test_*`` de otros archivos.
Cuando se requiere una suite agregada, debe resolverse con selección de rutas
(``pytest tests/test_a.py tests/test_b.py ...``) o markers en ``pytest.ini``.
"""

from __future__ import annotations

from importlib import import_module

import pytest


@pytest.mark.aggregate_contract
def test_public_state_imports() -> None:
    from fletplus import State as PublicState
    from fletplus.core import AppState, State as CoreState

    assert PublicState is AppState
    assert CoreState is AppState


@pytest.mark.aggregate_contract
@pytest.mark.parametrize(
    "module_name",
    [
        "tests.test_smart_table",
        "tests.test_sidebar_admin",
        "tests.test_responsive_grid",
        "tests.test_theme_manager",
        "tests.test_fletplus_app",
    ],
)
def test_core_component_test_modules_are_importable(module_name: str) -> None:
    module = import_module(module_name)
    assert module is not None


@pytest.mark.aggregate_contract
def test_public_component_entrypoints() -> None:
    from fletplus import (
        FletPlusApp,
        ResponsiveGrid,
        SidebarAdmin,
        SmartTable,
        ThemeManager,
    )
    from fletplus.components.responsive_grid import ResponsiveGrid as DirectResponsiveGrid
    from fletplus.components.sidebar_admin import SidebarAdmin as DirectSidebarAdmin
    from fletplus.components.smart_table import SmartTable as DirectSmartTable
    from fletplus.core_legacy import FletPlusApp as DirectFletPlusApp
    from fletplus.themes.theme_manager import ThemeManager as DirectThemeManager

    assert SmartTable is DirectSmartTable
    assert SidebarAdmin is DirectSidebarAdmin
    assert ResponsiveGrid is DirectResponsiveGrid
    assert ThemeManager is DirectThemeManager
    assert FletPlusApp is DirectFletPlusApp
