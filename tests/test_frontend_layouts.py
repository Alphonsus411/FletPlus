import flet as ft

from fletplus import FrontEndConfig
from fletplus.components import (
    CardGrid,
    HeroSection,
    PageShell,
    Section,
    resolve_layout_tokens,
)


class DummyPage:
    width = 390
    height = 844
    padding = None
    theme = None
    fonts = {}


def test_resolve_layout_tokens_uses_device_overrides():
    page = DummyPage()
    config = FrontEndConfig(spacing=10, page_padding=12, max_content_width=900)

    tokens = resolve_layout_tokens(
        page,
        config=config,
        spacing_by_device={"mobile": 8},
        padding_by_device={"mobile": 6},
        max_width_by_device={"mobile": 360},
        columns_by_device={"mobile": 1},
    )

    assert tokens.profile.name == "mobile"
    assert tokens.spacing == 8
    assert tokens.padding.left == 6
    assert tokens.max_width == 360
    assert tokens.columns == 1


def test_page_shell_builds_semantic_sections():
    page = DummyPage()
    config = FrontEndConfig(spacing=10, page_padding=12, max_content_width=900)
    grid = CardGrid(cards=[ft.Text("Card")], config=config, columns_by_device={"mobile": 1})

    shell = PageShell(
        sections=[
            HeroSection(headline="Hola", description="Layout", config=config),
            Section(title="Resumen", content=grid.build(page), config=config),
        ],
        config=config,
    ).build(page)

    assert shell.content is not None
    assert shell.content.width == 900


def test_page_shell_uses_mobile_screen_tokens_as_fallback():
    page = DummyPage()
    config = FrontEndConfig(
        spacing=10,
        page_padding=12,
        max_content_width=900,
        screen_tokens={"mobile": {"spacing": 7, "page_padding": 9, "max_width": 360}},
    )

    shell = PageShell(
        sections=[Section(content=ft.Text("Mobile"), config=config)],
        config=config,
    ).build(page)

    inner = shell.content
    assert inner is not None
    assert inner.width == 360
    assert inner.padding.left == 9
    assert inner.content.spacing == 7


def test_section_uses_desktop_screen_tokens_as_fallback():
    page = DummyPage()
    page.width = 1280
    page.height = 800
    config = FrontEndConfig(
        spacing=10,
        page_padding=12,
        max_content_width=900,
        screen_tokens={"desktop": {"spacing": 28, "padding": 32, "max_width": 1180}},
    )

    section = Section(content=ft.Text("Desktop"), config=config).build(page)

    assert section.width == 1180
    assert section.padding.left == 32
    assert section.content.spacing == 28


def test_card_grid_uses_portrait_screen_tokens_as_fallback():
    page = DummyPage()
    page.width = 390
    page.height = 844
    config = FrontEndConfig(
        spacing=10,
        page_padding=12,
        max_content_width=900,
        screen_tokens={
            "portrait": {
                "spacing": 11,
                "page_padding": 13,
                "max_width": 330,
                "columns": 2,
            }
        },
    )

    grid = CardGrid(cards=[ft.Text("A"), ft.Text("B")], config=config).build(page)

    assert grid.width == 330
    assert grid.padding.left == 13
    assert grid.content.spacing == 11
    assert grid.content.run_spacing == 11
    assert [control.col for control in grid.content.controls] == [
        {"xs": 12, "sm": 6},
        {"xs": 12, "sm": 6},
    ]


def test_layout_resolution_priority_keeps_explicit_and_device_overrides_first():
    page = DummyPage()
    config = FrontEndConfig(
        spacing=10,
        page_padding=12,
        max_content_width=900,
        screen_tokens={"mobile": {"spacing": 7, "page_padding": 9, "max_width": 360, "columns": 2}},
    )

    tokens = resolve_layout_tokens(
        page,
        config=config,
        spacing=30,
        padding=31,
        max_width=700,
        columns=4,
        spacing_by_device={"mobile": 20},
        padding_by_device={"mobile": 21},
        max_width_by_device={"mobile": 600},
        columns_by_device={"mobile": 3},
    )

    assert tokens.spacing == 30
    assert tokens.padding.left == 31
    assert tokens.max_width == 700
    assert tokens.columns == 4
