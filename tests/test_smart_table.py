import asyncio

import flet as ft

from fletplus.components.smart_table import (
    SmartTable,
    SmartTableColumn,
    SmartTableFilter,
    SmartTableQuery,
    SmartTableSort,
)


def test_smart_table_builds_with_filters_and_multi_sort():
    columns = [
        SmartTableColumn("id", "ID", sortable=True),
        SmartTableColumn("name", "Nombre", sortable=True, filterable=True),
        SmartTableColumn("age", "Edad", sortable=True),
    ]

    rows = [
        {"id": 2, "name": "Bob", "age": 25},
        {"id": 1, "name": "Alice", "age": 31},
        {"id": 3, "name": "Charlie", "age": 31},
    ]

    table = SmartTable(columns, rows=rows)
    built = table.build()

    assert isinstance(built, ft.Column)
    assert table._table is not None
    assert len(table._table.rows) == 3

    table.set_filter("name", "a")
    assert len(table._table.rows) == 2

    table.toggle_sort("age")
    table.toggle_sort("name", multi=True)

    first_row = table._table.rows[0]
    assert first_row.cells[0].content.value == "1"
    second_row = table._table.rows[1]
    assert second_row.cells[0].content.value == "3"

    # Indicadores de orden multi-columna
    assert isinstance(table._table.columns[2].label, ft.Row)
    assert isinstance(table._table.columns[1].label, ft.Row)


def test_inline_editing_with_validation_and_callback():
    saved_rows = []

    def email_validator(value: str) -> None:
        if "@" not in value:
            raise ValueError("Correo inválido")

    def on_save(data):
        saved_rows.append(data.copy())

    columns = [
        SmartTableColumn("id", "ID"),
        SmartTableColumn("email", "Correo", editable=True, validator=email_validator),
    ]

    rows = [{"id": 1, "email": "old@example.com"}]
    table = SmartTable(columns, rows=rows, on_save=on_save)
    table.build()

    row_id = table._records[0].row_id
    table.start_edit(row_id)

    table._edit_buffers[row_id]["email"] = "new@example.com"
    table.save_row(row_id)

    assert saved_rows[0]["email"] == "new@example.com"
    assert table._table.rows[0].selected is False


def test_toggle_sort_cycle_removes_sort():
    columns = [SmartTableColumn("id", "ID", sortable=True)]
    rows = [{"id": 2}, {"id": 1}]
    table = SmartTable(columns, rows=rows)
    table.build()

    table.toggle_sort("id")
    assert table._sorts[0].ascending is True
    table.toggle_sort("id")
    assert table._sorts[0].ascending is False
    table.toggle_sort("id")
    assert not table._sorts


def test_set_filter_requires_filterable_column():
    columns = [SmartTableColumn("id", "ID", sortable=True, filterable=False)]
    table = SmartTable(columns, rows=[{"id": 1}])
    table.build()

    try:
        table.set_filter("id", "1")
    except KeyError:
        pass
    else:
        raise AssertionError("Se esperaba KeyError al filtrar columna no habilitada")


def test_virtualized_async_provider_and_manual_refresh():
    columns = [
        SmartTableColumn("id", "ID"),
        SmartTableColumn("value", "Valor", filterable=True),
    ]

    async def provider(query: SmartTableQuery, start: int, end: int):
        await asyncio.sleep(0)
        return [
            {"id": idx, "value": f"Row {idx}"}
            for idx in range(start, end)
        ]

    table = SmartTable(
        columns,
        virtualized=True,
        data_provider=lambda q, s, e: provider(q, s, e),
        page_size=3,
    )

    table.build()
    assert table._records  # carga automática inicial
    assert len(table._records) == 3

    pending = table.load_more(sync=False)
    assert pending is not None
    asyncio.run(pending)

    assert len(table._records) == 6

    table.set_filter("value", "Row 5")
    assert len(table._table.rows) == 1
