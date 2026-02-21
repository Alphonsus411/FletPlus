"""Tests unitarios para la capa de compatibilidad de Flet."""

from __future__ import annotations

from pathlib import Path

import asyncio

from fletplus.utils.flet_compat import (
    get_flet_color,
    get_flet_colors,
    build_flet_control,
    get_flet_enum,
    get_flet_enum_member,
    get_flet_icon,
    get_flet_icons,
    get_page_height,
    get_page_width,
    make_navigation_bar_destination,
    make_navigation_drawer_destination,
    make_navigation_rail_destination,
    has_page_overlay_control,
    safe_close_drawer,
    safe_close_window,
    safe_open_drawer,
    safe_page_set_focus,
    safe_page_speak,
    safe_request_page_update,
    safe_set_window_attr,
    safe_take_screenshot,
    safe_update_page,
    safe_update_page_sync,
    set_page_drawer,
    set_page_height,
    set_page_title,
    set_page_width,
    with_opacity,
    append_page_overlay,
)


class _WindowWithAttrs:
    def __init__(self) -> None:
        self.width = 0.0
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _PageWithWindow:
    def __init__(self) -> None:
        self.window = _WindowWithAttrs()


class _DrawerPage:
    def __init__(self) -> None:
        self.drawer_opened = False
        self.drawer_closed = False

    def open_drawer(self) -> None:
        self.drawer_opened = True

    def close_drawer(self) -> None:
        self.drawer_closed = True


def test_safe_set_window_attr_handles_absence_without_exception() -> None:
    class _PageWithoutWindow:
        pass

    page = _PageWithoutWindow()
    assert safe_set_window_attr(page, "width", 800.0) is False


def test_safe_set_window_attr_sets_value_when_present() -> None:
    page = _PageWithWindow()

    assert safe_set_window_attr(page, "width", 800.0) is True
    assert page.window.width == 800.0


def test_safe_close_window_uses_supported_method_when_present() -> None:
    page = _PageWithWindow()

    assert safe_close_window(page) is True
    assert page.window.closed is True


def test_safe_update_page_falls_back_to_update() -> None:
    class _Page:
        def __init__(self) -> None:
            self.updated = False

        def update(self) -> None:
            self.updated = True

    page = _Page()
    asyncio.run(safe_update_page(page))

    assert page.updated is True


def test_safe_take_screenshot_uses_invoke_method_fallback() -> None:
    class _Page:
        def __init__(self) -> None:
            self.called = False

        async def _invoke_method_async(self, method: str, payload: dict, **kwargs) -> None:
            self.called = method == "screenshot" and payload["path"].endswith("sample.png")

    page = _Page()
    asyncio.run(safe_take_screenshot(page, Path("sample.png")))

    assert page.called is True


def test_safe_take_screenshot_no_supported_api_does_not_raise() -> None:
    class _Page:
        pass

    page = _Page()
    asyncio.run(safe_take_screenshot(page, Path("sample.png")))


def test_get_page_width_prioritizes_window_width() -> None:
    page = _PageWithWindow()
    page.window.width = 1024
    page.window_width = 800
    page.width = 640

    assert get_page_width(page) == 1024.0


def test_get_page_width_falls_back_to_legacy_window_width() -> None:
    class _Page:
        def __init__(self) -> None:
            self.window_width = 720

    page = _Page()

    assert get_page_width(page) == 720.0


def test_set_page_width_writes_window_width_when_available() -> None:
    page = _PageWithWindow()

    assert set_page_width(page, 1111) is True
    assert page.window.width == 1111


def test_set_page_width_falls_back_to_legacy_window_width() -> None:
    class _Page:
        def __init__(self) -> None:
            self.window_width = 700

    page = _Page()

    assert set_page_width(page, 900) is True
    assert page.window_width == 900


def test_get_page_height_prioritizes_window_height() -> None:
    page = _PageWithWindow()
    page.window.height = 730
    page.window_height = 700
    page.height = 680

    assert get_page_height(page) == 730.0


def test_set_page_height_falls_back_to_legacy_window_height() -> None:
    class _Page:
        def __init__(self) -> None:
            self.window_height = 700

    page = _Page()

    assert set_page_height(page, 910) is True
    assert page.window_height == 910


def test_safe_open_drawer_and_close_drawer_work_when_available() -> None:
    page = _DrawerPage()

    assert safe_open_drawer(page) is True
    assert safe_close_drawer(page) is True
    assert page.drawer_opened is True
    assert page.drawer_closed is True


def test_safe_close_drawer_falls_back_to_drawer_open_flag() -> None:
    class _Page:
        def __init__(self) -> None:
            self.drawer = type("Drawer", (), {"open": True})()

    page = _Page()

    assert safe_close_drawer(page) is True
    assert page.drawer.open is False


def test_safe_update_page_sync_noop_when_update_absent() -> None:
    class _Page:
        pass

    safe_update_page_sync(_Page())


def test_safe_update_page_sync_calls_update_when_available() -> None:
    class _Page:
        def __init__(self) -> None:
            self.updated = False

        def update(self) -> None:
            self.updated = True

    page = _Page()
    safe_update_page_sync(page)

    assert page.updated is True


def test_get_flet_icons_presence_and_absence(monkeypatch) -> None:
    from fletplus.utils import flet_compat

    fake = type("Icons", (), {"MENU": "menu"})()
    monkeypatch.setattr(flet_compat.ft, "Icons", fake, raising=False)
    monkeypatch.delattr(flet_compat.ft, "icons", raising=False)
    assert get_flet_icons() is fake

    monkeypatch.delattr(flet_compat.ft, "Icons", raising=False)
    monkeypatch.delattr(flet_compat.ft, "icons", raising=False)
    assert get_flet_icons() is None


def test_get_flet_colors_presence_and_absence(monkeypatch) -> None:
    from fletplus.utils import flet_compat

    fake = type("Colors", (), {"PRIMARY": "#123"})()
    monkeypatch.setattr(flet_compat.ft, "Colors", fake, raising=False)
    monkeypatch.delattr(flet_compat.ft, "colors", raising=False)
    assert get_flet_colors() is fake

    monkeypatch.delattr(flet_compat.ft, "Colors", raising=False)
    monkeypatch.delattr(flet_compat.ft, "colors", raising=False)
    assert get_flet_colors() is None


def test_get_flet_icon_and_color_member_fallbacks(monkeypatch) -> None:
    from fletplus.utils import flet_compat

    icons = type("Icons", (), {"MENU": "menu"})()
    colors = type("Colors", (), {"PRIMARY": "#1976D2"})()
    monkeypatch.setattr(flet_compat.ft, "Icons", icons, raising=False)
    monkeypatch.setattr(flet_compat.ft, "Colors", colors, raising=False)

    assert get_flet_icon("MENU", "fallback") == "menu"
    assert get_flet_icon("MISSING", "fallback") == "fallback"
    assert get_flet_color("PRIMARY", "fallback") == "#1976D2"
    assert get_flet_color("MISSING", "fallback") == "fallback"


def test_get_flet_enum_and_member_presence_and_absence(monkeypatch) -> None:
    from fletplus.utils import flet_compat

    enum_obj = type("ControlState", (), {"DEFAULT": "default"})()
    monkeypatch.setattr(flet_compat.ft, "ControlState", enum_obj, raising=False)

    assert get_flet_enum("ControlState") is enum_obj
    assert get_flet_enum_member("ControlState", "DEFAULT", "fallback") == "default"
    assert get_flet_enum_member("ControlState", "HOVERED", "fallback") == "fallback"

    monkeypatch.delattr(flet_compat.ft, "ControlState", raising=False)
    assert get_flet_enum("ControlState") is None
    assert get_flet_enum_member("ControlState", "DEFAULT", "fallback") == "fallback"


def test_with_opacity_presence_and_absence(monkeypatch) -> None:
    from fletplus.utils import flet_compat

    class _Colors:
        @staticmethod
        def with_opacity(opacity: float, color: str) -> str:
            return f"{opacity}:{color}"

    monkeypatch.setattr(flet_compat.ft, "Colors", _Colors, raising=False)
    assert with_opacity(0.5, "#000") == "0.5:#000"

    monkeypatch.delattr(flet_compat.ft, "Colors", raising=False)
    monkeypatch.delattr(flet_compat.ft, "colors", raising=False)
    assert with_opacity(0.5, "#000", default="#111") == "#111"


def test_safe_update_page_uses_update_async_when_available() -> None:
    class _Page:
        def __init__(self) -> None:
            self.async_updated = False
            self.sync_updated = False

        async def update_async(self) -> None:
            self.async_updated = True

        def update(self) -> None:
            self.sync_updated = True

    page = _Page()
    asyncio.run(safe_update_page(page))

    assert page.async_updated is True
    assert page.sync_updated is False


def test_get_flet_icons_falls_back_to_lowercase_namespace(monkeypatch) -> None:
    from fletplus.utils import flet_compat

    fake_icons = type("icons", (), {"MENU": "menu"})()
    monkeypatch.delattr(flet_compat.ft, "Icons", raising=False)
    monkeypatch.setattr(flet_compat.ft, "icons", fake_icons, raising=False)

    assert get_flet_icons() is fake_icons


def test_get_flet_colors_falls_back_to_lowercase_namespace(monkeypatch) -> None:
    from fletplus.utils import flet_compat

    class _Colors:
        @staticmethod
        def with_opacity(opacity: float, color: str) -> str:
            return f"{opacity}:{color}"

    monkeypatch.delattr(flet_compat.ft, "Colors", raising=False)
    monkeypatch.setattr(flet_compat.ft, "colors", _Colors, raising=False)

    assert get_flet_colors() is _Colors


def test_page_overlay_helpers_cover_presence_and_absence() -> None:
    class _Page:
        def __init__(self) -> None:
            self.overlay = []

    page = _Page()
    control = object()

    assert has_page_overlay_control(page, control) is False
    assert append_page_overlay(page, control) is True
    assert has_page_overlay_control(page, control) is True

    class _PageWithoutOverlay:
        pass

    assert append_page_overlay(_PageWithoutOverlay(), control) is False


def test_page_attribute_helpers_for_title_drawer_focus_and_speak() -> None:
    class _Page:
        def __init__(self) -> None:
            self.title = ""
            self.drawer = None
            self.focused = None
            self.spoken = []

        def set_focus(self, control: object) -> None:
            self.focused = control

        def speak(self, message: str) -> None:
            self.spoken.append(message)

    page = _Page()
    control = object()

    assert set_page_title(page, "Nuevo título") is True
    assert set_page_drawer(page, control) is True
    assert safe_page_set_focus(page, control) is True
    assert safe_page_speak(page, "hola") is True
    assert page.title == "Nuevo título"
    assert page.drawer is control
    assert page.focused is control
    assert page.spoken == ["hola"]


def test_safe_request_page_update_uses_run_task_update_async_when_needed() -> None:
    class _Page:
        def __init__(self) -> None:
            self.updated_async = False
            self.run_task_calls = 0

        def update(self) -> None:
            raise RuntimeError("update no permitido")

        async def update_async(self) -> None:
            self.updated_async = True

        def run_task(self, callback):
            self.run_task_calls += 1
            asyncio.run(callback())

    page = _Page()
    safe_request_page_update(page)

    assert page.run_task_calls == 1
    assert page.updated_async is True


def test_build_flet_control_returns_none_when_symbol_missing(monkeypatch) -> None:
    from fletplus.utils import flet_compat

    monkeypatch.delattr(flet_compat.ft, "NavigationBarDestination", raising=False)
    assert build_flet_control("NavigationBarDestination", label="Inicio", icon="home") is None


def test_navigation_destination_factories_fallback_when_symbol_missing(monkeypatch) -> None:
    from fletplus.utils import flet_compat

    monkeypatch.delattr(flet_compat.ft, "NavigationBarDestination", raising=False)
    monkeypatch.delattr(flet_compat.ft, "NavigationRailDestination", raising=False)
    monkeypatch.delattr(flet_compat.ft, "NavigationDrawerDestination", raising=False)

    nav_bar = make_navigation_bar_destination(icon="home", label="Inicio")
    nav_rail = make_navigation_rail_destination(icon="home", label="Inicio")
    nav_drawer = make_navigation_drawer_destination(icon="home", label="Inicio")

    assert isinstance(nav_bar, flet_compat.ft.Container)
    assert isinstance(nav_rail, flet_compat.ft.Container)
    assert isinstance(nav_drawer, flet_compat.ft.Container)


def test_navigation_destination_factories_use_symbols_when_present(monkeypatch) -> None:
    from fletplus.utils import flet_compat

    class _Bar:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    class _Rail:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    class _Drawer:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    monkeypatch.setattr(flet_compat.ft, "NavigationBarDestination", _Bar, raising=False)
    monkeypatch.setattr(flet_compat.ft, "NavigationRailDestination", _Rail, raising=False)
    monkeypatch.setattr(flet_compat.ft, "NavigationDrawerDestination", _Drawer, raising=False)

    nav_bar = make_navigation_bar_destination(icon="home", label="Inicio")
    nav_rail = make_navigation_rail_destination(icon="home", label="Inicio")
    nav_drawer = make_navigation_drawer_destination(icon="home", label="Inicio")

    assert isinstance(nav_bar, _Bar)
    assert isinstance(nav_rail, _Rail)
    assert isinstance(nav_drawer, _Drawer)
