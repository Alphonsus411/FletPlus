import flet as ft
from typing import Dict

from .responsive_manager import ResponsiveManager


class ResponsiveVisibility:
    """Muestra u oculta un control según breakpoints y orientación."""

    def __init__(
        self,
        page: ft.Page,
        control: ft.Control,
        width_breakpoints: Dict[int, bool] | None = None,
        height_breakpoints: Dict[int, bool] | None = None,
        orientation_visibility: Dict[str, bool] | None = None,
    ) -> None:
        self.control = control
        self.page = page
        self._width_vis = width_breakpoints or {}
        self._height_vis = height_breakpoints or {}
        self._orientation_vis = orientation_visibility or {}

        callbacks_w = {bp: self._update_width for bp in self._width_vis}
        callbacks_h = {bp: self._update_height for bp in self._height_vis}
        callbacks_o = {o: self._update_orientation for o in self._orientation_vis}

        self._manager = ResponsiveManager(
            page,
            breakpoints=callbacks_w,
            height_breakpoints=callbacks_h,
            orientation_callbacks=callbacks_o,
        )

        # Estado inicial
        self._update_width(page.width or 0)
        self._update_height(page.height or 0)
        orientation = "landscape" if (page.width or 0) >= (page.height or 0) else "portrait"
        self._update_orientation(orientation)

    # ------------------------------------------------------------------
    def _select_visibility(self, mapping: Dict[int, bool], value: int) -> bool | None:
        bp = max((bp for bp in mapping if value >= bp), default=None)
        if bp is None:
            return None
        return mapping.get(bp)

    def _update_width(self, width: int) -> None:
        vis = self._select_visibility(self._width_vis, width)
        if vis is not None:
            self.control.visible = vis
            self.page.update()

    def _update_height(self, height: int) -> None:
        vis = self._select_visibility(self._height_vis, height)
        if vis is not None:
            self.control.visible = vis
            self.page.update()

    def _update_orientation(self, orientation: str) -> None:
        if orientation in self._orientation_vis:
            self.control.visible = self._orientation_vis[orientation]
            self.page.update()
