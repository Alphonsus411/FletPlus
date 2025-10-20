# fletplus/themes/theme_manager.py

"""Utilities to manage visual theme tokens for a Flet page.

This module exposes :class:`ThemeManager`, a helper that keeps a dictionary
of design tokens (colors, typography, radii, spacing, borders and shadows)
and applies them to a ``ft.Page`` instance. Tokens can be queried or updated
at runtime using ``get_token`` and ``set_token`` which immediately refresh
the page theme.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
import flet as ft

from fletplus.themes.palettes import (
    get_palette_definition,
    has_palette,
    list_palettes,
)

logger = logging.getLogger(__name__)


def load_palette_from_file(file_path: str, mode: str = "light") -> dict[str, object]:
    """Load a color palette from a JSON file.

    Parameters
    ----------
    file_path:
        Path to the JSON file containing palette definitions under "light"
        and/or "dark" keys.
    mode:
        Palette mode to load. Must be ``"light"`` or ``"dark"``.

    Returns
    -------
    dict[str, object]
        Palette dictionary for the requested mode. Nested color groups
        such as ``{"info": {"100": "#BBDEFB"}}`` are flattened into
        ``{"info_100": "#BBDEFB"}``. This works for any semantic group
        (``info``, ``success``, ``warning`` or ``error``).
        If the mode key is missing, the file cannot be opened or contains
        invalid JSON, the error is logged and an empty dictionary is
        returned.

    Raises
    ------
    ValueError
        If ``mode`` is not ``"light"`` or ``"dark"``.
    """

    if mode not in {"light", "dark"}:
        raise ValueError("mode must be 'light' or 'dark'")

    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        logger.error("Palette file '%s' not found", file_path)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in palette file '%s': %s", file_path, exc)
        return {}

    palette = data.get(mode, {})

    flat_palette: dict[str, object] = {}
    for name, value in palette.items():
        if isinstance(value, dict):
            for shade, shade_value in value.items():
                flat_palette[f"{name}_{shade}"] = shade_value
        else:
            flat_palette[name] = value

    return flat_palette


class ThemeManager:
    """Manage theme tokens and apply them to a Flet page.

    Parameters
    ----------
    page:
        ``ft.Page`` instance whose theme will be managed.
    tokens:
        Optional dictionary of initial tokens grouped by ``"colors"``,
        ``"typography"``, ``"radii"``, ``"spacing"``, ``"borders`` and
        ``"shadows"``. Each group contains key/value pairs representing
        individual design tokens. Missing groups or tokens are filled with
        sensible defaults.
    primary_color:
        Backwards compatible argument used when ``tokens`` does not specify
        ``"colors.primary"``. Defaults to ``ft.Colors.BLUE``.
    """

    def __init__(
        self,
        page: ft.Page,
        tokens: dict | None = None,
        primary_color: str = ft.Colors.BLUE,
        *,
        palette: str | Mapping[str, Mapping[str, object]] | None = None,
        palette_mode: str | None = None,
    ) -> None:
        self.page = page
        self.dark_mode = False
        if palette_mode in {"dark", "light"}:
            self.dark_mode = palette_mode == "dark"

        # Default token structure
        shade_range = range(100, 1000, 100)
        base_colors = {
            "secondary": "PURPLE",
            "tertiary": "TEAL",
            "info": "BLUE",
            "success": "GREEN",
            "warning": "AMBER",
            "error": "RED",
        }

        color_defaults = {
            "primary": primary_color,
            **{
                f"{token}_{n}": getattr(ft.Colors, f"{base}_{n}")
                for token, base in base_colors.items()
                for n in shade_range
            },
        }
        self.tokens: dict[str, dict[str, object]] = {
            "colors": color_defaults,
            "typography": {},
            "radii": {},
            "spacing": {"default": 8},
            "borders": {"default": 1},
            "shadows": {"default": "none"},
            "gradients": {},
        }

        self._palette_definition: dict[str, Mapping[str, object]] | None = None
        self._palette_name: str | None = None

        if palette is not None:
            try:
                self.apply_palette(palette, mode=palette_mode, refresh=False)
            except Exception as exc:  # pragma: no cover - errores logueados
                logger.error("Failed to apply palette '%s': %s", palette, exc)

        if tokens:
            for group, values in tokens.items():
                if isinstance(values, Mapping):
                    self.tokens.setdefault(group, {}).update(values)

        # Aplicar la variante inicial de la paleta tras fusionar tokens
        if self._palette_definition is not None:
            self._apply_current_palette_variant()

    # ------------------------------------------------------------------
    def apply_theme(self) -> None:
        """Apply current tokens to the page theme."""

        colors = self.tokens.get("colors", {})
        typography = self.tokens.get("typography", {})
        radii = self.tokens.get("radii", {})
        spacing = self.tokens.get("spacing", {})
        borders = self.tokens.get("borders", {})
        shadows = self.tokens.get("shadows", {})

        self.page.theme = ft.Theme(
            color_scheme_seed=colors.get("primary"),
            font_family=typography.get("font_family"),
        )
        # Store additional tokens that are not directly supported by
        # ``ft.Theme`` as custom attributes.
        self.page.theme.radii = radii
        self.page.theme.spacing = spacing
        self.page.theme.borders = borders
        self.page.theme.shadows = shadows
        self.page.theme_mode = (
            ft.ThemeMode.DARK if self.dark_mode else ft.ThemeMode.LIGHT
        )

        background = colors.get("background")
        if background:
            self.page.bgcolor = background
        surface = colors.get("surface")
        if surface:
            setattr(self.page, "surface_tint_color", surface)

        self.page.update()

    # ------------------------------------------------------------------
    def toggle_dark_mode(self) -> None:
        """Toggle between light and dark modes."""

        self.dark_mode = not self.dark_mode
        self._apply_current_palette_variant()
        self.apply_theme()

    # ------------------------------------------------------------------
    def apply_palette(
        self,
        palette: str | Mapping[str, Mapping[str, object]],
        *,
        mode: str | None = None,
        refresh: bool = True,
    ) -> None:
        """Carga una paleta predefinida o personalizada y actualiza los tokens."""

        palette_definition: dict[str, Mapping[str, object]] | None

        if isinstance(palette, str):
            if not has_palette(palette):
                raise ValueError(f"Palette '{palette}' is not registered")
            definition = get_palette_definition(palette) or {}
            palette_definition = {
                key: value
                for key, value in definition.items()
                if isinstance(value, Mapping)
            }
            self._palette_name = palette
        elif isinstance(palette, Mapping):
            palette_definition = {
                key: value
                for key, value in palette.items()
                if isinstance(value, Mapping)
            }
            self._palette_name = None
        else:
            raise TypeError("palette must be a name or a mapping of tokens")

        if mode in {"light", "dark"}:
            self.dark_mode = mode == "dark"

        self._palette_definition = palette_definition
        self._apply_current_palette_variant()

        if refresh:
            self.apply_theme()

    # ------------------------------------------------------------------
    @staticmethod
    def _split_name(name: str) -> tuple[str, str]:
        """Split a ``group.token`` string into its components.

        This helper only separates on the first dot, allowing tokens to
        contain underscores, numbers or any other characters (e.g.
        ``"colors.warning_500"``).

        Parameters
        ----------
        name:
            Token identifier in ``"group.token"`` format.

        Returns
        -------
        tuple[str, str]
            The ``(group, token)`` pair.

        Raises
        ------
        ValueError
            If ``name`` does not contain a dot separator.
        """

        group, sep, token = name.partition(".")
        if not sep:
            raise ValueError("Token name must be in 'group.token' format")
        return group, token

    # ------------------------------------------------------------------
    def set_token(self, name: str, value: object) -> None:
        """Set a token value and update the theme.

        Parameters
        ----------
        name:
            Name of the token using ``"group.token"`` notation, e.g.
            ``"colors.primary"`` or ``"radii.default"``. Token names may
            contain underscores or numbers such as ``"colors.warning_500"``
            or ``"colors.success_200"``.
        value:
            New value for the token.
        """
        group, token = self._split_name(name)
        self.tokens.setdefault(group, {})[token] = value
        self.apply_theme()

    # ------------------------------------------------------------------
    def get_token(self, name: str) -> object | None:
        """Retrieve a token value.

        Parameters
        ----------
        name:
            Token identifier in ``"group.token"`` format. Token names may
            include underscores or numbers, e.g. ``"colors.info_100"`` or
            ``"colors.error_900"``.

        Returns
        -------
        The token value if present, otherwise ``None``.
        """
        group, token = self._split_name(name)
        return self.tokens.get(group, {}).get(token)

    # ------------------------------------------------------------------
    def set_primary_color(self, color: str) -> None:
        """Backwards compatible helper to set the primary color."""

        self.set_token("colors.primary", color)

    # ------------------------------------------------------------------
    def get_color(self, token: str, default: object | None = None) -> object | None:
        """Recupera un color almacenado en ``tokens.colors``."""

        return self.tokens.get("colors", {}).get(token, default)

    # ------------------------------------------------------------------
    def get_gradient(self, token: str) -> object | None:
        """Devuelve un gradiente preparado para usarse en contenedores."""

        return self.tokens.get("gradients", {}).get(token)

    # ------------------------------------------------------------------
    def list_available_palettes(self) -> list[tuple[str, str]]:
        """Lista las paletas disponibles junto a su descripción."""

        return list(list_palettes())

    # ------------------------------------------------------------------
    def _apply_current_palette_variant(self) -> None:
        if not self._palette_definition:
            return

        mode = "dark" if self.dark_mode else "light"
        variant = self._palette_definition.get(mode)
        if not isinstance(variant, Mapping):
            # Intentar modo alternativo si no existe la variante
            fallback = "light" if mode == "dark" else "dark"
            variant = self._palette_definition.get(fallback)
            if not isinstance(variant, Mapping):
                return

        self._merge_palette_tokens(variant)

    # ------------------------------------------------------------------
    def _merge_palette_tokens(self, palette_tokens: Mapping[str, object]) -> None:
        for group, values in palette_tokens.items():
            if group == "description":
                continue
            if group == "gradients" and isinstance(values, Mapping):
                gradients = self.tokens.setdefault("gradients", {})
                for name, definition in values.items():
                    gradients[name] = self._build_gradient(definition)
                continue

            if isinstance(values, Mapping):
                target = self.tokens.setdefault(group, {})
                target.update(values)

    # ------------------------------------------------------------------
    @staticmethod
    def _build_gradient(definition: object) -> object:
        if isinstance(definition, ft.Gradient):
            return definition
        if not isinstance(definition, Mapping):
            return definition

        colors = list(definition.get("colors", []))
        begin = ThemeManager._as_alignment(definition.get("begin"))
        end = ThemeManager._as_alignment(definition.get("end"))
        return ft.LinearGradient(colors=colors, begin=begin, end=end)

    # ------------------------------------------------------------------
    @staticmethod
    def _as_alignment(value: object) -> ft.Alignment:
        if isinstance(value, ft.Alignment):
            return value
        if isinstance(value, (tuple, list)) and len(value) == 2:
            try:
                return ft.alignment.Alignment(float(value[0]), float(value[1]))
            except (TypeError, ValueError):
                pass
        return ft.alignment.center

