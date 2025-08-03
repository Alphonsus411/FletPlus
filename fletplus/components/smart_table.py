import flet as ft
from typing import Callable, Optional

from fletplus.styles import Style


try:
    from collections.abc import Generator, Iterable
except ImportError:  # pragma: no cover - Python <3.10
    from typing import Generator, Iterable

class SmartTable:
    def __init__(
        self,
        columns,
        rows=None,
        sortable: bool = True,
        page_size: int = 10,
        virtualized: bool = False,
        data_provider: Optional[Callable[[int, int], Iterable]] = None,
        total_rows: Optional[int] = None,
        style: Style | None = None,
    ):
        """Inicializa una tabla inteligente.

        :param columns: Encabezados de la tabla.
        :param rows: Filas iniciales.
        :param sortable: Si permite ordenar columnas (deshabilitado en modo virtualizado).
        :param page_size: Cantidad de filas por página.
        :param virtualized: Si utiliza proveedor de datos bajo demanda.
        :param data_provider: Función que devuelve filas para un rango.
        :param total_rows: Total de filas disponibles al virtualizar. Si es ``None`` y
            la tabla está virtualizada, se asumirá ``0``.
        :param style: Estilo opcional a aplicar al contenedor de la tabla.
        """
        self.columns = columns
        self.rows = rows or []
        self.virtualized = virtualized
        self.data_provider = data_provider
        self.sortable = sortable and not virtualized
        self.page_size = page_size
        self.current_page = 0
        self.sorted_column = None
        self.sort_ascending = True

        if self.virtualized:
            self.total_rows = total_rows if total_rows is not None else 0
        else:
            self.total_rows = len(self.rows)

        self.style = style

    def build(self):
        column = ft.Column([
            ft.DataTable(
                columns=[
                    ft.DataColumn(
                        label=ft.Text(col),
                        on_sort=self._on_sort(index) if self.sortable else None,
                    )
                    for index, col in enumerate(self.columns)
                ],
                rows=self._get_page_rows(),
            ),
            ft.Row([
                ft.ElevatedButton("Anterior", on_click=self._previous_page),
                ft.ElevatedButton("Siguiente", on_click=self._next_page),
            ])
        ])

        return self.style.apply(column) if self.style else column

    def _on_sort(self, col_index):
        def handler(e):
            if self.sorted_column == col_index:
                self.sort_ascending = not self.sort_ascending
            else:
                self.sorted_column = col_index
                self.sort_ascending = True

            self.rows.sort(
                key=lambda x: x.cells[col_index].content.value,
                reverse=not self.sort_ascending
            )

            # Intentar actualizar la página si existe
            try:
                e.control.page.update()
            except AttributeError:
                pass  # Permite testear sin page real

        return handler

    def _get_page_rows(self):
        start = self.current_page * self.page_size
        end = start + self.page_size
        if self.virtualized and self.data_provider:
            data = self.data_provider(start, end)
            if isinstance(data, Generator) or isinstance(data, Iterable):
                return list(data)
            return data
        return self.rows[start:end]

    def _next_page(self, e):
        if self.total_rows == 0:
            return

        if (self.current_page + 1) * self.page_size < self.total_rows:
            self.current_page += 1
            try:
                e.control.page.update()
            except AttributeError:
                pass

    def _previous_page(self, e):
        if self.current_page > 0:
            self.current_page -= 1
            try:
                e.control.page.update()
            except AttributeError:
                pass
