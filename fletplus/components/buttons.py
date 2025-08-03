import flet as ft
from fletplus.styles import Style
from fletplus.themes.theme_manager import ThemeManager


def _get_button_tokens(theme: ThemeManager | None, color_key: str):
    """Obtiene tamaños e información de colores para los estados del botón."""

    text_size = None
    icon_size = None
    bgcolor: dict[ft.ControlState, str] = {}

    if theme is not None:
        text_size = theme.get_token("typography.button_size")
        icon_size = theme.get_token("typography.icon_size")

        base = theme.get_token(f"colors.{color_key}")
        if base is not None:
            bgcolor[ft.ControlState.DEFAULT] = base

        hovered = theme.get_token(f"colors.{color_key}_hover")
        if hovered is not None:
            bgcolor[ft.ControlState.HOVERED] = hovered

        focused = theme.get_token(f"colors.{color_key}_focus")
        if focused is not None:
            bgcolor[ft.ControlState.FOCUSED] = focused

        pressed = theme.get_token(f"colors.{color_key}_pressed")
        if pressed is not None:
            bgcolor[ft.ControlState.PRESSED] = pressed

    text_style = ft.TextStyle(size=text_size) if text_size is not None else None
    icon_size_style = (
        {ft.ControlState.DEFAULT: icon_size} if icon_size is not None else None
    )

    return text_style, icon_size_style, bgcolor

class PrimaryButton(ft.ElevatedButton):
    """Botón principal con colores basados en ``ThemeManager``."""

    def __init__(
        self,
        label: str,
        icon: str | None = None,
        *,
        icon_position: str = "start",
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        self._style = style
        text_style, icon_size_style, bgcolor = _get_button_tokens(
            theme, "primary"
        )
        button_style = ft.ButtonStyle(
            text_style=text_style,
            icon_size=icon_size_style,
            bgcolor=bgcolor or None,
        )

        content = None
        text_param = label
        icon_param = icon
        if icon is not None and icon_position == "end":
            text_param = None
            icon_param = None
            text_size = text_style.size if text_style else None
            icon_size = icon_size_style[ft.ControlState.DEFAULT] if icon_size_style else None
            content = ft.Row(
                [
                    ft.Text(label, size=text_size),
                    ft.Icon(icon, size=icon_size),
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
            )
        super().__init__(
            text=text_param,
            icon=icon_param,
            content=content,
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
        icon_position: str = "start",
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        self._style = style
        text_style, icon_size_style, bgcolor = _get_button_tokens(
            theme, "secondary"
        )
        if not bgcolor and theme is None:
            bgcolor = {ft.ControlState.DEFAULT: ft.colors.BLUE_GREY_100}
        elif not bgcolor:
            bgcolor = {ft.ControlState.DEFAULT: theme.get_token("colors.secondary") or ft.colors.BLUE_GREY_100}

        button_style = ft.ButtonStyle(
            text_style=text_style,
            icon_size=icon_size_style,
            bgcolor=bgcolor,
        )

        content = None
        text_param = label
        icon_param = icon
        if icon is not None and icon_position == "end":
            text_param = None
            icon_param = None
            text_size = text_style.size if text_style else None
            icon_size = icon_size_style[ft.ControlState.DEFAULT] if icon_size_style else None
            content = ft.Row(
                [
                    ft.Text(label, size=text_size),
                    ft.Icon(icon, size=icon_size),
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
            )

        super().__init__(
            text=text_param,
            icon=icon_param,
            content=content,
            style=button_style,
            **kwargs,
        )

    def build(self):
        return self._style.apply(self) if self._style else self


class _StatusButton(ft.ElevatedButton):
    """Botón genérico con color configurable mediante tokens."""

    def __init__(
        self,
        color_key: str,
        label: str,
        icon: str | None = None,
        *,
        icon_position: str = "start",
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        self._style = style
        text_style, icon_size_style, bgcolor = _get_button_tokens(theme, color_key)
        button_style = ft.ButtonStyle(
            text_style=text_style,
            icon_size=icon_size_style,
            bgcolor=bgcolor or None,
        )

        content = None
        text_param = label
        icon_param = icon
        if icon is not None and icon_position == "end":
            text_param = None
            icon_param = None
            text_size = text_style.size if text_style else None
            icon_size = (
                icon_size_style[ft.ControlState.DEFAULT]
                if icon_size_style
                else None
            )
            content = ft.Row(
                [ft.Text(label, size=text_size), ft.Icon(icon, size=icon_size)],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
            )
        super().__init__(
            text=text_param,
            icon=icon_param,
            content=content,
            style=button_style,
            **kwargs,
        )

    def build(self):
        return self._style.apply(self) if self._style else self


class SuccessButton(_StatusButton):
    """Botón de éxito basado en tokens de ``ThemeManager``."""

    def __init__(
        self,
        label: str,
        icon: str | None = None,
        *,
        icon_position: str = "start",
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            "success",
            label,
            icon,
            icon_position=icon_position,
            theme=theme,
            style=style,
            **kwargs,
        )


class WarningButton(_StatusButton):
    """Botón de advertencia basado en tokens de ``ThemeManager``."""

    def __init__(
        self,
        label: str,
        icon: str | None = None,
        *,
        icon_position: str = "start",
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            "warning",
            label,
            icon,
            icon_position=icon_position,
            theme=theme,
            style=style,
            **kwargs,
        )


class DangerButton(_StatusButton):
    """Botón de peligro basado en tokens de ``ThemeManager``."""

    def __init__(
        self,
        label: str,
        icon: str | None = None,
        *,
        icon_position: str = "start",
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            "error",
            label,
            icon,
            icon_position=icon_position,
            theme=theme,
            style=style,
            **kwargs,
        )


class InfoButton(_StatusButton):
    """Botón informativo basado en tokens de ``ThemeManager``."""

    def __init__(
        self,
        label: str,
        icon: str | None = None,
        *,
        icon_position: str = "start",
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            "info",
            label,
            icon,
            icon_position=icon_position,
            theme=theme,
            style=style,
            **kwargs,
        )


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
        _, icon_size_style, icon_colors = _get_button_tokens(theme, "primary")
        button_style = ft.ButtonStyle(
            icon_size=icon_size_style,
            icon_color=icon_colors or None,
        )
        super().__init__(
            icon=icon,
            tooltip=label,
            style=button_style,
            **kwargs,
        )

    def build(self):
        return self._style.apply(self) if self._style else self


class OutlinedButton(ft.OutlinedButton):
    """Botón delineado con soporte de tokens y estados."""

    def __init__(
        self,
        label: str,
        icon: str | None = None,
        *,
        icon_position: str = "start",
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        self._style = style
        text_style, icon_size_style, bgcolor = _get_button_tokens(theme, "primary")
        color = None
        if theme is not None:
            color = theme.get_token("colors.primary")

        side = (
            {ft.ControlState.DEFAULT: ft.BorderSide(1, color)}
            if color is not None
            else None
        )
        color_states = {ft.ControlState.DEFAULT: color} if color is not None else None
        button_style = ft.ButtonStyle(
            text_style=text_style,
            icon_size=icon_size_style,
            bgcolor=bgcolor or None,
            side=side,
            color=color_states,
        )

        content = None
        text_param = label
        icon_param = icon
        if icon is not None and icon_position == "end":
            text_param = None
            icon_param = None
            text_size = text_style.size if text_style else None
            icon_size = icon_size_style[ft.ControlState.DEFAULT] if icon_size_style else None
            content = ft.Row(
                [ft.Text(label, size=text_size), ft.Icon(icon, size=icon_size)],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
            )

        super().__init__(
            text=text_param,
            icon=icon_param,
            content=content,
            style=button_style,
            **kwargs,
        )

    def build(self):
        return self._style.apply(self) if self._style else self


class TextButton(ft.TextButton):
    """Botón de texto con soporte de estados y tokens."""

    def __init__(
        self,
        label: str,
        icon: str | None = None,
        *,
        icon_position: str = "start",
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        self._style = style
        text_style, icon_size_style, bgcolor = _get_button_tokens(theme, "primary")
        color = None
        if theme is not None:
            color = theme.get_token("colors.primary")

        color_states = {ft.ControlState.DEFAULT: color} if color is not None else None
        button_style = ft.ButtonStyle(
            text_style=text_style,
            icon_size=icon_size_style,
            bgcolor=bgcolor or None,
            color=color_states,
        )

        content = None
        text_param = label
        icon_param = icon
        if icon is not None and icon_position == "end":
            text_param = None
            icon_param = None
            text_size = text_style.size if text_style else None
            icon_size = icon_size_style[ft.ControlState.DEFAULT] if icon_size_style else None
            content = ft.Row(
                [ft.Text(label, size=text_size), ft.Icon(icon, size=icon_size)],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
            )

        super().__init__(
            text=text_param,
            icon=icon_param,
            content=content,
            style=button_style,
            **kwargs,
        )

    def build(self):
        return self._style.apply(self) if self._style else self


class FloatingActionButton(ft.ElevatedButton):
    """Botón de acción flotante con soporte de estilos y estados."""

    def __init__(
        self,
        icon: str,
        label: str = "",
        *,
        icon_position: str = "start",
        theme: ThemeManager | None = None,
        style: Style | None = None,
        **kwargs,
    ) -> None:
        self._style = style
        text_style, icon_size_style, bgcolor = _get_button_tokens(theme, "primary")
        button_style = ft.ButtonStyle(
            text_style=text_style,
            icon_size=icon_size_style,
            bgcolor=bgcolor or None,
            shape={ft.ControlState.DEFAULT: ft.CircleBorder()},
        )

        content = None
        text_param = label
        icon_param = icon
        if icon_position == "end" and label:
            text_param = None
            icon_param = None
            text_size = text_style.size if text_style else None
            icon_size = icon_size_style[ft.ControlState.DEFAULT] if icon_size_style else None
            content = ft.Row(
                [ft.Text(label, size=text_size), ft.Icon(icon, size=icon_size)],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
            )

        super().__init__(
            text=text_param,
            icon=icon_param,
            content=content,
            style=button_style,
            **kwargs,
        )

    def build(self):
        return self._style.apply(self) if self._style else self
