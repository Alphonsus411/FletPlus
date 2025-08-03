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
import flet as ft


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
        ``{"info_100": "#BBDEFB"}``. If the mode key is missing in the
        file, an empty dictionary is returned.

    Raises
    ------
    ValueError
        If ``mode`` is not ``"light"`` or ``"dark"``.
    """

    if mode not in {"light", "dark"}:
        raise ValueError("mode must be 'light' or 'dark'")

    with open(file_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

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
        ``"colors.primary"``. Defaults to ``ft.colors.BLUE``.
    """

    def __init__(
        self,
        page: ft.Page,
        tokens: dict | None = None,
        primary_color: str = ft.colors.BLUE,
    ) -> None:
        self.page = page
        self.dark_mode = False

        # Default token structure
        shade_range = range(100, 1000, 100)
        color_defaults = {
            "primary": primary_color,
            **{f"info_{n}": getattr(ft.colors, f"BLUE_{n}") for n in shade_range},
            **{f"secondary_{n}": getattr(ft.colors, f"PURPLE_{n}") for n in shade_range},
            **{f"tertiary_{n}": getattr(ft.colors, f"TEAL_{n}") for n in shade_range},
            **{
                f"{token}_{n}": getattr(ft.colors, f"{base}_{n}")
                for token, base in {
                    "info": "BLUE",
                    "success": "GREEN",
                    "warning": "AMBER",
                    "error": "RED",
                }.items()
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
        }

        if tokens:
            for group, values in tokens.items():
                self.tokens.setdefault(group, {}).update(values)

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
        self.page.update()

    # ------------------------------------------------------------------
    def toggle_dark_mode(self) -> None:
        """Toggle between light and dark modes."""

        self.dark_mode = not self.dark_mode
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
            contain underscores or numbers such as ``"colors.warning_500"``.
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
            include underscores or numbers, e.g. ``"colors.info_100"``.

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

