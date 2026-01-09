"""Componente de tabla con carga incremental y edición en línea.

Este módulo provee `SmartTable`, un envoltorio de ``ft.DataTable`` que
agrega las capacidades necesarias para escenarios de datos modernos:

* Carga virtualizada con proveedores síncronos o asíncronos.
* Filtros por columna con API declarativa.
* Ordenamiento multi-columna con indicadores visuales.
* Edición en línea con validaciones y callbacks de guardado.

Las estructuras auxiliares (`SmartTableColumn`, `SmartTableFilter`,
`SmartTableSort` y `SmartTableQuery`) facilitan la configuración tipada de
estas capacidades.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import importlib.util
import asyncio
import inspect
from typing import (
    Any,
    AsyncIterable,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Union,
)

import flet as ft

from fletplus.styles import Style


# ---------------------------------------------------------------------------
# Modelos declarativos
# ---------------------------------------------------------------------------


def filter_contains_ci(cell_value: Any, filter_value: Any) -> bool:
    if filter_value in ("", None):
        return True
    if cell_value is None:
        return False
    return str(filter_value).lower() in str(cell_value).lower()


def filter_eq(cell_value: Any, filter_value: Any) -> bool:
    return cell_value == filter_value


def filter_neq(cell_value: Any, filter_value: Any) -> bool:
    return cell_value != filter_value


def _filter_compare(
    comparator: Callable[[Any, Any], bool],
    cell_value: Any,
    filter_value: Any,
) -> bool:
    try:
        return comparator(cell_value, filter_value)
    except TypeError:
        return False


def filter_lt(cell_value: Any, filter_value: Any) -> bool:
    return _filter_compare(lambda left, right: left < right, cell_value, filter_value)


def filter_lte(cell_value: Any, filter_value: Any) -> bool:
    return _filter_compare(lambda left, right: left <= right, cell_value, filter_value)


def filter_gt(cell_value: Any, filter_value: Any) -> bool:
    return _filter_compare(lambda left, right: left > right, cell_value, filter_value)


def filter_gte(cell_value: Any, filter_value: Any) -> bool:
    return _filter_compare(lambda left, right: left >= right, cell_value, filter_value)


def _default_filter_predicate(cell_value: Any, filter_value: Any) -> bool:
    return filter_contains_ci(cell_value, filter_value)


_RUST_FILTER_OPERATORS: Dict[Callable[[Any, Any], bool], str] = {
    _default_filter_predicate: "contains_ci",
    filter_contains_ci: "contains_ci",
    filter_eq: "eq",
    filter_neq: "neq",
    filter_lt: "lt",
    filter_lte: "lte",
    filter_gt: "gt",
    filter_gte: "gte",
}


@dataclass(slots=True)
class SmartTableFilter:
    """Representa un filtro aplicado a una columna."""

    key: str
    value: Any
    predicate: Callable[[Any, Any], bool] = field(default=_default_filter_predicate)

    def matches(self, cell_value: Any) -> bool:
        """Indica si ``cell_value`` cumple con el filtro configurado."""

        if self.value in (None, ""):
            return True
        try:
            return bool(self.predicate(cell_value, self.value))
        except Exception:  # pragma: no cover - errores de usuario
            return False


@dataclass(slots=True)
class SmartTableSort:
    """Representa el orden aplicado a una columna."""

    key: str
    ascending: bool = True


@dataclass(slots=True)
class SmartTableQuery:
    """Consulta enviada al proveedor de datos."""

    filters: Dict[str, SmartTableFilter] = field(default_factory=dict)
    sorts: List[SmartTableSort] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Devuelve una representación serializable de la consulta."""

        return {
            "filters": {
                key: {"value": flt.value} for key, flt in self.filters.items()
            },
            "sorts": [
                {"key": sort.key, "ascending": sort.ascending}
                for sort in self.sorts
            ],
        }


@dataclass(slots=True)
class SmartTableColumn:
    """Define la configuración de una columna."""

    key: str
    label: Union[str, ft.Control]
    width: Optional[int] = None
    sortable: bool = True
    filterable: bool = False
    editable: bool = False
    cell_builder: Optional[Callable[[Any], ft.Control]] = None
    editor_builder: Optional[Callable[[Any, Callable[[Any], None]], ft.Control]] = None
    validator: Optional[Callable[[Any], None]] = None
    alignment: Optional[ft.TextAlign] = None

    def build_label(
        self,
        sort_order: Optional[int],
        ascending: Optional[bool],
    ) -> ft.Control:
        """Construye la etiqueta con indicadores de orden."""

        base_label = (
            self.label
            if isinstance(self.label, ft.Control)
            else ft.Text(str(self.label))
        )

        if sort_order is None:
            return base_label

        icon = ft.Icon(
            name=ft.Icons.ARROW_UPWARD if ascending else ft.Icons.ARROW_DOWNWARD,
            size=14,
        )
        order_badge = ft.Container(
            content=ft.Text(str(sort_order), size=12),
            padding=ft.padding.symmetric(horizontal=4, vertical=2),
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.PRIMARY),
            border_radius=6,
        )
        return ft.Row([base_label, icon, order_badge], spacing=4)


@dataclass(slots=True)
class _SmartTableRecord:
    """Contenedor interno de registros."""

    row_id: int
    values: Dict[str, Any]


# ---------------------------------------------------------------------------
# Utilidades privadas
# ---------------------------------------------------------------------------


def _extract_value(control: Any) -> Any:
    """Intenta obtener un valor comparable desde un control de Flet."""

    if isinstance(control, ft.Control):
        for attr in ("value", "label", "text"):
            if hasattr(control, attr):
                return getattr(control, attr)
        # Componentes complejos
        if hasattr(control, "controls") and isinstance(control.controls, list):
            return " ".join(filter(None, map(_extract_value, control.controls)))
    return control


def _default_cell(value: Any) -> ft.Control:
    """Control por defecto de una celda."""

    if isinstance(value, ft.Control):
        return value
    return ft.Text("" if value is None else str(value))


def _default_editor(
    value: Any,
    on_changed: Callable[[Any], None],
) -> ft.Control:
    """Editor por defecto para celdas editables."""

    return ft.TextField(value="" if value is None else str(value), on_change=lambda e: on_changed(e.control.value))


def _ensure_awaitable_result(result: Any) -> Awaitable:
    """Normaliza resultados de proveedores asíncronos."""

    if inspect.isawaitable(result):
        return result  # type: ignore[return-value]

    if isinstance(result, AsyncIterable):

        async def consume() -> List[Any]:
            return [item async for item in result]

        return consume()

    raise TypeError("El proveedor asíncrono debe devolver un awaitable o AsyncIterable")


def _run_async(awaitable: Awaitable[Any]) -> Any:
    """Ejecuta un awaitable respetando el estado del event loop."""

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    if loop.is_running():
        future = asyncio.ensure_future(awaitable)
        # Para entornos donde no podemos bloquear, se devuelve la tarea.
        # Flet actualizará la vista cuando la tarea finalice.
        return future

    return loop.run_until_complete(awaitable)


# ---------------------------------------------------------------------------
# Componente principal
# ---------------------------------------------------------------------------


def _load_rust_backend():
    spec = importlib.util.find_spec("fletplus.components.smart_table_rs")
    if spec is None:
        return None
    module = importlib.import_module("fletplus.components.smart_table_rs")
    if (
        getattr(module, "apply_query", None) is None
        and getattr(module, "apply_query_ids", None) is None
    ):
        return None
    return module


_SMART_TABLE_RS = _load_rust_backend()


class SmartTable:
    """Tabla enriquecida con virtualización, filtros y edición."""

    def __init__(
        self,
        columns: Sequence[Union[SmartTableColumn, str, Mapping[str, Any]]],
        rows: Optional[Sequence[Union[Mapping[str, Any], ft.DataRow]]] = None,
        *,
        page_size: int = 50,
        virtualized: bool = False,
        data_provider: Optional[
            Callable[[SmartTableQuery, int, int], Union[Iterable[Mapping[str, Any]], Awaitable[Iterable[Mapping[str, Any]]], AsyncIterable[Mapping[str, Any]]]]
        ] = None,
        total_rows: Optional[int] = None,
        style: Optional[Style] = None,
        on_save: Optional[Callable[[MutableMapping[str, Any]], Union[None, Awaitable[None]]]] = None,
        auto_load: bool = True,
    ) -> None:
        self.columns: List[SmartTableColumn] = [
            self._normalize_column(col) for col in columns
        ]
        self.page_size = max(page_size, 1)
        self.virtualized = virtualized or data_provider is not None
        self.data_provider = data_provider
        self.total_rows = total_rows
        self.style = style
        self.on_save = on_save
        self.auto_load = auto_load

        self._filters: Dict[str, SmartTableFilter] = {}
        self._sorts: List[SmartTableSort] = []
        self._records: List[_SmartTableRecord] = []
        self._next_row_id = 0
        self._exhausted = False
        self._editing_rows: set[int] = set()
        self._edit_buffers: Dict[int, Dict[str, Any]] = {}
        self._table: Optional[ft.DataTable] = None
        self._container: Optional[ft.Control] = None

        if rows:
            self._ingest_rows(rows)
        if self.virtualized and self.auto_load:
            self.load_more(sync=True)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        """Construye la tabla con filtros y acciones."""

        self._table = ft.DataTable(
            columns=self._build_columns(),
            rows=self._build_rows_view(),
            heading_row_height=48,
            divider_thickness=1,
        )

        controls: List[ft.Control] = []
        filters_row = self._build_filters_row()
        if filters_row is not None:
            controls.append(filters_row)
        controls.append(self._table)

        self._container = ft.Column(controls, spacing=12, expand=True)
        wrapped: ft.Control = self._container
        if self.style:
            wrapped = self.style.apply(wrapped)
        return wrapped

    def refresh(self) -> None:
        """Actualiza la tabla tras cambios en filtros u ordenamiento."""

        if self._table is None:
            return
        self._table.columns = self._build_columns()
        self._table.rows = self._build_rows_view()

    def set_filter(self, key: str, value: Any, predicate: Optional[Callable[[Any, Any], bool]] = None) -> None:
        """Configura un filtro para la columna ``key``."""

        column = self._find_column(key)
        if column is None or not column.filterable:
            raise KeyError(f"La columna '{key}' no admite filtros")

        self._filters[key] = SmartTableFilter(
            key=key,
            value=value,
            predicate=predicate or _default_filter_predicate,
        )
        self.refresh()

    def clear_filter(self, key: str) -> None:
        """Elimina el filtro de una columna."""

        if key in self._filters:
            self._filters.pop(key)
            self.refresh()

    def toggle_sort(self, key: str, multi: bool = False) -> None:
        """Alterna el estado de ordenamiento para ``key``."""

        column = self._find_column(key)
        if column is None or not column.sortable:
            raise KeyError(f"La columna '{key}' no admite ordenamiento")

        existing = next((s for s in self._sorts if s.key == key), None)
        if existing:
            if existing.ascending:
                existing.ascending = False
            else:
                self._sorts.remove(existing)
        else:
            if not multi:
                self._sorts.clear()
            self._sorts.append(SmartTableSort(key=key, ascending=True))
        self.refresh()

    def clear_sorts(self) -> None:
        """Elimina todos los ordenamientos."""

        if self._sorts:
            self._sorts.clear()
            self.refresh()

    def load_more(self, *, sync: bool = False) -> Optional[Awaitable[Any]]:
        """Solicita el siguiente bloque de datos al proveedor."""

        if not self.virtualized or self._exhausted or self.data_provider is None:
            return None

        start = len(self._records)
        end = start + self.page_size

        query = self._build_query()
        result = self.data_provider(query, start, end)

        if inspect.isawaitable(result) or isinstance(result, AsyncIterable):
            awaitable = _ensure_awaitable_result(result)

            async def consume_async() -> None:
                batch = await awaitable
                self._ingest_rows(batch)
                if self.total_rows is not None and len(self._records) >= self.total_rows:
                    self._exhausted = True
                self.refresh()

            if sync:
                _run_async(consume_async())
                return None
            return consume_async()

        batch = list(result) if isinstance(result, Iterable) else []
        self._ingest_rows(batch)
        if self.total_rows is not None and len(self._records) >= self.total_rows:
            self._exhausted = True
        self.refresh()
        return None

    def start_edit(self, row_id: int) -> None:
        """Activa el modo edición para una fila."""

        if row_id not in {record.row_id for record in self._records}:
            raise KeyError(f"Fila '{row_id}' inexistente")
        self._editing_rows.add(row_id)
        self._edit_buffers.setdefault(row_id, {}).clear()
        self.refresh()

    def cancel_edit(self, row_id: int) -> None:
        """Cancela la edición de una fila."""

        self._editing_rows.discard(row_id)
        self._edit_buffers.pop(row_id, None)
        self.refresh()

    def save_row(self, row_id: int) -> Optional[Awaitable[None]]:
        """Valida y guarda los cambios en una fila."""

        record = next((r for r in self._records if r.row_id == row_id), None)
        if record is None:
            raise KeyError(f"Fila '{row_id}' inexistente")

        updates = self._edit_buffers.get(row_id, {})
        if not updates:
            self.cancel_edit(row_id)
            return None

        # Validaciones por columna
        for column in self.columns:
            if not column.editable or column.key not in updates:
                continue
            validator = column.validator
            if validator:
                validator(updates[column.key])

        record.values.update(updates)
        self._editing_rows.discard(row_id)
        self._edit_buffers.pop(row_id, None)

        if self.on_save is None:
            self.refresh()
            return None

        maybe = self.on_save(record.values)
        if inspect.isawaitable(maybe):

            async def wait_and_refresh() -> None:
                await maybe
                self.refresh()

            return wait_and_refresh()

        self.refresh()
        return None

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _normalize_column(
        self, column: Union[SmartTableColumn, str, Mapping[str, Any]]
    ) -> SmartTableColumn:
        if isinstance(column, SmartTableColumn):
            return column
        if isinstance(column, Mapping):
            return SmartTableColumn(**column)
        return SmartTableColumn(key=str(column), label=str(column))

    def _ingest_rows(
        self, rows: Sequence[Union[Mapping[str, Any], ft.DataRow]]
    ) -> None:
        if not rows:
            self._exhausted = True
            return

        new_records: List[_SmartTableRecord] = []
        for item in rows:
            if isinstance(item, ft.DataRow):
                values = {
                    column.key: _extract_value(cell.content)
                    for column, cell in zip(self.columns, item.cells)
                }
            elif isinstance(item, Mapping):
                values = dict(item)
            else:
                raise TypeError(
                    "Cada fila debe ser Mapping[str, Any] o ft.DataRow"
                )

            record = _SmartTableRecord(row_id=self._next_row_id, values=values)
            self._next_row_id += 1
            new_records.append(record)

        self._records.extend(new_records)

    def _build_rows_view(self) -> List[ft.DataRow]:
        records = self._apply_query(self._records)
        view: List[ft.DataRow] = []
        for record in records:
            row = self._build_row(record)
            view.append(row)
        return view

    def _build_row(self, record: _SmartTableRecord) -> ft.DataRow:
        cells: List[ft.DataCell] = []
        edit_mode = record.row_id in self._editing_rows
        buffer = self._edit_buffers.setdefault(record.row_id, {})
        for column in self.columns:
            value = buffer.get(column.key, record.values.get(column.key))
            control: ft.Control
            if column.editable and edit_mode:
                builder = column.editor_builder or _default_editor

                def on_changed(new_value: Any, *, key=column.key, row=record.row_id) -> None:
                    self._edit_buffers[row][key] = new_value

                control = builder(value, on_changed)
            else:
                builder = column.cell_builder or _default_cell
                control = builder(value)

            if column.alignment and isinstance(control, ft.Text):
                control.text_align = column.alignment
            cells.append(ft.DataCell(control))

        if any(column.editable for column in self.columns) or self.on_save:
            action_button: ft.Control
            if edit_mode:
                action_button = ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.CHECK,
                            tooltip="Guardar",
                            on_click=lambda _=None, row=record.row_id: self._resolve_save(row),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            tooltip="Cancelar",
                            on_click=lambda _=None, row=record.row_id: self.cancel_edit(row),
                        ),
                    ],
                    spacing=4,
                )
            else:
                action_button = ft.IconButton(
                    icon=ft.Icons.EDIT,
                    tooltip="Editar",
                    on_click=lambda _=None, row=record.row_id: self.start_edit(row),
                )
            cells.append(ft.DataCell(action_button))

        return ft.DataRow(cells=cells, selected=edit_mode)

    def _resolve_save(self, row_id: int) -> None:
        maybe = self.save_row(row_id)
        if inspect.isawaitable(maybe):
            _run_async(maybe)

    def _apply_query(
        self, records: Sequence[_SmartTableRecord]
    ) -> List[_SmartTableRecord]:
        rust_filters, py_filters = self._serialize_filters_for_rust()
        rust_sorts = [
            {"key": sort.key, "ascending": sort.ascending}
            for sort in self._sorts
        ]
        if _SMART_TABLE_RS is not None and (rust_filters or rust_sorts):
            payload = [(record.row_id, record.values) for record in records]
            try:
                if not py_filters and getattr(_SMART_TABLE_RS, "apply_query_ids", None):
                    ordered_ids = _SMART_TABLE_RS.apply_query_ids(
                        payload, rust_filters, rust_sorts
                    )
                else:
                    ordered_ids = _SMART_TABLE_RS.apply_query(
                        payload, rust_filters, rust_sorts
                    )
            except Exception:
                ordered_ids = None
            else:
                if ordered_ids is not None:
                    index = {record.row_id: record for record in records}
                    ordered_records = [
                        index[row_id] for row_id in ordered_ids if row_id in index
                    ]
                    if py_filters:
                        # Filtrado híbrido: las reglas en Python preservan el orden ya
                        # calculado por Rust.
                        return self._apply_unsupported_filters_py(
                            ordered_records, py_filters
                        )
                    return ordered_records

        return self._apply_query_py(records)

    def _serialize_filters_for_rust(
        self,
    ) -> tuple[List[Dict[str, Any]], List[SmartTableFilter]]:
        rust_filters: List[Dict[str, Any]] = []
        py_filters: List[SmartTableFilter] = []
        for key, flt in self._filters.items():
            op = _RUST_FILTER_OPERATORS.get(flt.predicate)
            if op is None:
                py_filters.append(flt)
                continue
            rust_filters.append({"key": key, "value": flt.value, "op": op})
        return rust_filters, py_filters

    def _apply_unsupported_filters_py(
        self,
        records: Sequence[_SmartTableRecord],
        filters: Sequence[SmartTableFilter],
    ) -> List[_SmartTableRecord]:
        filtered_records = list(records)
        for flt in filters:
            filtered_records = [
                record
                for record in filtered_records
                if flt.matches(record.values.get(flt.key))
            ]
        return filtered_records

    def _apply_query_py(
        self, records: Sequence[_SmartTableRecord]
    ) -> List[_SmartTableRecord]:
        filtered = [
            record
            for record in records
            if all(
                flt.matches(record.values.get(key))
                for key, flt in self._filters.items()
            )
        ]

        if not self._sorts:
            return filtered

        def sort_key_factory(sort: SmartTableSort) -> Callable[[
            _SmartTableRecord
        ], Any]:
            def key(record: _SmartTableRecord) -> Any:
                value = record.values.get(sort.key)
                return (value is None, value)

            return key

        sorted_records = list(filtered)
        for index, sort in enumerate(reversed(self._sorts)):
            key_fn = sort_key_factory(sort)
            sorted_records.sort(key=key_fn, reverse=not sort.ascending)
        return sorted_records

    def _build_columns(self) -> List[ft.DataColumn]:
        columns: List[ft.DataColumn] = []
        for column in self.columns:
            sort_index = next(
                (idx for idx, sort in enumerate(self._sorts, start=1) if sort.key == column.key),
                None,
            )
            ascending = None
            if sort_index is not None:
                sort = next(s for s in self._sorts if s.key == column.key)
                ascending = sort.ascending

            label = column.build_label(sort_index, ascending)
            columns.append(
                ft.DataColumn(
                    label=label,
                    on_sort=(
                        self._make_sort_handler(column)
                        if column.sortable
                        else None
                    ),
                    numeric=False,
                )
            )

        if any(column.editable for column in self.columns) or self.on_save:
            columns.append(
                ft.DataColumn(
                    label=ft.Text("Acciones"),
                    on_sort=None,
                )
            )
        return columns

    def _build_filters_row(self) -> Optional[ft.Control]:
        if not any(column.filterable for column in self.columns):
            return None

        fields: List[ft.Control] = []
        for column in self.columns:
            if not column.filterable:
                fields.append(ft.Container(width=column.width))
                continue

            current = self._filters.get(column.key)
            field = ft.TextField(
                value="" if current is None else current.value,
                hint_text=f"Filtrar {column.label if isinstance(column.label, str) else ''}",
                on_change=lambda e, key=column.key: self._handle_filter_change(key, e.control.value),
            )
            fields.append(field)

        return ft.Row(fields, alignment=ft.MainAxisAlignment.START)

    def _handle_filter_change(self, key: str, value: Any) -> None:
        if value in ("", None):
            self.clear_filter(key)
            return
        self.set_filter(key, value)

    def _make_sort_handler(self, column: SmartTableColumn) -> Callable[[Any], None]:
        def handler(event: Any) -> None:
            multi = bool(getattr(event, "shift_key", False))
            self.toggle_sort(column.key, multi=multi)

        return handler

    def _build_query(self) -> SmartTableQuery:
        return SmartTableQuery(filters=dict(self._filters), sorts=list(self._sorts))

    def _find_column(self, key: str) -> Optional[SmartTableColumn]:
        return next((column for column in self.columns if column.key == key), None)


__all__ = [
    "SmartTable",
    "SmartTableColumn",
    "SmartTableFilter",
    "SmartTableSort",
    "SmartTableQuery",
]
