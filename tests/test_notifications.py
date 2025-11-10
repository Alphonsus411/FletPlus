import sys
import logging
import fletplus.desktop.notifications as notifications


def test_windows_backend_called(monkeypatch):
    called = []

    def fake_win(title, body):
        called.append((title, body))

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(notifications, "_notify_windows", fake_win)
    notifications.show_notification("Hola", "Mundo")
    assert called == [("Hola", "Mundo")]


def test_macos_backend_called(monkeypatch):
    called = []

    def fake_mac(title, body):
        called.append(True)

    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(notifications, "_notify_macos", fake_mac)
    notifications.show_notification("Hola", "Mac")
    assert called == [True]


def test_linux_backend_called(monkeypatch):
    called = []

    def fake_linux(title, body):
        called.append(True)

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(notifications, "_notify_linux", fake_linux)
    notifications.show_notification("Hola", "Linux")
    assert called == [True]


def test_fallback_to_in_page(monkeypatch):
    called = []

    def fake_fallback(title, body):
        called.append(True)

    monkeypatch.setattr(sys, "platform", "amiga")
    monkeypatch.setattr(notifications, "_notify_in_page", fake_fallback)
    notifications.show_notification("Hola", "Fallback")
    assert called == [True]


def test_show_notification_logs_error(monkeypatch, caplog):
    monkeypatch.setattr(sys, "platform", "win32")

    with caplog.at_level(logging.ERROR):
        notifications.show_notification("Hola", "Error")

    assert "Error al mostrar la notificación" in caplog.text
