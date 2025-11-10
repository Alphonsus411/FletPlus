"""Ejecutor agregado para lanzar varias pruebas unitarias a la vez.

La importación ``from tests...`` funciona correctamente cuando ``pytest``
descubre el paquete porque añade la raíz del proyecto al ``sys.path``.
Sin embargo, ejecutar el módulo directamente con ``python tests/test_all.py``
fallaba con ``ModuleNotFoundError`` al no resolverse el paquete ``tests``.

Para mantener la compatibilidad con ambos escenarios utilizamos
``importlib`` y, en caso de no estar empacado, añadimos la raíz del
repositorio al ``sys.path`` antes de cargar los módulos necesarios.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys
from typing import Protocol, cast


class _SmartTableModule(Protocol):
    def test_smart_table_builds_with_filters_and_multi_sort(self) -> None: ...

    def test_inline_editing_with_validation_and_callback(self) -> None: ...

    def test_toggle_sort_cycle_removes_sort(self) -> None: ...

    def test_set_filter_requires_filterable_column(self) -> None: ...

    def test_virtualized_async_provider_and_manual_refresh(self) -> None: ...


class _SidebarAdminModule(Protocol):
    def test_sidebar_admin_build_and_selection(self) -> None: ...


class _ResponsiveGridModule(Protocol):
    def test_responsive_grid_builds_correctly(self) -> None: ...


class _ThemeManagerModule(Protocol):
    def test_theme_manager_initialization_and_toggle(self) -> None: ...


class _FletPlusAppModule(Protocol):
    def test_fletplus_app_initialization_and_routing(self) -> None: ...


def _module_prefix() -> str:
    """Devuelve el prefijo apropiado para importar submódulos de pruebas."""

    if __package__:
        return f"{__package__}."

    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return "tests."


def _load_tests() -> tuple[
    _SmartTableModule,
    _SidebarAdminModule,
    _ResponsiveGridModule,
    _ThemeManagerModule,
    _FletPlusAppModule,
]:
    prefix = _module_prefix()
    return (
        cast(_SmartTableModule, import_module(f"{prefix}test_smart_table")),
        cast(_SidebarAdminModule, import_module(f"{prefix}test_sidebar_admin")),
        cast(
            _ResponsiveGridModule, import_module(f"{prefix}test_responsive_grid")
        ),
        cast(_ThemeManagerModule, import_module(f"{prefix}test_theme_manager")),
        cast(_FletPlusAppModule, import_module(f"{prefix}test_fletplus_app")),
    )


(
    test_smart_table_module,
    test_sidebar_admin_module,
    test_responsive_grid_module,
    test_theme_manager_module,
    test_fletplus_app_module,
) = _load_tests()


def test_all_components() -> None:
    test_smart_table_module.test_smart_table_builds_with_filters_and_multi_sort()
    test_smart_table_module.test_inline_editing_with_validation_and_callback()
    test_smart_table_module.test_toggle_sort_cycle_removes_sort()
    test_smart_table_module.test_set_filter_requires_filterable_column()
    test_smart_table_module.test_virtualized_async_provider_and_manual_refresh()
    test_sidebar_admin_module.test_sidebar_admin_build_and_selection()
    test_responsive_grid_module.test_responsive_grid_builds_correctly()
    test_theme_manager_module.test_theme_manager_initialization_and_toggle()
    test_fletplus_app_module.test_fletplus_app_initialization_and_routing()
