import flet as ft

class SmartTable:
    def __init__(self, columns, rows, sortable=True, page_size=10):
        self.columns = columns
        self.rows = rows
        self.sortable = sortable
        self.page_size = page_size
        self.current_page = 0
        self.sorted_column = None
        self.sort_ascending = True

    def build(self):
        return ft.Column([
            ft.DataTable(
                columns=[
                    ft.DataColumn(
                        label=ft.Text(col),
                        on_sort=self._on_sort(index) if self.sortable else None
                    ) for index, col in enumerate(self.columns)
                ],
                rows=self._get_page_rows()
            ),
            ft.Row([
                ft.ElevatedButton("Anterior", on_click=self._previous_page),
                ft.ElevatedButton("Siguiente", on_click=self._next_page),
            ])
        ])

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
        return self.rows[start:end]

    def _next_page(self, e):
        if (self.current_page + 1) * self.page_size < len(self.rows):
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
