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
