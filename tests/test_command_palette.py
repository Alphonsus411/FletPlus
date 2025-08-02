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
