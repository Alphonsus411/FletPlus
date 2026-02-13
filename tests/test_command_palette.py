import logging

from fletplus.components import command_palette as command_palette_module
from fletplus.components.command_palette import CommandPalette


def test_command_palette_filters_and_executes():
    called = []
    palette = CommandPalette({"Saludar": lambda: called.append("hola"), "Adios": lambda: called.append("bye")})

    palette.search.value = "sal"
    palette._on_search(None)
    assert len(palette.list_view.controls) == 1
    tile = palette.list_view.controls[0]
    tile.on_click(None)
    assert called == ["hola"]


def test_command_palette_ignores_invalid_indices_and_deduplicates(monkeypatch, caplog):
    called = []
    palette = CommandPalette(
        {
            "Saludar": lambda: called.append("hola"),
            "Adios": lambda: called.append("bye"),
        }
    )

    def fake_filter_commands(_names, _query):
        return [0, 99, "1", -1, 0, 1]

    monkeypatch.setattr(command_palette_module, "filter_commands", fake_filter_commands)

    with caplog.at_level(logging.WARNING):
        palette.search.value = "x"
        palette.refresh()

    assert [name for name, _ in palette.filtered] == ["Saludar", "Adios"]
    assert len(palette.list_view.controls) == 2
    assert "índice fuera de rango" in caplog.text.lower()
    assert "índice no entero" in caplog.text.lower()

    tile = palette.list_view.controls[0]
    tile.on_click(None)
    assert called == ["hola"]


def test_command_palette_dispose_unsubscribes_all(caplog):
    palette = CommandPalette({})
    calls = []

    def unsubscribe_ok_1():
        calls.append("ok1")

    def unsubscribe_error():
        calls.append("error")
        raise RuntimeError("boom")

    def unsubscribe_ok_2():
        calls.append("ok2")

    palette._subscriptions = [unsubscribe_ok_1, unsubscribe_error, unsubscribe_ok_2]

    with caplog.at_level(logging.ERROR):
        palette.dispose()

    assert calls == ["ok1", "error", "ok2"]
    assert palette._subscriptions == []
    assert palette._disposed is True
    assert "error al cancelar la subscripción de commandpalette" in caplog.text.lower()


def test_command_palette_dispose_is_idempotent():
    palette = CommandPalette({})
    calls = []

    def unsubscribe_once():
        calls.append("called")

    palette._subscriptions = [unsubscribe_once]

    palette.dispose()
    palette.dispose()

    assert calls == ["called"]
    assert palette._subscriptions == []
    assert palette._disposed is True
