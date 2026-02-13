import flet as ft

from fletplus.utils.device import is_mobile, is_web, is_desktop


class DummyPage:
    def __init__(self, platform: str):
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


def test_device_helpers():
    android = type("P", (), {"platform": "android"})()
    assert is_mobile(android)
    assert not is_web(android)
    assert not is_desktop(android)

    web = type("P", (), {"platform": "web"})()
    assert is_web(web)
    assert not is_mobile(web)

    desktop = type("P", (), {"platform": "windows"})()
    assert is_desktop(desktop)
    assert not is_mobile(desktop)

