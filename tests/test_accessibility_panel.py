import flet as ft
import pytest

from fletplus.components.accessibility_panel import AccessibilityPanel
from fletplus.components.adaptive_layout import AdaptiveDestination, AdaptiveNavigationLayout
from fletplus.utils.accessibility import AccessibilityPreferences


class DummyPage:
    def __init__(self, width: int, height: int, platform: str = "windows"):
        self.width = width
        self.height = height
        self.window_width = width
        self.platform = platform
        self.on_resize = None
        self.theme = ft.Theme()
        self.update_calls: list[int] = []

    def resize(self, width: int | None = None, height: int | None = None) -> None:
        if width is not None:
            self.width = width
            self.window_width = width
        if height is not None:
            self.height = height
        if self.on_resize:
            self.on_resize(None)

    def update(self) -> None:
        self.update_calls.append(self.width)

    def set_focus(self, _control: ft.Control) -> None:
        pass


@pytest.fixture()
def page() -> DummyPage:
    return DummyPage(480, 800)


def test_accessibility_panel_updates_preferences(monkeypatch: pytest.MonkeyPatch, page: DummyPage) -> None:
    prefs = AccessibilityPreferences()
    calls: list[tuple[float, bool, bool]] = []

    def fake_apply(_page: ft.Page, _theme: object) -> None:
        calls.append((prefs.text_scale, prefs.high_contrast, prefs.enable_captions))

    monkeypatch.setattr(prefs, "apply", fake_apply, raising=False)

    panel = AccessibilityPanel(preferences=prefs)
    control = panel.build(page)
    assert control is panel.control

    panel.set_text_scale(1.4)
    panel.toggle_high_contrast(True)
    panel.toggle_captions(True)

    assert prefs.text_scale == pytest.approx(1.4)
    assert prefs.high_contrast is True
    assert prefs.enable_captions is True
    assert calls[-1] == (pytest.approx(1.4), True, True)


def test_accessibility_panel_switches_orientation(page: DummyPage) -> None:
    panel = AccessibilityPanel(preferences=AccessibilityPreferences())
    panel.build(page)
    assert panel.orientation == "column"

    page.resize(width=900)
    assert panel.orientation == "row"


def test_adaptive_layout_includes_accessibility_panel(page: DummyPage) -> None:
    prefs = AccessibilityPreferences(enable_captions=True)
    panel = AccessibilityPanel(preferences=prefs)
    destinations = [
        AdaptiveDestination(label="Inicio", icon=ft.Icons.HOME_OUTLINED),
        AdaptiveDestination(label="Perfil", icon=ft.Icons.PERSON_OUTLINED),
    ]

    def build_content(index: int, device: str) -> ft.Control:
        return ft.Text(f"{index}-{device}")

    layout = AdaptiveNavigationLayout(
        destinations,
        build_content,
        accessibility=prefs,
        accessibility_panel=panel,
    )

    root = layout.build(page)
    assert layout.accessibility_panel_control is panel.control

    # En móvil el panel aparece en la columna principal
    layout_column = root.controls[1]
    assert layout.accessibility_panel_control in layout_column.controls

    # Cambiar a escritorio redistribuye la navegación y el panel permanece visible
    page.resize(width=1200)
    assert layout.current_device == "desktop"
    layout_row = root.controls[-1]
    assert isinstance(layout_row, ft.Row)
    content_column = layout_row.controls[1]
    assert layout.accessibility_panel_control in content_column.controls
    assert panel.orientation == "row"
