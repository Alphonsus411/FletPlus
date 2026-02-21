import flet as ft

from fletplus.components import (
    AdaptiveNavigationItem,
    UniversalAdaptiveScaffold,
)
from fletplus.components.accessibility_panel import AccessibilityPanel
from fletplus.utils.accessibility import AccessibilityPreferences


class DummyPage:
    def __init__(self, width: int, height: int, platform: str = "web") -> None:
        self.width = width
        self.height = height
        self.platform = platform
        self.on_resize = None
        self.theme = ft.Theme()
        self.title = ""
        self.drawer = None
        self.overlay: list[ft.Control] = []
        self.update_calls = 0
        self.focus_target: ft.Control | None = None
        self.drawer_opened = 0
        self.speak_messages: list[str] = []

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

    def speak(self, message: str) -> None:
        self.speak_messages.append(message)


def _scaffold(items_count: int = 3) -> tuple[UniversalAdaptiveScaffold, DummyPage]:
    icons = [ft.Icons.LOOKS_ONE, ft.Icons.LOOKS_TWO, ft.Icons.LOOKS_3]
    items = [
        AdaptiveNavigationItem(
            f"tab-{idx}",
            f"Sección {idx}",
            icons[idx] if idx < len(icons) else ft.Icons.DASHBOARD_OUTLINED,
        )
        for idx in range(items_count)
    ]
    prefs = AccessibilityPreferences(enable_captions=True, caption_mode="inline")
    page = DummyPage(480, 820)
    scaffold = UniversalAdaptiveScaffold(
        navigation_items=items,
        content_builder=lambda item, idx: ft.Text(f"Contenido {item.id}-{idx}"),
        accessibility=prefs,
        accessibility_panel=AccessibilityPanel(preferences=prefs),
        page_title="Panel universal",
        header_controls=[ft.Text("Encabezado"), ft.Text("Estado OK")],
    )
    root = scaffold.build(page)
    assert isinstance(root, ft.Control)
    return scaffold, page


def test_universal_scaffold_initializes_mobile_layout() -> None:
    scaffold, page = _scaffold()

    assert isinstance(scaffold.root, ft.Stack)
    assert scaffold.navigation_items[0].label.startswith("Sección")
    assert scaffold.selected_item.id == "tab-0"
    assert scaffold._nav_bar.visible is True
    assert scaffold._nav_rail.visible is False
    assert any(isinstance(ctrl, ft.BottomSheet) for ctrl in page.overlay)


def test_universal_scaffold_switches_to_desktop_layout() -> None:
    scaffold, page = _scaffold()

    page.resize(width=1320)

    assert scaffold._nav_bar.visible is False
    assert scaffold._nav_rail.visible is True
    assert scaffold._nav_rail.extended is True
    assert scaffold._current_device == "desktop"

    scaffold._toggle_accessibility_panel(None)
    assert scaffold._show_desktop_accessibility_panel is True
    assert page.update_calls > 0


def test_universal_scaffold_inline_captions_and_speak() -> None:
    scaffold, page = _scaffold()

    scaffold._handle_accessibility_change(scaffold.accessibility)
    scaffold.announce("Mensaje importante", tone="success")

    assert "Mensaje importante" in scaffold._inline_caption_text.value
    assert scaffold._inline_caption_container.visible is True
    assert "Mensaje importante" in page.speak_messages


class DummyWindow:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height


class WindowOnlyPage(DummyPage):
    def __init__(self, width: int, height: int, platform: str = "web") -> None:
        super().__init__(width, height, platform=platform)
        self.window = DummyWindow(width, height)
        self.width = None
        self.height = None


def test_universal_scaffold_uses_window_dimensions_when_page_dimensions_missing() -> None:
    items = [AdaptiveNavigationItem("tab-0", "Inicio", ft.Icons.HOME)]
    page = WindowOnlyPage(1280, 800)
    scaffold = UniversalAdaptiveScaffold(
        navigation_items=items,
        content_builder=lambda item, idx: ft.Text(f"Contenido {item.id}-{idx}"),
        accessibility=AccessibilityPreferences(enable_captions=False),
    )

    scaffold.build(page)

    assert scaffold._current_device == "desktop"


def test_universal_scaffold_open_drawer_is_tolerant_with_failing_runtime() -> None:
    class FailingOpenDrawerPage(DummyPage):
        def open_drawer(self) -> None:  # type: ignore[override]
            raise RuntimeError("drawer API unavailable")

    items = [AdaptiveNavigationItem("tab-0", "Inicio", ft.Icons.HOME)]
    page = FailingOpenDrawerPage(520, 800)
    scaffold = UniversalAdaptiveScaffold(
        navigation_items=items,
        content_builder=lambda item, idx: ft.Text(f"Contenido {item.id}-{idx}"),
        drawer=ft.NavigationDrawer(controls=[ft.Text("Menú")]),
        accessibility=AccessibilityPreferences(enable_captions=False),
    )

    scaffold.build(page)
    scaffold._open_drawer()

    assert page.drawer is not None


def test_universal_scaffold_tolerates_missing_overlay_list() -> None:
    class PageWithoutOverlay(DummyPage):
        def __init__(self, width: int, height: int) -> None:
            super().__init__(width, height)
            self.overlay = None

    items = [AdaptiveNavigationItem("tab-0", "Inicio", ft.Icons.HOME)]
    page = PageWithoutOverlay(520, 800)
    scaffold = UniversalAdaptiveScaffold(
        navigation_items=items,
        content_builder=lambda item, idx: ft.Text(f"Contenido {item.id}-{idx}"),
        accessibility=AccessibilityPreferences(enable_captions=False),
    )

    root = scaffold.build(page)

    assert isinstance(root, ft.Control)


def test_universal_scaffold_announce_tolerates_missing_speak_api() -> None:
    class PageWithoutSpeak(DummyPage):
        def __init__(self, width: int, height: int) -> None:
            super().__init__(width, height)
            self.speak = None

    items = [AdaptiveNavigationItem("tab-0", "Inicio", ft.Icons.HOME)]
    page = PageWithoutSpeak(520, 800)
    scaffold = UniversalAdaptiveScaffold(
        navigation_items=items,
        content_builder=lambda item, idx: ft.Text(f"Contenido {item.id}-{idx}"),
        accessibility=AccessibilityPreferences(enable_captions=True, caption_mode="inline"),
    )

    scaffold.build(page)
    scaffold.announce("Mensaje sin API speak")

    assert "Mensaje sin API speak" in scaffold._inline_caption_text.value


def test_universal_scaffold_focus_tolerates_missing_set_focus() -> None:
    class PageWithoutSetFocus(DummyPage):
        def __init__(self, width: int, height: int) -> None:
            super().__init__(width, height)
            self.set_focus = None

    items = [AdaptiveNavigationItem("tab-0", "Inicio", ft.Icons.HOME)]
    page = PageWithoutSetFocus(520, 800)
    scaffold = UniversalAdaptiveScaffold(
        navigation_items=items,
        content_builder=lambda item, idx: ft.Text(f"Contenido {item.id}-{idx}"),
        accessibility=AccessibilityPreferences(enable_captions=False),
    )

    scaffold.build(page)
    scaffold._focus_main_content()

    assert scaffold.root is not None
