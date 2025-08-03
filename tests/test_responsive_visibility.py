import flet as ft
from fletplus.utils.responsive_visibility import ResponsiveVisibility


class DummyPage:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.on_resize = None

    def resize(self, width: int | None = None, height: int | None = None):
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if self.on_resize:
            self.on_resize(None)

    def update(self):
        pass


def test_responsive_visibility_width():
    page = DummyPage(500, 400)
    txt = ft.Text("hola")
    ResponsiveVisibility(page, txt, width_breakpoints={0: True, 600: False})

    assert txt.visible is True
    page.resize(650)
    assert txt.visible is False


def test_responsive_visibility_orientation():
    page = DummyPage(500, 800)
    txt = ft.Text("hola")
    ResponsiveVisibility(page, txt, orientation_visibility={"portrait": True, "landscape": False})

    assert txt.visible is True
    page.resize(width=900, height=600)
    assert txt.visible is False
