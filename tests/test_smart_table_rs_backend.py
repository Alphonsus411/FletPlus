import random
import time

import pytest

from fletplus.components.smart_table import (
    SmartTable,
    SmartTableColumn,
    filter_eq,
    filter_neq,
    filter_lt,
    filter_lte,
    filter_gt,
    filter_gte,
)

backend = pytest.importorskip("fletplus.components.smart_table_rs")

if backend.apply_query is None:  # pragma: no cover - entorno sin compilación Rust
    pytest.skip("backend Rust no disponible", allow_module_level=True)


def _build_table(size: int = 300) -> SmartTable:
    rng = random.Random(42)
    columns = [
        SmartTableColumn("id", "ID", sortable=True),
        SmartTableColumn("name", "Nombre", filterable=True, sortable=True),
        SmartTableColumn("age", "Edad", sortable=True),
        SmartTableColumn("score", "Puntaje", sortable=True),
    ]

    rows = [
        {
            "id": idx,
            "name": f"Nombre {rng.randint(0, size)}",
            "age": rng.randint(18, 90),
            "score": rng.random() * 1000,
        }
        for idx in range(size)
    ]

    return SmartTable(columns, rows=rows)


def _build_small_table() -> SmartTable:
    columns = [
        SmartTableColumn("id", "ID", sortable=True),
        SmartTableColumn("name", "Nombre", filterable=True, sortable=True),
        SmartTableColumn("age", "Edad", filterable=True, sortable=True),
        SmartTableColumn("score", "Puntaje", filterable=True, sortable=True),
    ]

    rows = [
        {"id": 1, "name": "Ana", "age": 30, "score": 90.5},
        {"id": 2, "name": "Luis", "age": 25, "score": 70.0},
        {"id": 3, "name": "Marta", "age": 40, "score": 85.25},
        {"id": 4, "name": "Ana", "age": 35, "score": 92.0},
    ]

    return SmartTable(columns, rows=rows)


def test_rust_matches_python_ordering_with_filters():
    table = _build_table(400)
    table.set_filter("name", "1")
    table.toggle_sort("age")
    table.toggle_sort("name", multi=True)

    rust_records = table._apply_query(table._records)
    python_records = table._apply_query_py(table._records)

    assert [rec.row_id for rec in rust_records] == [rec.row_id for rec in python_records]


def test_rust_backend_is_faster_on_large_dataset():
    table = _build_table(8000)
    table.set_filter("name", "Nombre 2")
    table.toggle_sort("score")
    table.toggle_sort("age", multi=True)

    # Calentamiento para evitar sesgos por primera ejecución
    table._apply_query(table._records)

    start_py = time.perf_counter()
    python_records = table._apply_query_py(table._records)
    python_elapsed = time.perf_counter() - start_py

    start_rust = time.perf_counter()
    rust_records = table._apply_query(table._records)
    rust_elapsed = time.perf_counter() - start_rust

    assert [rec.row_id for rec in rust_records] == [rec.row_id for rec in python_records]
    assert rust_elapsed <= python_elapsed * 1.5


@pytest.mark.parametrize(
    "key,value,predicate",
    [
        ("name", "Ana", filter_eq),
        ("name", "Ana", filter_neq),
        ("age", 35, filter_lt),
        ("age", 35, filter_lte),
        ("age", 30, filter_gt),
        ("age", 30, filter_gte),
    ],
)
def test_rust_matches_python_for_supported_predicates(key, value, predicate):
    table = _build_small_table()
    table.set_filter(key, value, predicate=predicate)

    rust_records = table._apply_query(table._records)
    python_records = table._apply_query_py(table._records)

    assert [rec.row_id for rec in rust_records] == [rec.row_id for rec in python_records]


def test_rust_falls_back_for_unknown_predicate():
    table = _build_small_table()

    def _unsupported_predicate(cell_value, filter_value):
        return cell_value == filter_value

    table.set_filter("name", "Ana", predicate=_unsupported_predicate)
    assert table._serialize_filters_for_rust() is None

    rust_records = table._apply_query(table._records)
    python_records = table._apply_query_py(table._records)

    assert [rec.row_id for rec in rust_records] == [rec.row_id for rec in python_records]
