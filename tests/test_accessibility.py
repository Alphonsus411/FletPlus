import flet as ft

import flet as ft

from fletplus.utils.accessibility import AccessibilityPreferences


class DummyPage:
    def __init__(self) -> None:
        self.theme = ft.Theme()
        self.locale: str | None = None
        self.updated = 0

    def update(self) -> None:
        self.updated += 1


def test_accessibility_preferences_apply_high_contrast_theme():
    page = DummyPage()
    prefs = AccessibilityPreferences(
        text_scale=1.2,
        high_contrast=True,
        reduce_motion=True,
        enable_captions=True,
        tooltip_wait_ms=500,
        caption_duration_ms=6000,
        locale="es-ES",
    )

    prefs.apply(page)

    assert page.locale == "es-ES"
    assert page.theme.color_scheme.on_background == ft.Colors.WHITE
    assert page.theme.text_theme.body_medium.size == max(12, int(14 * 1.2))
    assert page.theme.tooltip_theme.wait_duration == 500
    assert page.theme.page_transitions.android == ft.PageTransitionTheme.NONE
    assert page.updated == 1


def test_accessibility_preferences_default_focus_colors():
    page = DummyPage()
    prefs = AccessibilityPreferences(text_scale=1.0, high_contrast=False)

    prefs.apply(page)

    assert page.theme.focus_color == ft.Colors.BLUE_300
    assert page.theme.highlight_color == ft.Colors.BLUE_100
    assert page.theme.text_theme.body_medium.size == 14


def test_accessibility_preferences_store_tokens_on_theme_manager():
    page = DummyPage()

    class DummyThemeManager:
        def __init__(self) -> None:
            self.tokens: dict[str, dict[str, object]] = {}
            self.applied = 0

        def apply_theme(self) -> None:
            self.applied += 1

    manager = DummyThemeManager()
    prefs = AccessibilityPreferences(enable_captions=True, caption_mode="overlay")

    prefs.apply(page, manager)  # type: ignore[arg-type]

    assert manager.tokens["accessibility"]["caption_mode"] == "overlay"
    assert manager.tokens["accessibility"]["captions_enabled"] is True
    assert manager.applied == 1


def test_high_contrast_toggle_restores_base_colors():
    page = DummyPage()
    base_theme = ft.Theme()

    prefs = AccessibilityPreferences(high_contrast=True)
    prefs.apply(page)
    assert page.theme.color_scheme is not None
    assert page.theme.scaffold_bgcolor == ft.Colors.BLACK

    prefs = AccessibilityPreferences(high_contrast=False)
    prefs.apply(page)

    assert page.theme.color_scheme == base_theme.color_scheme
    assert page.theme.scaffold_bgcolor == base_theme.scaffold_bgcolor
    assert page.theme.focus_color == ft.Colors.BLUE_300
    assert page.theme.highlight_color == ft.Colors.BLUE_100


def test_reduce_motion_toggle_restores_transitions_and_preserves_theme_fields():
    page = DummyPage()
    base_theme = ft.Theme()

    prefs_on = AccessibilityPreferences(reduce_motion=True)
    prefs_on.apply(page)

    prefs_off = AccessibilityPreferences(reduce_motion=False)
    prefs_off.apply(page)

    assert page.theme.page_transitions == base_theme.page_transitions

    reference_page = DummyPage()
    reference_page.theme = ft.Theme()
    prefs_off.apply(reference_page)

    assert (
        page.theme.text_theme.body_small.size
        == reference_page.theme.text_theme.body_small.size
    )
    assert (
        page.theme.text_theme.body_medium.size
        == reference_page.theme.text_theme.body_medium.size
    )
    assert (
        page.theme.text_theme.body_large.size
        == reference_page.theme.text_theme.body_large.size
    )
    assert (
        page.theme.text_theme.title_medium.size
        == reference_page.theme.text_theme.title_medium.size
    )
    assert (
        page.theme.text_theme.title_large.size
        == reference_page.theme.text_theme.title_large.size
    )
    assert page.theme.text_theme.body_medium.color == reference_page.theme.text_theme.body_medium.color
    assert page.theme.color_scheme == reference_page.theme.color_scheme
    assert page.theme.scaffold_bgcolor == reference_page.theme.scaffold_bgcolor
    assert page.theme.focus_color == reference_page.theme.focus_color
    assert page.theme.highlight_color == reference_page.theme.highlight_color
    assert (
        page.theme.tooltip_theme.wait_duration
        == reference_page.theme.tooltip_theme.wait_duration
    )
    assert (
        page.theme.tooltip_theme.show_duration
        == reference_page.theme.tooltip_theme.show_duration
    )
    assert (
        page.theme.tooltip_theme.text_style.size
        == reference_page.theme.tooltip_theme.text_style.size
    )
    assert (
        page.theme.tooltip_theme.text_style.color
        == reference_page.theme.tooltip_theme.text_style.color
    )
