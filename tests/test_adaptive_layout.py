import flet as ft

from fletplus.components.adaptive_layout import (
    AdaptiveDestination,
    AdaptiveNavigationLayout,
)
from fletplus.components.caption_overlay import CaptionOverlay
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
        self.drawer = None
        self.drawer_opened = 0
        self.update_calls = 0

    def resize(self, width: int | None = None, height: int | None = None) -> None:
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if self.on_resize:
            self.on_resize(None)

    def update(self) -> None:
        self.update_calls += 1

    def set_focus(self, control: ft.Control) -> None:
        self.focus_target = control

    def open_drawer(self) -> None:
        self.drawer_opened += 1


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


def test_adaptive_navigation_layout_overlay_drawer_and_fab():
    page = DummyPage(520, 900)
    destinations = [
        AdaptiveDestination(label="Inicio", icon=ft.Icons.HOME_OUTLINED),
        AdaptiveDestination(label="Perfil", icon=ft.Icons.PERSON_OUTLINED),
    ]

    overlay = CaptionOverlay()
    prefs = AccessibilityPreferences(enable_captions=True, caption_mode="overlay")

    layout = AdaptiveNavigationLayout(
        destinations,
        lambda idx, dev: ft.Text(f"Vista {idx}-{dev}"),
        accessibility=prefs,
        drawer=ft.NavigationDrawer(controls=[ft.Text("Menú")]),
        floating_action_button=ft.FloatingActionButton(icon=ft.Icons.ADD),
        caption_overlay=overlay,
    )

    root = layout.build(page)

    assert page.drawer is not None
    assert isinstance(root.controls[1], ft.Row)
    assert isinstance(root.controls[2], ft.Stack)
    assert overlay.control.visible is True

    layout._open_drawer(None)
    assert page.drawer_opened == 1

    page.resize(width=1300)
    assert layout.current_device == "desktop"
    main_row = layout.root.controls[-1]
    assert isinstance(main_row, ft.Row)
    assert isinstance(main_row.controls[1], ft.Stack)


def test_adaptive_navigation_layout_secondary_panel():
    page = DummyPage(1400, 900)
    destinations = [
        AdaptiveDestination(label="Inicio", icon=ft.Icons.HOME_OUTLINED),
        AdaptiveDestination(label="Perfil", icon=ft.Icons.PERSON_OUTLINED),
    ]

    calls: list[str] = []

    def secondary(device: str) -> ft.Control:
        calls.append(device)
        return ft.Text(f"Panel {device}")

    layout = AdaptiveNavigationLayout(
        destinations,
        lambda idx, dev: ft.Text(f"Vista {idx}-{dev}"),
        secondary_panel_builder=secondary,
        accessibility=AccessibilityPreferences(enable_captions=False),
    )

    layout.build(page)

    assert calls[-1] == "desktop"
    main_row = layout.root.controls[-1]
    assert isinstance(main_row, ft.Row)
    assert len(main_row.controls) == 3
    secondary_container = main_row.controls[2]
    assert isinstance(secondary_container, ft.Container)
    assert isinstance(secondary_container.content, ft.Text)
    assert "Panel desktop" in secondary_container.content.value


class DummyWindow:
    def __init__(self, width: int = 0) -> None:
        self.width = width


class DummyPageWithWindow:
    def __init__(self, width: int, height: int, platform: str = "android") -> None:
        self.width = width
        self.height = height
        self.platform = platform
        self.window = DummyWindow(width)
        self.on_resize = None
        self.theme = ft.Theme()
        self.locale = None
        self.focus_target = None
        self.drawer = None
        self.drawer_opened = 0
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1


def test_on_width_change_updates_window_width_api() -> None:
    layout = AdaptiveNavigationLayout(
        [AdaptiveDestination(label="Inicio", icon=ft.Icons.HOME_OUTLINED)],
        lambda idx, dev: ft.Text(f"Vista {idx}-{dev}"),
    )
    page = DummyPageWithWindow(480, 800)

    layout.build(page)
    layout._on_width_change(960)

    assert page.window.width == 960


def test_on_width_change_falls_back_to_legacy_window_width_api() -> None:
    class LegacyPage(DummyPage):
        def __init__(self, width: int, height: int) -> None:
            super().__init__(width, height)
            self.window_width = width

    layout = AdaptiveNavigationLayout(
        [AdaptiveDestination(label="Inicio", icon=ft.Icons.HOME_OUTLINED)],
        lambda idx, dev: ft.Text(f"Vista {idx}-{dev}"),
    )
    page = LegacyPage(480, 800)

    layout.build(page)
    layout._on_width_change(970)

    assert page.window_width == 970


def test_build_uses_window_width_when_page_width_missing() -> None:
    class WindowOnlyPage(DummyPageWithWindow):
        def __init__(self, width: int, height: int) -> None:
            super().__init__(width, height)
            self.width = None

    page = WindowOnlyPage(1360, 768)
    layout = AdaptiveNavigationLayout(
        [AdaptiveDestination(label="Inicio", icon=ft.Icons.HOME_OUTLINED)],
        lambda idx, dev: ft.Text(f"Vista {idx}-{dev}"),
    )

    layout.build(page)

    assert layout.current_device == "desktop"


def test_open_drawer_is_tolerant_when_method_not_available() -> None:
    class PageWithoutOpenDrawer(DummyPage):
        def open_drawer(self) -> None:  # type: ignore[override]
            raise RuntimeError("no disponible")

    page = PageWithoutOpenDrawer(520, 900)
    layout = AdaptiveNavigationLayout(
        [AdaptiveDestination(label="Inicio", icon=ft.Icons.HOME_OUTLINED)],
        lambda idx, dev: ft.Text(f"Vista {idx}-{dev}"),
        drawer=ft.NavigationDrawer(controls=[ft.Text("Menú")]),
    )

    layout.build(page)
    layout._open_drawer(None)

    assert page.drawer is not None
