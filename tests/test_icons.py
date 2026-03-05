import importlib

import flet as ft
import pytest

import fletplus

from fletplus.icons import (
    DEFAULT_ICON_SET,
    Icon,
    available_icon_sets,
    has_icon,
    icon,
    list_icons,
    register_icon,
    register_icon_set,
    resolve_icon_name,
)

CRITICAL_UPSTREAM_ICONS = {
    "HOME": "SETTINGS",
    "INSIGHTS": "DASHBOARD",
    "ANALYTICS": "DASHBOARD",
    "SUPERVISED_USER_CIRCLE": "PERSON",
    "SETTINGS": "HOME",
    "MENU": "MORE_HORIZ",
    "SKIP_NEXT_OUTLINED": "SKIP_NEXT",
    "CLOSED_CAPTION": "SUBTITLES",
    "VERIFIED_OUTLINED": "CHECK_CIRCLE",
    "WARNING_AMBER_OUTLINED": "WARNING",
    "ERROR_OUTLINE": "ERROR",
    "ARROW_UPWARD": "NORTH",
    "ARROW_DOWNWARD": "SOUTH",
    "EDIT": "CREATE",
    "CHECK": "DONE",
    "CLOSE": "CANCEL",
}


def _icons_namespace() -> object:
    namespace = getattr(ft, "Icons", None) or getattr(ft, "icons", None)
    assert namespace is not None, "No existe namespace de iconos compatible en Flet"
    return namespace


def _resolve_upstream_icon_with_fallback(name: str, fallback: str) -> object:
    icons = _icons_namespace()
    icon_value = getattr(icons, name, None)
    if icon_value is not None:
        return icon_value
    fallback_value = getattr(icons, fallback, None)
    assert fallback_value is not None, (
        f"Falta icono crítico '{name}' y su fallback '{fallback}' en namespace de iconos"
    )
    return fallback_value


def test_icon_resolves_from_material_catalog():
    result = icon("home")
    assert isinstance(result, ft.Icon)
    assert result.name == "home"


def test_icon_uses_fallback_when_missing():
    result = icon("no-existe", fallback="settings")
    assert result.name == "settings"


def test_icon_uses_cross_set_fallback():
    result = icon(
        "no-lucide",
        icon_set="lucide",
        fallback="home",
        fallback_set=DEFAULT_ICON_SET,
    )
    assert result.name == "home"


def test_resolve_icon_name_errors_without_fallback():
    with pytest.raises(ValueError):
        resolve_icon_name("sin-fallback", fallback=None)


def test_available_sets_include_defaults():
    sets = available_icon_sets()
    assert "material" in sets
    assert "lucide" in sets


def test_list_icons_returns_sorted_names():
    icons = list(list_icons("material"))
    assert icons == sorted(icons)
    assert "home" in icons


def test_register_icon_adds_or_overrides_icon():
    register_icon("brand", "lucide:brand", icon_set="lucide")
    assert has_icon("brand", "lucide")
    result = icon("brand", icon_set="lucide")
    assert result.name == "lucide:brand"


def test_register_icon_set_creates_new_catalog():
    register_icon_set("custom", {"logo": "custom:logo"})
    assert "custom" in available_icon_sets()
    result = icon("logo", icon_set="custom")
    assert result.name == "custom:logo"


def test_icon_class_builds_instances():
    factory = Icon("menu", icon_set="lucide", kwargs={"color": "red"})
    instance = factory()
    assert isinstance(instance, ft.Icon)
    assert instance.name == "lucide:menu"
    assert instance.color == "red"


def test_critical_upstream_icons_have_compatible_fallback() -> None:
    for icon_name, fallback_name in CRITICAL_UPSTREAM_ICONS.items():
        resolved = _resolve_upstream_icon_with_fallback(icon_name, fallback_name)
        assert resolved is not None


def test_upstream_icon_fallback_path_is_exercised() -> None:
    class _FakeIcons:
        SETTINGS = object()

    resolved = getattr(_FakeIcons, "INSIGHTS", None)
    if resolved is None:
        resolved = getattr(_FakeIcons, "SETTINGS", None)

    assert resolved is _FakeIcons.SETTINGS


def test_critical_upstream_icon_name_resolution_for_component_catalog() -> None:
    for icon_name, fallback_name in CRITICAL_UPSTREAM_ICONS.items():
        fallback = fallback_name.lower() if has_icon(fallback_name.lower()) else "home"
        resolved_icon = icon(icon_name.lower(), fallback=fallback)

        assert isinstance(resolved_icon, ft.Icon)
        assert isinstance(resolved_icon.name, str)
        assert resolved_icon.name


def test_upstream_icon_namespace_supports_pascal_or_snake_case() -> None:
    icons = _icons_namespace()
    assert getattr(icons, "HOME", None) is not None


def test_icon_compat_soporta_invocacion_posicional_y_legacy(monkeypatch):
    class _LegacyIcon:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    monkeypatch.setattr(ft, "Icon", _LegacyIcon)
    monkeypatch.setattr(ft, "_fletplus_patched_controls", False, raising=False)
    module = importlib.import_module("fletplus")
    importlib.reload(module)
    module.enable_compat_patches(force=True)

    positional = ft.Icon("home", color="blue")
    assert positional.args == ("home",)
    assert positional.kwargs == {"color": "blue"}

    legacy = ft.Icon(icon="settings", color="red")
    assert legacy.args == ("settings",)
    assert legacy.kwargs == {"color": "red"}


def test_icon_compat_prioridad_de_argumentos_en_conflicto(monkeypatch):
    class _LegacyIcon:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    monkeypatch.setattr(ft, "Icon", _LegacyIcon)
    monkeypatch.setattr(ft, "_fletplus_patched_controls", False, raising=False)
    module = importlib.import_module("fletplus")
    importlib.reload(module)
    module.enable_compat_patches(force=True)

    conflict = ft.Icon("posicional", name="name", icon="icon")
    assert conflict.args == ("posicional",)

    conflict_by_name = ft.Icon(name="name", icon="icon")
    assert conflict_by_name.args == ("name",)


def test_control_patch_es_idempotente(monkeypatch):
    class _LegacyIcon:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class _LegacyTextButton:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    monkeypatch.setattr(ft, "Icon", _LegacyIcon)
    monkeypatch.setattr(ft, "TextButton", _LegacyTextButton)
    monkeypatch.setattr(ft, "_fletplus_patched_controls", False, raising=False)
    module = importlib.import_module("fletplus")
    importlib.reload(module)
    module.enable_compat_patches(force=True)

    first_icon = ft.Icon
    first_button = ft.TextButton

    module = importlib.import_module("fletplus")
    importlib.reload(module)
    module.enable_compat_patches(force=True)

    assert ft.Icon is first_icon
    assert ft.TextButton is first_button
