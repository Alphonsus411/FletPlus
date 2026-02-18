"""Tests unitarios para la capa de compatibilidad de Flet."""

from __future__ import annotations

from pathlib import Path

import asyncio

from fletplus.utils.flet_compat import (
    get_page_height,
    get_page_width,
    safe_close_drawer,
    safe_close_window,
    safe_open_drawer,
    safe_set_window_attr,
    safe_take_screenshot,
    safe_update_page,
    set_page_height,
    set_page_width,
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
