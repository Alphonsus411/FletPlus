"""Tests unitarios para la capa de compatibilidad de Flet."""

from __future__ import annotations

from pathlib import Path

import asyncio
import pytest

from fletplus.utils.flet_compat import (
    ScreenshotNotSupportedError,
    safe_close_window,
    safe_set_window_attr,
    safe_take_screenshot,
    safe_update_page,
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


def test_safe_take_screenshot_no_supported_api_raises() -> None:
    class _Page:
        pass

    page = _Page()
    with pytest.raises(ScreenshotNotSupportedError):
        asyncio.run(safe_take_screenshot(page, Path("sample.png")))
