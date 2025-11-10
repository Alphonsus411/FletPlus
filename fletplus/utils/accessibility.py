"""Herramientas para aplicar preferencias de accesibilidad a la página."""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from fletplus.themes.theme_manager import ThemeManager


@dataclass
class AccessibilityPreferences:
    """Preferencias que mejoran la accesibilidad visual y auditiva."""

    text_scale: float = 1.0
    high_contrast: bool = False
    reduce_motion: bool = False
    enable_captions: bool = False
    caption_mode: str = "inline"
    tooltip_wait_ms: int = 400
    caption_duration_ms: int = 4000
    locale: str | None = None

    def apply(self, page: ft.Page, theme: ThemeManager | None = None) -> None:
        """Aplica las preferencias sobre ``page`` y actualiza el tema activo."""

        theme_obj = page.theme if page.theme else ft.Theme()
        if self.locale:
            setattr(page, "locale", self.locale)

        text_color = ft.Colors.WHITE if self.high_contrast else None
        base_size = max(12, int(14 * self.text_scale))

        theme_obj.text_theme = ft.TextTheme(
            body_small=ft.TextStyle(size=max(12, base_size - 2), color=text_color),
            body_medium=ft.TextStyle(size=base_size, color=text_color),
            body_large=ft.TextStyle(size=base_size + 2, color=text_color),
            title_medium=ft.TextStyle(
                size=base_size + 4,
                weight=ft.FontWeight.W_600,
                color=text_color,
            ),
            title_large=ft.TextStyle(
                size=base_size + 6,
                weight=ft.FontWeight.W_700,
                color=text_color,
            ),
        )

        theme_obj.tooltip_theme = ft.TooltipTheme(
            wait_duration=self.tooltip_wait_ms,
            show_duration=self.caption_duration_ms,
            text_style=ft.TextStyle(size=max(12, int(12 * self.text_scale)), color=text_color),
        )

        if self.high_contrast:
            if not hasattr(theme_obj, "_base_color_scheme"):
                theme_obj._base_color_scheme = theme_obj.color_scheme
            if not hasattr(theme_obj, "_base_scaffold_bgcolor"):
                theme_obj._base_scaffold_bgcolor = theme_obj.scaffold_bgcolor
            theme_obj.focus_color = ft.Colors.AMBER_300
            theme_obj.highlight_color = ft.Colors.AMBER_200
            theme_obj.color_scheme = ft.ColorScheme(
                primary=ft.Colors.BLACK,
                on_primary=ft.Colors.WHITE,
                secondary=ft.Colors.BLUE_GREY_700,
                on_secondary=ft.Colors.WHITE,
                background=ft.Colors.BLACK,
                on_background=ft.Colors.WHITE,
                surface=ft.Colors.BLACK,
                on_surface=ft.Colors.WHITE,
                error=ft.Colors.RED_400,
                on_error=ft.Colors.WHITE,
            )
            theme_obj.scaffold_bgcolor = ft.Colors.BLACK
        else:
            theme_obj.focus_color = ft.Colors.BLUE_300
            theme_obj.highlight_color = ft.Colors.BLUE_100
            if hasattr(theme_obj, "_base_color_scheme"):
                theme_obj.color_scheme = theme_obj._base_color_scheme
            if hasattr(theme_obj, "_base_scaffold_bgcolor"):
                theme_obj.scaffold_bgcolor = theme_obj._base_scaffold_bgcolor

        if self.reduce_motion:
            theme_obj.page_transitions = ft.PageTransitionsTheme(
                android=ft.PageTransitionTheme.NONE,
                ios=ft.PageTransitionTheme.NONE,
                linux=ft.PageTransitionTheme.NONE,
                macos=ft.PageTransitionTheme.NONE,
                windows=ft.PageTransitionTheme.NONE,
            )

        page.theme = theme_obj

        if theme is not None:
            typography = theme.tokens.setdefault("typography", {})
            typography["text_scale"] = self.text_scale
            typography["high_contrast"] = self.high_contrast
            accessibility = theme.tokens.setdefault("accessibility", {})
            accessibility["caption_mode"] = self.caption_mode
            accessibility["captions_enabled"] = self.enable_captions
            theme.apply_theme()

        page.update()

    # Conveniencia -----------------------------------------------------
    @property
    def show_accessibility_panel(self) -> bool:
        """Indica si se debe mostrar un panel de controles accesibles."""

        return self.enable_captions or self.high_contrast or self.text_scale != 1.0
