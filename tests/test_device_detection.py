from enum import Enum

import flet as ft
import pytest

from fletplus.utils.device import is_desktop, is_mobile, is_web


class DummyPage:
    def __init__(self, platform: object):
        self.platform = platform
        self.title = ""
        self.controls = []
        self.theme = None
        self.theme_mode = None
        self.scroll = None
        self.horizontal_alignment = None
        self.updated = False

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        self.updated = True


class PlatformEnum(str, Enum):
    ANDROID = "android"
    WEB = "web"
    WINDOWS = "windows"


class ValueWrapper:
    def __init__(self, value: object):
        self.value = value


@pytest.mark.parametrize(
    ("platform", "mobile", "web", "desktop"),
    [
        ("android", True, False, False),
        ("web", False, True, False),
        ("windows", False, False, True),
    ],
)
def test_device_helpers(platform, mobile, web, desktop):
    page = DummyPage(platform)
    assert is_mobile(page) is mobile
    assert is_web(page) is web
    assert is_desktop(page) is desktop


@pytest.mark.parametrize(
    ("platform", "mobile", "web", "desktop"),
    [
        ("AnDrOiD", True, False, False),
        ("WEB", False, True, False),
        ("LiNuX", False, False, True),
    ],
)
def test_device_helpers_case_insensitive(platform, mobile, web, desktop):
    page = DummyPage(platform)
    assert is_mobile(page) is mobile
    assert is_web(page) is web
    assert is_desktop(page) is desktop


@pytest.mark.parametrize(
    ("platform", "mobile", "web", "desktop"),
    [
        (PlatformEnum.ANDROID, True, False, False),
        (PlatformEnum.WEB, False, True, False),
        (PlatformEnum.WINDOWS, False, False, True),
        (ValueWrapper("iOS"), True, False, False),
        (ValueWrapper("MACOS"), False, False, True),
        (ValueWrapper("WEB"), False, True, False),
    ],
)
def test_device_helpers_enum_and_non_string_values(platform, mobile, web, desktop):
    page = DummyPage(platform)
    assert is_mobile(page) is mobile
    assert is_web(page) is web
    assert is_desktop(page) is desktop
