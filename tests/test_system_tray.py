from fletplus.desktop.system_tray import SystemTray


def test_initialization_defaults():
    tray = SystemTray(icon="icon.png")
    assert tray.icon == "icon.png"
    assert tray.menu == []
    assert tray.visible is False


def test_show_hide_and_click():
    tray = SystemTray(icon="i", menu=["Abrir"])
    called = []

    def handler():
        called.append(True)

    tray.on_click(handler)
    tray.show()
    assert tray.visible is True

    tray._emit_click()
    assert called == [True]

    tray.hide()
    assert tray.visible is False
