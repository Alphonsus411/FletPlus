import flet as ft

from fletplus.utils.device import is_mobile, is_web, is_desktop
from fletplus.core import FletPlusApp


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


def test_fletplus_app_platform_tokens():
    def home():
        return ft.Text("Inicio")

    routes = {"home": home}

    page_mobile = DummyPage("android")
    mobile_config = {
        "tokens": {"colors": {"primary": ft.Colors.RED}},
        "mobile_tokens": {"colors": {"primary": ft.Colors.GREEN}},
    }
    app_mobile = FletPlusApp(page_mobile, routes, theme_config=mobile_config)
    assert app_mobile.platform == "mobile"
    assert app_mobile.theme.tokens["colors"]["primary"] == ft.Colors.GREEN

    page_web = DummyPage("web")
    web_config = {"web_tokens": {"colors": {"primary": ft.Colors.YELLOW}}}
    app_web = FletPlusApp(page_web, routes, theme_config=web_config)
    assert app_web.platform == "web"
    assert app_web.theme.tokens["colors"]["primary"] == ft.Colors.YELLOW

    page_desktop = DummyPage("linux")
    desktop_config = {"desktop_tokens": {"colors": {"primary": ft.Colors.BLUE}}}
    app_desktop = FletPlusApp(page_desktop, routes, theme_config=desktop_config)
    assert app_desktop.platform == "desktop"
    assert app_desktop.theme.tokens["colors"]["primary"] == ft.Colors.BLUE
