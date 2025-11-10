"""Controlador para adaptar temas según dispositivo, orientación y ancho."""

from __future__ import annotations

from copy import deepcopy
import logging
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

import flet as ft

from fletplus.themes.theme_manager import ThemeManager
from fletplus.utils.device_profiles import (
    DeviceProfile,
    EXTENDED_DEVICE_PROFILES,
    iter_device_profiles,
)
from fletplus.utils.responsive_manager import ResponsiveManager

logger = logging.getLogger(__name__)


PaletteSpec = Mapping[str, object] | str | tuple[object, ...]


@dataclass(slots=True)
class _PaletteConfig:
    palette: str | None = None
    mode: str | None = None
    definition: Mapping[str, Mapping[str, object]] | None = None


class AdaptiveThemeController:
    """Aplica tokens del :class:`ThemeManager` según el contexto actual."""

    def __init__(
        self,
        page: ft.Page,
        theme: ThemeManager,
        *,
        device_palettes: Mapping[str, PaletteSpec] | None = None,
        device_tokens: Mapping[str, Mapping[str, Mapping[str, object]]] | None = None,
        orientation_tokens: Mapping[str, Mapping[str, Mapping[str, object]]] | None = None,
        breakpoint_tokens: Mapping[int, Mapping[str, Mapping[str, object]]] | None = None,
        device_profiles: Sequence[DeviceProfile] | None = None,
    ) -> None:
        self.page = page
        self.theme = theme
        self.device_profiles = tuple(device_profiles or EXTENDED_DEVICE_PROFILES)

        self._device_palettes: dict[str, _PaletteConfig] = {
            key.lower(): self._normalize_palette_spec(value)
            for key, value in (device_palettes or {}).items()
        }

        self._default_palette = self._capture_current_palette()

        if device_tokens:
            for device, tokens in device_tokens.items():
                self.theme.set_device_tokens(device, tokens, refresh=False)

        if orientation_tokens:
            for orientation, tokens in orientation_tokens.items():
                self.theme.set_orientation_tokens(orientation, tokens, refresh=False)

        if breakpoint_tokens:
            for breakpoint, tokens in breakpoint_tokens.items():
                self.theme.set_breakpoint_tokens(breakpoint, tokens, refresh=False)

        width_callbacks: dict[int, Callable[[int], None]] = {}
        for profile in iter_device_profiles(self.device_profiles):
            width_callbacks[profile.min_width] = self._handle_width_change
        if not width_callbacks:
            width_callbacks = {0: self._handle_width_change}

        device_callbacks = {
            profile.name: self._handle_device_change for profile in self.device_profiles
        }

        orientation_callbacks = {
            "portrait": self._handle_orientation_change,
            "landscape": self._handle_orientation_change,
        }

        self._current_device: str | None = None
        self._current_orientation: str | None = None
        self._current_width: int | None = None

        self._manager = ResponsiveManager(
            page,
            breakpoints=width_callbacks,
            orientation_callbacks=orientation_callbacks,
            device_callbacks=device_callbacks,
            device_profiles=self.device_profiles,
        )

    # ------------------------------------------------------------------
    def _capture_current_palette(self) -> _PaletteConfig | None:
        palette_def = getattr(self.theme, "_palette_definition", None)
        palette_name = getattr(self.theme, "_palette_name", None)
        mode = "dark" if self.theme.dark_mode else "light"
        if palette_name:
            return _PaletteConfig(palette=palette_name, mode=mode)
        if isinstance(palette_def, Mapping):
            return _PaletteConfig(definition=deepcopy(palette_def), mode=mode)
        return None

    # ------------------------------------------------------------------
    def _normalize_palette_spec(self, spec: PaletteSpec) -> _PaletteConfig:
        if isinstance(spec, str):
            return _PaletteConfig(palette=spec)

        if isinstance(spec, Mapping):
            if "light" in spec or "dark" in spec:
                return _PaletteConfig(definition=spec)
            palette_name = spec.get("palette") or spec.get("name")
            mode = spec.get("mode") if isinstance(spec.get("mode"), str) else None
            definition = spec.get("definition")
            if isinstance(definition, Mapping):
                return _PaletteConfig(palette=palette_name, mode=mode, definition=definition)
            return _PaletteConfig(palette=palette_name, mode=mode)

        if isinstance(spec, tuple) and spec:
            palette_name = spec[0] if isinstance(spec[0], str) else None
            mode = spec[1] if len(spec) > 1 and isinstance(spec[1], str) else None
            return _PaletteConfig(palette=palette_name, mode=mode)

        return _PaletteConfig()

    # ------------------------------------------------------------------
    def _apply_palette(self, config: _PaletteConfig | None) -> None:
        if config is None:
            config = self._default_palette
        if config is None:
            return
        try:
            if config.definition is not None:
                self.theme.apply_palette(
                    config.definition, mode=config.mode, refresh=False
                )
            elif config.palette is not None:
                self.theme.apply_palette(config.palette, mode=config.mode, refresh=False)
        except Exception as exc:  # pragma: no cover - registro defensivo
            logger.error("Failed to apply palette '%s': %s", config.palette, exc)

    # ------------------------------------------------------------------
    def _refresh_theme(self) -> None:
        self.theme.apply_theme(
            device=self._current_device,
            orientation=self._current_orientation,
            width=self._current_width,
        )

    # ------------------------------------------------------------------
    def _handle_device_change(self, device: str) -> None:
        self._current_device = device
        palette = self._device_palettes.get(device) or self._device_palettes.get("default")
        self._apply_palette(palette)
        self._refresh_theme()

    # ------------------------------------------------------------------
    def _handle_orientation_change(self, orientation: str) -> None:
        self._current_orientation = orientation
        self._refresh_theme()

    # ------------------------------------------------------------------
    def _handle_width_change(self, width: int) -> None:
        self._current_width = width
        self._refresh_theme()


__all__ = ["AdaptiveThemeController"]

