import flet as ft

from fletplus.components.adaptive_layout import (
    AdaptiveDestination,
    AdaptiveNavigationLayout,
)
from fletplus.utils.accessibility import AccessibilityPreferences


class DummyPage:
    def __init__(self, width: int, height: int, platform: str = "android") -> None:
        self.width = width
        self.height = height
        self.platform = platform
        self.on_resize = None
        self.theme = ft.Theme()
        self.locale = None
        self.focus_target = None

    def resize(self, width: int | None = None, height: int | None = None) -> None:
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if self.on_resize:
            self.on_resize(None)

    def update(self) -> None:
        pass

    def set_focus(self, control: ft.Control) -> None:
        self.focus_target = control


def test_adaptive_navigation_layout_switches_between_devices():
    page = DummyPage(480, 800)
    calls: list[tuple[int, str]] = []
    destinations = [
        AdaptiveDestination(label="Inicio", icon=ft.Icons.HOME_OUTLINED),
        AdaptiveDestination(label="Perfil", icon=ft.Icons.PERSON_OUTLINED),
    ]

    def builder(index: int, device: str) -> ft.Control:
        calls.append((index, device))
        return ft.Text(f"{index}-{device}")

    layout = AdaptiveNavigationLayout(
        destinations,
        builder,
        accessibility=AccessibilityPreferences(enable_captions=True),
    )

    root = layout.build(page)

    assert isinstance(root, ft.Column)
    assert layout.navigation_bar.visible is True
    assert layout.navigation_rail.visible is False
    assert layout.current_device == "mobile"
    assert calls[-1] == (0, "mobile")
    assert layout.caption_container.content.value.startswith("Sección activa")

    page.resize(width=1300)
    assert layout.navigation_bar.visible is False
    assert layout.navigation_rail.visible is True
    assert layout.current_device == "desktop"
    assert calls[-1][1] == "desktop"


def test_adaptive_navigation_layout_updates_selection_and_captions():
    page = DummyPage(900, 800, platform="windows")
    destinations = [
        AdaptiveDestination(label="Inicio", icon=ft.Icons.HOME_OUTLINED),
        AdaptiveDestination(label="Perfil", icon=ft.Icons.PERSON_OUTLINED),
    ]

    layout = AdaptiveNavigationLayout(
        destinations,
        lambda idx, dev: ft.Text(f"Vista {idx}-{dev}"),
        accessibility=AccessibilityPreferences(enable_captions=True),
    )
    layout.build(page)

    layout.select_destination(1)

    assert layout.selected_index == 1
    assert layout.navigation_bar.selected_index == 1
    assert "Perfil" in layout.caption_container.content.value
