# fletplus/components/sidebar_admin.py

import flet as ft

from fletplus.context import theme_context
from fletplus.styles import Style


class SidebarAdmin:
    def __init__(
        self,
        menu_items,
        on_select=None,
        header="Menú",
        width=250,
        style: Style | None = None,
        *,
        active_color: str | None = None,
        inactive_color: str | None = None,
    ):
        """Crea una barra lateral de administración mejorada."""

        self.menu_items = menu_items
        self.on_select = on_select
        self.header = header
        self.width = width
        self.selected_index = 0
        self.tiles: list[ft.Container] = []
        self._tile_entries: list[tuple[ft.Container, ft.Icon, ft.Text]] = []
        self.style = style

        resolved_active = active_color
        resolved_inactive = inactive_color
        if resolved_active is None:
            try:
                theme_manager = theme_context.get()
                resolved_active = theme_manager.get_color("primary", ft.Colors.PRIMARY) or ft.Colors.PRIMARY
            except LookupError:
                resolved_active = ft.Colors.PRIMARY
        if resolved_inactive is None:
            base = resolved_active or ft.Colors.PRIMARY
            fallback = ft.Colors.ON_SURFACE if base == ft.Colors.PRIMARY else base
            resolved_inactive = ft.Colors.with_opacity(0.72, fallback)

        self.active_color = resolved_active
        self.inactive_color = resolved_inactive
        self._selected_bg = ft.Colors.with_opacity(0.12, self.active_color)
        self._base_bg = ft.Colors.with_opacity(0.04, self.active_color)

    def build(self):
        self.tiles = []
        self._tile_entries = []

        nav_controls: list[ft.Control] = []
        for i, item in enumerate(self.menu_items):
            icon = ft.Icon(item.get("icon", ft.Icons.CIRCLE), size=20)
            text = ft.Text(item.get("title", ""), weight=ft.FontWeight.W_500)
            row = ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[icon, text],
            )
            container = ft.Container(
                data=i,
                content=row,
                border_radius=ft.border_radius.all(18),
                padding=ft.Padding(14, 10, 14, 10),
                on_click=lambda e, idx=i: self._select_item(idx, e),
                ink=True,
            )
            container.selected = (i == self.selected_index)
            self.tiles.append(container)
            self._tile_entries.append((container, icon, text))
            self._apply_tile_state(i, container, icon, text)
            nav_controls.append(container)

        content = ft.Container(
            width=self.width,
            bgcolor=ft.Colors.with_opacity(0.02, self.active_color),
            border_radius=ft.border_radius.all(24),
            padding=ft.Padding(6, 16, 6, 16),
            content=ft.Column(
                controls=[
                    ft.Text(self.header, size=20, weight=ft.FontWeight.W_700),
                    ft.Divider(opacity=0.3),
                    ft.Column(nav_controls, expand=True, tight=True, spacing=6),
                ],
                spacing=12,
                expand=True,
            ),
        )

        return self.style.apply(content) if self.style else content

    def select(self, index: int) -> None:
        if not 0 <= index < len(self.menu_items):
            return
        self.selected_index = index
        for i, (tile, icon, text) in enumerate(self._tile_entries):
            self._apply_tile_state(i, tile, icon, text)
            if tile.page:
                tile.update()

    def _apply_tile_state(self, index: int, tile: ft.Container, icon: ft.Icon, text: ft.Text) -> None:
        is_selected = index == self.selected_index
        tile.selected = is_selected
        tile.bgcolor = self._selected_bg if is_selected else self._base_bg
        icon.color = self.active_color if is_selected else self.inactive_color
        text.color = self.active_color if is_selected else self.inactive_color
        text.weight = ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_500

    def _select_item(self, index, e):
        if self.selected_index == index:
            return
        self.select(index)
        if self.on_select:
            self.on_select(index)
        if e and e.control and e.control.page:
            e.control.page.update()
