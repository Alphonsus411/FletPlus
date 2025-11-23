import importlib.util
import logging
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "fletplus" / "desktop" / "notifications.py"
spec = importlib.util.spec_from_file_location("fletplus.desktop.notifications", MODULE_PATH)
notifications = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(notifications)


def test_windows_backend_called(monkeypatch):
    called = []

    def fake_win(title, body):
        called.append((title, body))
        return True

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(notifications, "_notify_windows", fake_win)
    monkeypatch.setattr(notifications, "_notify_in_page", lambda *args, **kwargs: called.append("fallback"))

    notifications.show_notification("Hola", "Mundo")
    assert called == [("Hola", "Mundo")]


def test_macos_backend_called(monkeypatch):
    called = []

    def fake_mac(title, body):
        called.append(True)
        return True

    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(notifications, "_notify_macos", fake_mac)
    monkeypatch.setattr(notifications, "_notify_in_page", lambda *args, **kwargs: called.append("fallback"))

    notifications.show_notification("Hola", "Mac")
    assert called == [True]


def test_linux_backend_called(monkeypatch):
    called = []

    def fake_linux(title, body):
        called.append(True)
        return True

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(notifications, "_notify_linux", fake_linux)
    monkeypatch.setattr(notifications, "_notify_in_page", lambda *args, **kwargs: called.append("fallback"))

    notifications.show_notification("Hola", "Linux")
    assert called == [True]


def test_fallback_to_in_page(monkeypatch):
    called = []

    def fake_win(title, body):
        return False

    def fake_fallback(title, body):
        called.append((title, body))
        return True

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(notifications, "_notify_windows", fake_win)
    monkeypatch.setattr(notifications, "_notify_in_page", fake_fallback)
    notifications.show_notification("Hola", "Fallback")
    assert called == [("Hola", "Fallback")]


def test_show_notification_logs_error(monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(notifications, "_notify_windows", boom)

    with caplog.at_level(logging.ERROR):
        notifications.show_notification("Hola", "Error")

    assert "Error al mostrar la notificación" in caplog.text
