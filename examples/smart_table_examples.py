"""Ejemplos interactivos para la `SmartTable` avanzada."""

from __future__ import annotations

import asyncio
import random
import flet as ft

from examples import ensure_project_root

ensure_project_root()

from fletplus.components.smart_table import SmartTable, SmartTableColumn


async def async_people_provider(query, start: int, end: int):
    """Proveedor que simula una API con filtros y ordenamiento."""

    await asyncio.sleep(0.05)

    base = [
        {
            "id": idx,
            "name": f"Persona {idx}",
            "role": random.choice(["Admin", "Editor", "Visitante"]),
            "email": f"persona{idx}@ejemplo.com",
        }
        for idx in range(start, end)
    ]

    # Aplicar filtros básicos en memoria para la demo
    for flt in query.filters.values():
        base = [item for item in base if flt.matches(item.get(flt.key))]

    # Ordenamiento estable según la consulta
    for sort in reversed(query.sorts):
        base.sort(key=lambda item: item.get(sort.key), reverse=not sort.ascending)

    return base


def main(page: ft.Page) -> None:
    page.title = "SmartTable virtualizada"
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START

    events_log = ft.ListView(height=160, spacing=4)

    def handle_save(data: dict[str, str]) -> None:
        events_log.controls.append(ft.Text(f"Fila guardada: {data!r}"))
        page.update()

    def role_editor(value: str, on_changed):
        return ft.Dropdown(
            value=value,
            options=[
                ft.dropdown.Option("Admin"),
                ft.dropdown.Option("Editor"),
                ft.dropdown.Option("Visitante"),
            ],
            on_change=lambda e: on_changed(e.control.value),
            width=160,
        )

    columns = [
        SmartTableColumn("id", "ID", sortable=True),
        SmartTableColumn("name", "Nombre", filterable=True, sortable=True, editable=True),
        SmartTableColumn(
            "role",
            "Rol",
            filterable=True,
            sortable=True,
            editable=True,
            editor_builder=role_editor,
        ),
        SmartTableColumn("email", "Correo", filterable=True),
    ]

    table = SmartTable(
        columns,
        virtualized=True,
        page_size=25,
        data_provider=lambda q, s, e: async_people_provider(q, s, e),
        on_save=handle_save,
    )

    table_view = table.build()

    async def load_more_async(_: ft.ControlEvent) -> None:
        pending = table.load_more(sync=False)
        if pending is not None:
            await pending
            page.update()

    load_more_button = ft.ElevatedButton("Cargar más", on_click=load_more_async)

    page.add(
        ft.Text(
            "La tabla admite scroll infinito, filtros por columna, orden multi-columna y edición en línea.",
            size=16,
        ),
        table_view,
        ft.Row([load_more_button]),
        ft.Text("Eventos"),
        events_log,
    )


if __name__ == "__main__":
    ft.app(main)
