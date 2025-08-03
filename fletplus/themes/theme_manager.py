# fletplus/themes/theme_manager.py

"""Utilities to manage visual theme tokens for a Flet page.

This module exposes :class:`ThemeManager`, a helper that keeps a dictionary
of design tokens (colors, typography and radii) and applies them to a
``ft.Page`` instance. Tokens can be queried or updated at runtime using
``get_token`` and ``set_token`` which immediately refresh the page theme.
"""

from __future__ import annotations

import flet as ft


class ThemeManager:
    """Manage theme tokens and apply them to a Flet page.

    Parameters
    ----------
    page:
        ``ft.Page`` instance whose theme will be managed.
    tokens:
        Optional dictionary of initial tokens grouped by ``"colors"``,
        ``"typography"`` and ``"radii"``. Each group contains key/value
        pairs representing individual design tokens. Missing groups or
        tokens are filled with sensible defaults.
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
        self.tokens: dict[str, dict[str, object]] = {
            "colors": {"primary": primary_color},
            "typography": {},
            "radii": {},
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

        self.page.theme = ft.Theme(
            color_scheme_seed=colors.get("primary"),
            font_family=typography.get("font_family"),
        )
        # Store additional tokens that are not directly supported by
        # ``ft.Theme`` as custom attributes.
        self.page.theme.radii = radii
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
    def set_token(self, name: str, value: object) -> None:
        """Set a token value and update the theme.

        Parameters
        ----------
        name:
            Name of the token using ``"group.token"`` notation, e.g.
            ``"colors.primary"`` or ``"radii.default"``.
        value:
            New value for the token.
        """

        group, token = name.split(".", 1)
        self.tokens.setdefault(group, {})[token] = value
        self.apply_theme()

    # ------------------------------------------------------------------
    def get_token(self, name: str) -> object | None:
        """Retrieve a token value.

        Parameters
        ----------
        name:
            Token identifier in ``"group.token"`` format.

        Returns
        -------
        The token value if present, otherwise ``None``.
        """

        group, token = name.split(".", 1)
        return self.tokens.get(group, {}).get(token)

    # ------------------------------------------------------------------
    def set_primary_color(self, color: str) -> None:
        """Backwards compatible helper to set the primary color."""

        self.set_token("colors.primary", color)

