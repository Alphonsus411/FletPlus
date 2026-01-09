from __future__ import annotations

import pytest

from fletplus.components.command_palette_rs import (
    filter_commands_python,
    native_filter_commands,
)


@pytest.mark.skipif(native_filter_commands is None, reason="Extensión nativa no disponible")
@pytest.mark.parametrize(
    "names,query",
    [
        (["Abrir", "Cerrar", "Save File", "search", "Lista"], ""),
        (["Abrir", "Cerrar", "Save File", "search", "Lista"], "sa"),
        (["Abrir", "Cerrar", "Save File", "search", "Lista"], "SA"),
        (["Abrir", "Cerrar", "Save File", "search", "Lista"], "ar"),
        (["Abrir", "Cerrar", "Save File", "search", "Lista"], "LIST"),
    ],
)
def test_native_filter_matches_python(names: list[str], query: str) -> None:
    assert native_filter_commands(names, query) == filter_commands_python(names, query)
