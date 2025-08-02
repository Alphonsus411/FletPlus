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
