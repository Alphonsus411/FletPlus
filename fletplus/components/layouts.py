import flet as ft
from fletplus.styles import Style
from fletplus.utils.responsive_manager import ResponsiveManager


class ResponsiveContainer:
    """Contenedor que ajusta su estilo según el ancho de la página."""

    def __init__(self, content: ft.Control, breakpoints: dict[int, Style] | None = None):
        self.content = content
        self.breakpoints = breakpoints or {0: Style()}

    def _get_style(self, width: int) -> Style:
        style = Style()
        for bp, st in sorted(self.breakpoints.items()):
            if width >= bp:
                style = st
        return style

    def init_responsive(self, page: ft.Page) -> ft.Container:
        container = ft.Container(content=self.content)

        def rebuild(width: int) -> None:
            style = self._get_style(width)
            if style.padding is not None:
                container.padding = style.padding
            if style.max_width is not None:
                container.max_width = style.max_width
            if style.max_height is not None:
                container.max_height = style.max_height
            if style.width is not None:
                container.width = style.width
            if style.height is not None:
                container.height = style.height
            page.update()

        callbacks = {bp: rebuild for bp in self.breakpoints}
        ResponsiveManager(page, callbacks)
        rebuild(page.width or 0)
        return container


class _FlexBase:
    def __init__(self, controls: list[ft.Control], breakpoints: dict[int, dict] | None = None, style: Style | None = None):
        self.controls = controls or []
        self.breakpoints = breakpoints or {0: {}}
        self.style = style

    def _get_config(self, width: int) -> dict:
        config: dict = {}
        for bp, cfg in sorted(self.breakpoints.items()):
            if width >= bp:
                config = cfg
        return config


class FlexRow(_FlexBase):
    """Fila flexible que recalcula espaciado, alineación y envoltura."""

    def init_responsive(self, page: ft.Page) -> ft.Control:
        cfg = self._get_config(page.width or 0)
        row = ft.Row(
            controls=self.controls,
            spacing=cfg.get("spacing", 0),
            alignment=cfg.get("alignment", ft.MainAxisAlignment.START),
            wrap=cfg.get("wrap", False),
        )
        layout = self.style.apply(row) if self.style else row
        target = layout.content if self.style else layout

        def rebuild(width: int) -> None:
            cfg = self._get_config(width)
            target.spacing = cfg.get("spacing", target.spacing)
            target.alignment = cfg.get("alignment", target.alignment)
            target.wrap = cfg.get("wrap", target.wrap)
            page.update()

        callbacks = {bp: rebuild for bp in self.breakpoints}
        ResponsiveManager(page, callbacks)
        return layout


class FlexColumn(_FlexBase):
    """Columna flexible que recalcula espaciado y alineación."""

    def init_responsive(self, page: ft.Page) -> ft.Control:
        cfg = self._get_config(page.width or 0)
        column = ft.Column(
            controls=self.controls,
            spacing=cfg.get("spacing", 0),
            alignment=cfg.get("alignment", ft.MainAxisAlignment.START),
            scroll=cfg.get("wrap", False),
        )
        layout = self.style.apply(column) if self.style else column
        target = layout.content if self.style else layout

        def rebuild(width: int) -> None:
            cfg = self._get_config(width)
            target.spacing = cfg.get("spacing", target.spacing)
            target.alignment = cfg.get("alignment", target.alignment)
            target.scroll = cfg.get("wrap", target.scroll)
            page.update()

        callbacks = {bp: rebuild for bp in self.breakpoints}
        ResponsiveManager(page, callbacks)
        return layout
