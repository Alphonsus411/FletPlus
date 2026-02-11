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


def test_load_more_sync_true_raises_when_loop_is_running():
    async def scenario():
        columns = [SmartTableColumn("id", "ID")]

        async def provider(query, start, end):
            await asyncio.sleep(0)
            return [{"id": idx} for idx in range(start, end)]

        table = SmartTable(
            columns,
            virtualized=True,
            auto_load=False,
            page_size=1,
            data_provider=lambda q, s, e: provider(q, s, e),
        )

        try:
            table.load_more(sync=True)
        except RuntimeError as exc:
            assert "sync=True" in str(exc)
        else:
            raise AssertionError("Se esperaba RuntimeError con loop activo")

    asyncio.run(scenario())


def test_autoload_and_resolve_save_capture_async_exceptions_without_orphans():
    async def scenario():
        captured_contexts = []

        async def failing_provider(query, start, end):
            await asyncio.sleep(0)
            raise ValueError("provider exploded")

        loop = asyncio.get_running_loop()
        previous_handler = loop.get_exception_handler()

        def exception_handler(loop, context):
            captured_contexts.append(context)

        loop.set_exception_handler(exception_handler)

        try:
            SmartTable(
                [SmartTableColumn("id", "ID")],
                virtualized=True,
                page_size=1,
                data_provider=lambda q, s, e: failing_provider(q, s, e),
            )

            table = SmartTable(
                [SmartTableColumn("id", "ID", editable=True)],
                rows=[{"id": 1}],
                on_save=lambda _: failing_provider(None, 0, 1),
            )
            table.build()
            row_id = table._records[0].row_id
            table.start_edit(row_id)
            table._edit_buffers[row_id]["id"] = 2
            table._resolve_save(row_id)
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            await asyncio.sleep(0)

            messages = [ctx.get("message", "") for ctx in captured_contexts]
            assert any(
                "carga inicial" in message or "load_more" in message
                for message in messages
            )
            assert any("save_row" in message for message in messages)
        finally:
            loop.set_exception_handler(previous_handler)

    asyncio.run(scenario())


def test_autoload_with_running_loop_does_not_duplicate_provider_calls_for_tasks():
    async def scenario():
        calls = 0
        call_done = asyncio.Event()

        async def provider(query, start, end):
            nonlocal calls
            calls += 1
            await asyncio.sleep(0)
            call_done.set()
            return [{"id": idx} for idx in range(start, end)]

        table = SmartTable(
            [SmartTableColumn("id", "ID")],
            virtualized=True,
            page_size=1,
            data_provider=lambda q, s, e: asyncio.create_task(provider(q, s, e)),
        )

        await asyncio.wait_for(call_done.wait(), timeout=1)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert calls == 1
        assert len(table._records) == 1

    asyncio.run(scenario())


def test_refresh_consistency_after_sync_load_more():
    columns = [SmartTableColumn("id", "ID"), SmartTableColumn("name", "Nombre")]

    def provider(query, start, end):
        return [{"id": idx, "name": f"Item {idx}"} for idx in range(start, end)]

    table = SmartTable(
        columns,
        virtualized=True,
        auto_load=False,
        page_size=2,
        data_provider=provider,
    )
    table.build()

    table.load_more(sync=True)
    assert len(table._records) == 2
    assert table._table is not None
    assert len(table._table.rows) == 2
    assert table._table.rows[0].cells[1].content.value == "Item 0"

    table.load_more(sync=True)
    assert len(table._records) == 4
    assert len(table._table.rows) == 4
    assert table._table.rows[-1].cells[1].content.value == "Item 3"
