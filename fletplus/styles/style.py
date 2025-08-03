"""Herramientas de estilo para controles de Flet."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import flet as ft


@dataclass
class Style:
    """Define estilos para un control de Flet.

    Los parámetros corresponden a propiedades de :class:`ft.Container` y se
    utilizan para envolver un control con dichos estilos.
    """

    margin: Optional[Any] = None
    padding: Optional[Any] = None
    bgcolor: Optional[Any] = None
    border_radius: Optional[Any] = None
    border_color: Optional[Any] = None
    border_width: int | float = 1
    text_style: Optional[Any] = None

    def apply(self, control: ft.Control) -> ft.Container:
        """Envuelve ``control`` en un :class:`ft.Container` con los estilos.

        Si ``text_style`` está definido e ``control`` admite estilos de texto,
        se aplica directamente al control antes de envolverlo.
        """

        if self.text_style is not None:
            # Intentar asignar el estilo a controles de texto
            if hasattr(control, "style"):
                try:
                    control.style = self.text_style
                except Exception:
                    pass

        container_kwargs: dict[str, Any] = {}
        if self.margin is not None:
            container_kwargs["margin"] = self.margin
        if self.padding is not None:
            container_kwargs["padding"] = self.padding
        if self.bgcolor is not None:
            container_kwargs["bgcolor"] = self.bgcolor
        if self.border_radius is not None:
            container_kwargs["border_radius"] = self.border_radius
        if self.border_color is not None:
            container_kwargs["border"] = ft.border.all(self.border_width, self.border_color)

        return ft.Container(content=control, **container_kwargs)
