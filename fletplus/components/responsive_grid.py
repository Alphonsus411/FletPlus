import flet as ft

class ResponsiveGrid:
    def __init__(self, children: list[ft.Control], breakpoints=None, spacing=10):
        """
        :param children: Lista de widgets (flet.Control) a distribuir en la grilla.
        :param breakpoints: Diccionario {ancho_px: columnas}, por ejemplo {0: 1, 600: 2, 900: 3}
        :param spacing: Espaciado entre elementos
        """
        self.children = children
        self.spacing = spacing
        self.breakpoints = breakpoints or {
            0: 1,
            600: 2,
            900: 3,
            1200: 4
        }

    def build(self, page_width: int):
        # Determinar cuántas columnas según el ancho de página
        columns = 1
        for bp, cols in sorted(self.breakpoints.items()):
            if page_width >= bp:
                columns = cols

        col_span = max(1, int(12 / columns))  # Sistema de 12 columnas de Flet

        return ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=child,
                    col=col_span,
                    padding=self.spacing
                ) for child in self.children
            ],
            alignment=ft.MainAxisAlignment.START
        )
