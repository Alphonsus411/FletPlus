import flet as ft

from fletplus.themes.theme_manager import ThemeManager


class PageStub:
    def __init__(self):
        self.theme = None
        self.theme_mode = None
        self.bgcolor = None
        self.surface_tint_color = None
        self.updated = False

    def update(self):
        self.updated = True


def test_theme_manager_signals_emit_on_changes():
    page = PageStub()
    manager = ThemeManager(page)

    token_events: list[str] = []
    override_events: list[dict[str, dict[str, object]]] = []
    mode_events: list[bool] = []

    manager.tokens_signal.subscribe(
        lambda tokens: token_events.append(tokens["colors"]["primary"])
    )
    manager.overrides_signal.subscribe(override_events.append)
    manager.mode_signal.subscribe(mode_events.append)

    manager.set_token("colors.primary", "#445566")
    manager.set_dark_mode(True)

    assert token_events, "tokens_signal no notificó cambios"
    assert token_events[-1] == "#445566"

    assert override_events, "overrides_signal no registró overrides"
    assert override_events[-1]["colors"]["primary"] == "#445566"

    assert mode_events, "mode_signal no notificó cambios de modo"
    assert mode_events[-1] is True

    assert page.updated, "El tema debería solicitar una actualización de la página"
