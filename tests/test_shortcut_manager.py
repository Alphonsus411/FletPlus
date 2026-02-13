from fletplus.utils.shortcut_manager import ShortcutManager


class DummyPage:
    def __init__(self):
        self.on_keyboard_event = None


def test_shortcut_manager_executes_callback():
    page = DummyPage()
    manager = ShortcutManager(page)
    called = []
    manager.register("k", lambda: called.append("ok"), ctrl=True)

    class Event:
        def __init__(self):
            self.key = "k"
            self.ctrl = True
            self.shift = False
            self.alt = False

    manager._handle_event(Event())
    assert called == ["ok"]


def test_shortcut_manager_preserves_existing_handler():
    events = []

    class Event:
        def __init__(self, key: str, ctrl: bool = False):
            self.key = key
            self.ctrl = ctrl
            self.shift = False
            self.alt = False

    def previous_handler(event):
        events.append(("previous", event.key))

    page = DummyPage()
    page.on_keyboard_event = previous_handler

    manager = ShortcutManager(page)
    manager.register("x", lambda: events.append(("shortcut", "x")))

    manager._handle_event(Event("x"))

    assert events == [("shortcut", "x"), ("previous", "x")]


def test_dispose_restores_previous_handler_and_disables_shortcuts():
    events = []

    class Event:
        def __init__(self, key: str):
            self.key = key
            self.ctrl = False
            self.shift = False
            self.alt = False

    def previous_handler(event):
        events.append(("previous", event.key))

    page = DummyPage()
    page.on_keyboard_event = previous_handler

    manager = ShortcutManager(page)
    manager.register("x", lambda: events.append(("shortcut", "x")))

    manager.dispose()

    assert page.on_keyboard_event is previous_handler

    page.on_keyboard_event(Event("x"))
    assert events == [("previous", "x")]


def test_dispose_is_idempotent():
    page = DummyPage()
    manager = ShortcutManager(page)

    manager.dispose()
    manager.dispose()

    assert page.on_keyboard_event is None
