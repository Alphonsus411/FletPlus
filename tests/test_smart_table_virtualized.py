import flet as ft
from fletplus.components.smart_table import SmartTable


class DummyPage:
    def update(self):
        pass


class DummyControl:
    page = DummyPage()


class DummyEvent:
    def __init__(self, column_index):
        self.column_index = column_index
        self.control = DummyControl()


def test_virtualized_with_list_provider():
    columns = ["ID"]
    calls = []

    def provider(start, end):
        calls.append((start, end))
        return [
            ft.DataRow(cells=[ft.DataCell(ft.Text(str(i)))])
            for i in range(start, end)
        ]

    table = SmartTable(
        columns,
        virtualized=True,
        data_provider=provider,
        total_rows=50,
        page_size=10,
    )

    rows = table._get_page_rows()
    assert len(rows) == 10
    assert rows[0].cells[0].content.value == "0"
    assert calls == [(0, 10)]

    table._next_page(DummyEvent(0))
    rows = table._get_page_rows()
    assert rows[0].cells[0].content.value == "10"
    assert calls == [(0, 10), (10, 20)]


def test_virtualized_with_generator_provider():
    columns = ["ID"]

    def provider(start, end):
        for i in range(start, end):
            yield ft.DataRow(cells=[ft.DataCell(ft.Text(str(i)))])

    table = SmartTable(
        columns,
        virtualized=True,
        data_provider=provider,
        total_rows=30,
        page_size=10,
    )

    rows = table._get_page_rows()
    assert len(rows) == 10
    assert rows[-1].cells[0].content.value == "9"


def test_virtualized_performance_calls():
    columns = ["ID"]
    call_count = 0
    ranges = []

    def provider(start, end):
        nonlocal call_count
        call_count += 1
        ranges.append((start, end))
        for i in range(start, end):
            yield ft.DataRow(cells=[ft.DataCell(ft.Text(str(i)))])

    table = SmartTable(
        columns,
        virtualized=True,
        data_provider=provider,
        total_rows=1000,
        page_size=100,
    )

    table._get_page_rows()
    table._next_page(DummyEvent(0))
    table._get_page_rows()

    assert call_count == 2
    assert ranges == [(0, 100), (100, 200)]
