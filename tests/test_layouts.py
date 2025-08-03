import flet as ft
from fletplus.components.layouts import ResponsiveContainer, FlexRow, FlexColumn
from fletplus.styles import Style


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


def test_flex_row_updates_properties():
    page = DummyPage(500, 800)
    row = FlexRow(
        [ft.Text("A"), ft.Text("B")],
        breakpoints={
            0: {"spacing": 5, "alignment": ft.MainAxisAlignment.START, "wrap": False},
            600: {"spacing": 20, "alignment": ft.MainAxisAlignment.SPACE_BETWEEN, "wrap": True},
        },
    )
    layout = row.init_responsive(page)
    assert layout.spacing == 5
    assert layout.wrap is False
    assert layout.alignment == ft.MainAxisAlignment.START

    page.resize(700)
    assert layout.spacing == 20
    assert layout.wrap is True
    assert layout.alignment == ft.MainAxisAlignment.SPACE_BETWEEN


def test_flex_column_updates_properties():
    page = DummyPage(400, 800)
    col = FlexColumn(
        [ft.Text("A"), ft.Text("B")],
        breakpoints={
            0: {"spacing": 5, "alignment": ft.MainAxisAlignment.START, "wrap": False},
            500: {"spacing": 15, "alignment": ft.MainAxisAlignment.CENTER, "wrap": True},
        },
    )
    layout = col.init_responsive(page)
    assert layout.spacing == 5
    assert layout.alignment == ft.MainAxisAlignment.START
    assert not layout.scroll

    page.resize(600)
    assert layout.spacing == 15
    assert layout.alignment == ft.MainAxisAlignment.CENTER
    assert layout.scroll is True


def test_responsive_container_adjusts_style():
    page = DummyPage(300, 800)
    rc = ResponsiveContainer(
        ft.Text("Hola"),
        breakpoints={
            0: Style(max_width=200, padding=5),
            400: Style(max_width=400, padding=20),
        },
    )
    container = rc.init_responsive(page)
    assert container.max_width == 200
    assert container.padding == 5

    page.resize(500)
    assert container.max_width == 400
    assert container.padding == 20
