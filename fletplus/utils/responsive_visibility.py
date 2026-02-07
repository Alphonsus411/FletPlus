from __future__ import annotations

from typing import Dict

import flet as ft

from fletplus.utils.responsive_breakpoints import BreakpointRegistry
from fletplus.utils.responsive_manager import ResponsiveManager
from fletplus.utils.breakpoint_rs import select_breakpoint


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
        raw_width = width_breakpoints or {}
        raw_height = height_breakpoints or {}
        self._width_vis = BreakpointRegistry.normalize(raw_width)
        self._height_vis = BreakpointRegistry.normalize(raw_height)
        self._orientation_vis = orientation_visibility or {}
        self._width_keys = sorted(self._width_vis.keys())
        self._height_keys = sorted(self._height_vis.keys())

        callbacks_w = {bp: self._update_width for bp in self._width_keys}
        callbacks_h = {bp: self._update_height for bp in self._height_keys}
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
    def _select_visibility(self, mapping: Dict[int, bool], keys: list[int], value: int) -> bool | None:
        bp = select_breakpoint(keys, value)
        if bp is None:
            return None
        return mapping.get(bp)

    def _update_width(self, width: int) -> None:
        vis = self._select_visibility(self._width_vis, self._width_keys, width)
        if vis is not None:
            self.control.visible = vis
            self.page.update()

    def _update_height(self, height: int) -> None:
        vis = self._select_visibility(self._height_vis, self._height_keys, height)
        if vis is not None:
            self.control.visible = vis
            self.page.update()

    def _update_orientation(self, orientation: str) -> None:
        if orientation in self._orientation_vis:
            self.control.visible = self._orientation_vis[orientation]
            self.page.update()
