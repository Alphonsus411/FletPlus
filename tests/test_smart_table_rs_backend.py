import random
import time

import pytest

from fletplus.components.smart_table import SmartTable, SmartTableColumn

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
