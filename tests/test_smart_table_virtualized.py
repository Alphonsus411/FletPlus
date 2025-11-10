import asyncio

from fletplus.components.smart_table import SmartTable, SmartTableColumn


class DummyEvent:
    def __init__(self, shift_key: bool = False):
        self.shift_key = shift_key


def test_query_passed_to_provider_on_virtualized_requests():
    captured_queries = []

    columns = [
        SmartTableColumn("id", "ID", sortable=True),
        SmartTableColumn("name", "Nombre", filterable=True, sortable=True),
    ]

    async def provider(query, start, end):
        captured_queries.append(query)
        await asyncio.sleep(0)
        return [
            {"id": idx, "name": f"Item {idx}"}
            for idx in range(start, end)
        ]

    table = SmartTable(
        columns,
        virtualized=True,
        page_size=2,
        data_provider=lambda q, s, e: provider(q, s, e),
    )

    # Aplicar filtros y orden multi-columna antes de la siguiente carga
    table.set_filter("name", "Item")
    table.toggle_sort("id")
    table.toggle_sort("name", multi=True)

    pending = table.load_more(sync=False)
    asyncio.run(pending)

    assert captured_queries
    query = captured_queries[-1]
    assert "name" in query.filters
    assert len(query.sorts) == 2
