import flet as ft

from fletplus.components.layouts import (
    ResponsiveContainer,
    FlexRow,
    FlexColumn,
    Grid,
    GridItem,
    Spacer,
    Stack,
    StackItem,
    Wrap,
)
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


def test_grid_resolves_spans_and_spacing_with_aliases():
    page = DummyPage(500, 800)
    grid = Grid(
        items=[
            GridItem(ft.Text("Primario"), span_breakpoints={"xs": 12, "md": 6, "xl": 3}),
            GridItem(ft.Text("Secundario"), span=6, visible_breakpoints={"md": True}),
        ],
        spacing=8,
        spacing_breakpoints={"md": 16},
    )
    row = grid.init_responsive(page)
    assert row.controls[0].col == 12
    assert row.controls[0].visible is True
    assert row.spacing == 8

    page.resize(900)
    assert row.controls[0].col == 6
    assert row.controls[1].visible is True
    assert row.spacing == 16

    page.resize(1400)
    assert row.controls[0].col == 3


def test_wrap_updates_spacing_with_symbolic_breakpoints():
    page = DummyPage(640, 800)
    wrap = Wrap(
        [ft.Text("A"), ft.Text("B")],
        breakpoints={
            "xs": {"spacing": 4, "run_spacing": 2},
            "md": {"spacing": 12, "run_spacing": 6},
        },
    )
    row = wrap.init_responsive(page)
    assert row.spacing == 4
    assert row.run_spacing == 2

    page.resize(900)
    assert row.spacing == 12
    assert row.run_spacing == 6


def test_stack_controls_visibility_via_aliases():
    page = DummyPage(500, 800)
    item = StackItem(ft.Text("Visible"), visible_breakpoints={"xs": True, "md": False, "xl": True})
    stack = Stack([item])
    layout = stack.init_responsive(page)
    assert layout.controls[0].visible is True

    page.resize(900)
    assert layout.controls[0].visible is False

    page.resize(1500)
    assert layout.controls[0].visible is True


def test_spacer_adjusts_size_per_breakpoint():
    page = DummyPage(300, 800)
    spacer = Spacer(orientation="vertical", breakpoints={"xs": 4, "md": 10})
    control = spacer.init_responsive(page)
    assert control.height == 4

    page.resize(900)
    assert control.height == 10
