# fletplus/components/sidebar_admin.py

import flet as ft
from fletplus.styles import Style

class SidebarAdmin:
    def __init__(
        self,
        menu_items,
        on_select=None,
        header="Menú",
        width=250,
        style: Style | None = None,
    ):
        """Crea una barra lateral de administración.

        :param menu_items: Lista de dicts con {"title": str, "icon": ft.IconName}
        :param on_select: Función callback cuando se selecciona un ítem
        :param header: Título de la barra lateral
        :param width: Anchura del sidebar
        :param style: Estilo opcional a aplicar sobre el contenedor principal
        """
        self.menu_items = menu_items
        self.on_select = on_select
        self.header = header
        self.width = width
        self.selected_index = 0
        self.tiles = []  # Para actualizar visualmente los seleccionados
        self.style = style

    def build(self):
        self.tiles = []

        for i, item in enumerate(self.menu_items):
            tile = ft.ListTile(
                title=ft.Text(item["title"]),
                leading=ft.Icon(item.get("icon", ft.icons.CIRCLE)),
                selected=(i == self.selected_index),
                on_click=lambda e, idx=i: self._select_item(idx, e),
            )
            self.tiles.append(tile)

        container = ft.Container(
            width=self.width,
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=10,
            content=ft.Column([
                ft.Text(self.header, size=20, weight="bold"),
                ft.Divider(),
                ft.Column(self.tiles, expand=True),
            ])
        )

        return self.style.apply(container) if self.style else container

    def _select_item(self, index, e):
        self.selected_index = index

        for i, tile in enumerate(self.tiles):
            tile.selected = (i == index)

        if self.on_select:
            self.on_select(index)

        e.control.page.update()
