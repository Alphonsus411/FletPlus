import flet as ft
import pytest

from fletplus.components.caption_overlay import CaptionOverlay


class DummyPage:
    def __init__(self) -> None:
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1


def _get_messages(control: ft.Control) -> list[ft.Control]:
    semantics = control.content
    panel = semantics.content
    messages = panel.content
    return messages.controls


def test_caption_overlay_announces_messages() -> None:
    overlay = CaptionOverlay(max_messages=2)
    page = DummyPage()
    control = overlay.build(page)

    overlay.announce("Mensaje de prueba")
    overlay.announce("Segundo mensaje", tone="warning")

    assert control.visible is True
    messages = _get_messages(control)
    assert len(messages) == 2
    assert isinstance(messages[0], ft.Row)
    assert page.update_calls >= 2

    overlay.set_enabled(False)
    assert control.visible is False


def test_caption_overlay_clear_and_validation() -> None:
    overlay = CaptionOverlay(max_messages=1)
    page = DummyPage()
    control = overlay.build(page)

    overlay.announce("")
    assert control.visible is False

    overlay.announce("Hola")
    assert control.visible is True
    overlay.clear()
    assert control.visible is False

    with pytest.raises(ValueError):
        CaptionOverlay(max_messages=0)
