import flet as ft

from fletplus.themes.theme_manager import ThemeManager


class EventHookStub:
    def __init__(self):
        self._callbacks: list = []

    def subscribe(self, callback):
        self._callbacks.append(callback)

        def unsubscribe():
            try:
                self._callbacks.remove(callback)
            except ValueError:
                pass

        return unsubscribe

    def trigger(self, event):
        for callback in list(self._callbacks):
            callback(event)


class PageStub:
    def __init__(self):
        self.theme = None
        self.theme_mode = None
        self.bgcolor = None
        self.surface_tint_color = None
        self.updated = False
        self.platform_brightness = ft.Brightness.LIGHT
        self.platform_theme = ft.ThemeMode.LIGHT
        self.on_platform_brightness_change = EventHookStub()
        self.on_platform_theme_change = EventHookStub()

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


def test_theme_manager_detects_initial_platform_brightness():
    page = PageStub()
    page.platform_brightness = ft.Brightness.DARK
    page.platform_theme = ft.ThemeMode.DARK

    manager = ThemeManager(page)

    assert manager.dark_mode is True
    assert manager.mode_signal.value is True


def test_theme_manager_updates_on_platform_brightness_change():
    page = PageStub()
    page.platform_brightness = ft.Brightness.LIGHT

    manager = ThemeManager(page)

    token_events: list[dict[str, dict[str, object]]] = []
    mode_events: list[bool] = []

    manager.tokens_signal.subscribe(token_events.append)
    manager.mode_signal.subscribe(mode_events.append)

    page.updated = False
    page.platform_brightness = ft.Brightness.DARK

    class Event:
        brightness = ft.Brightness.DARK
        data = "dark"

    page.on_platform_brightness_change.trigger(Event())

    assert manager.dark_mode is True
    assert mode_events, "mode_signal no notificó el cambio del sistema"
    assert token_events, "tokens_signal debería emitir un snapshot para refrescar controles"
    assert page.updated, "set_dark_mode debería invocar page.update()"


def test_theme_manager_can_disable_platform_tracking():
    page = PageStub()
    page.platform_brightness = ft.Brightness.DARK

    manager = ThemeManager(page)
    manager.set_follow_platform_theme(False)

    token_events: list = []
    mode_events: list = []
    manager.tokens_signal.subscribe(token_events.append)
    manager.mode_signal.subscribe(mode_events.append)

    manager.set_dark_mode(False)
    assert manager.dark_mode is False

    page.updated = False
    page.platform_brightness = ft.Brightness.DARK

    class Event:
        brightness = ft.Brightness.DARK

    page.on_platform_brightness_change.trigger(Event())

    assert manager.dark_mode is False
    assert len(token_events) == 1, "No deberían emitirse tokens al ignorar el evento"
    assert len(mode_events) == 1, "El modo no debería cambiar cuando el seguimiento está desactivado"
    assert page.updated is False
