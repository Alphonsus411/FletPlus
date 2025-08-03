import flet as ft
from fletplus.styles import Style
from fletplus.utils.responsive_manager import ResponsiveManager

class ResponsiveGrid:
    def __init__(
        self,
        children: list[ft.Control] = None,
        columns: int = None,
        breakpoints: dict = None,
        spacing: int = 10,
        style: Style | None = None,
    ):
        """Grid responsiva basada en el ancho de la página.

        :param children: Lista de controles a distribuir.
        :param columns: Número fijo de columnas (sobrescribe breakpoints).
        :param breakpoints: Diccionario {ancho_px: columnas}. Ignorado si se usa columns.
        :param spacing: Espaciado entre elementos (padding).
        :param style: Estilo opcional aplicado al grid completo.
        """
        self.children = children or []
        self.spacing = spacing
        self.style = style

        if columns is not None:
            self.breakpoints = {0: columns}
        else:
            self.breakpoints = breakpoints or {
                0: 1,
                600: 2,
                900: 3,
                1200: 4
            }

    def build(self, page_width: int) -> ft.Control:
        # Determinar cuántas columnas usar según el ancho de página
        columns = 1
        for bp, cols in sorted(self.breakpoints.items()):
            if page_width >= bp:
                columns = cols

        col_span = max(1, int(12 / columns))  # Sistema de 12 columnas

        row = ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=child,
                    col=col_span,
                    padding=self.spacing
                ) for child in self.children
            ],
            alignment=ft.MainAxisAlignment.START
        )

        return self.style.apply(row) if self.style else row

    def init_responsive(self, page: ft.Page) -> ft.Control:
        """Inicializa el grid y lo actualiza cuando cambia el ancho de la página."""
        layout = self.build(page.width)
        row = layout.content if self.style else layout

        def rebuild(width: int) -> None:
            updated = self.build(width)
            new_row = updated.content if self.style else updated
            row.controls.clear()
            row.controls.extend(new_row.controls)
            page.update()

        callbacks = {bp: rebuild for bp in self.breakpoints}
        ResponsiveManager(page, callbacks)
        return layout
