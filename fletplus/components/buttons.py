import flet as ft
from fletplus.styles import Style
from fletplus.themes.theme_manager import ThemeManager

class PrimaryButton(ft.ElevatedButton):
    """Botón principal con colores basados en ``ThemeManager``."""

    def __init__(
        self,
        label: str,
        icon: str | None = None,
        *,
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        self._style = style
        text_size = None
        bgcolor = None
        if theme is not None:
            bgcolor = theme.get_token("colors.primary")
            text_size = theme.get_token("typography.button_size")
        button_style = (
            ft.ButtonStyle(text_style=ft.TextStyle(size=text_size))
            if text_size is not None
            else None
        )
        super().__init__(
            text=label,
            icon=icon,
            bgcolor=bgcolor,
            style=button_style,
            **kwargs,
        )

    def build(self):
        return self._style.apply(self) if self._style else self


class SecondaryButton(ft.ElevatedButton):
    """Botón secundario que usa tokens de ``ThemeManager``."""

    def __init__(
        self,
        label: str,
        icon: str | None = None,
        *,
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        self._style = style
        text_size = None
        bgcolor = ft.colors.BLUE_GREY_100
        if theme is not None:
            bgcolor = theme.get_token("colors.secondary") or bgcolor
            text_size = theme.get_token("typography.button_size")
        button_style = (
            ft.ButtonStyle(text_style=ft.TextStyle(size=text_size))
            if text_size is not None
            else None
        )
        super().__init__(
            text=label,
            icon=icon,
            bgcolor=bgcolor,
            style=button_style,
            **kwargs,
        )

    def build(self):
        return self._style.apply(self) if self._style else self


class IconButton(ft.IconButton):
    """Botón icónico que aplica tokens de ``ThemeManager``."""

    def __init__(
        self,
        icon: str,
        label: str = "",
        *,
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        self._style = style
        color = None
        size = None
        if theme is not None:
            color = theme.get_token("colors.primary")
            size = theme.get_token("typography.icon_size")
        super().__init__(
            icon=icon,
            tooltip=label,
            icon_color=color,
            icon_size=size,
            **kwargs,
        )

    def build(self):
        return self._style.apply(self) if self._style else self
