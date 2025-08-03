"""Herramientas de estilo para controles de Flet."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import flet as ft


@dataclass
class Style:
    """Define estilos para un control de Flet.

    Los parámetros corresponden a propiedades de :class:`ft.Container` y se
    utilizan para envolver un control con dichos estilos. Cualquiera de ellos
    puede omitirse.

    Ejemplo
    -------
    >>> import flet as ft
    >>> from fletplus.styles import Style
    >>> style = Style(width=100, height=50, bgcolor=ft.colors.BLUE,
    ...              shadow=ft.BoxShadow(blur_radius=4, color=ft.colors.BLACK))
    >>> container = style.apply(ft.Text("hola"))
    >>> container.width, container.height
    (100, 50)
    """

    margin: Optional[Any] = None
    padding: Optional[Any] = None
    bgcolor: Optional[Any] = None
    border_radius: Optional[Any] = None
    border_color: Optional[Any] = None
    border_width: int | float = 1
    text_style: Optional[Any] = None
    width: Optional[int | float] = None
    height: Optional[int | float] = None
    min_width: Optional[int | float] = None
    max_width: Optional[int | float] = None
    min_height: Optional[int | float] = None
    max_height: Optional[int | float] = None
    shadow: Optional[Any] = None
    gradient: Optional[Any] = None
    alignment: Optional[Any] = None
    opacity: Optional[float] = None
    transform: Optional[Any] = None
    transition: Optional[Any] = None

    def apply(self, control: ft.Control) -> ft.Container:
        """Envuelve ``control`` en un :class:`ft.Container` con los estilos.

        Si ``text_style`` está definido e ``control`` admite estilos de texto,
        se aplica directamente al control antes de envolverlo. Las propiedades
        como ``width``, ``height``, ``shadow``, ``gradient``, ``alignment``,
        ``opacity``, ``transform`` (``scale``, ``rotate`` u ``offset``) y
        ``transition`` se traducen a parámetros de :class:`ft.Container`.
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
        if self.width is not None:
            container_kwargs["width"] = self.width
        if self.height is not None:
            container_kwargs["height"] = self.height
        if self.shadow is not None:
            container_kwargs["shadow"] = self.shadow
        if self.gradient is not None:
            container_kwargs["gradient"] = self.gradient
        if self.alignment is not None:
            container_kwargs["alignment"] = self.alignment
        if self.opacity is not None:
            container_kwargs["opacity"] = self.opacity
        if self.transition is not None:
            container_kwargs["animate"] = self.transition

        if self.transform is not None:
            if isinstance(self.transform, dict):
                if "scale" in self.transform:
                    container_kwargs["scale"] = self.transform["scale"]
                if "rotate" in self.transform:
                    container_kwargs["rotate"] = self.transform["rotate"]
                if "offset" in self.transform:
                    container_kwargs["offset"] = self.transform["offset"]
            else:
                if isinstance(self.transform, ft.transform.Scale):
                    container_kwargs["scale"] = self.transform
                elif isinstance(self.transform, ft.transform.Rotate):
                    container_kwargs["rotate"] = self.transform
                elif isinstance(self.transform, ft.transform.Offset):
                    container_kwargs["offset"] = self.transform

        container = ft.Container(content=control, **container_kwargs)

        if self.min_width is not None:
            container.min_width = self.min_width
        if self.max_width is not None:
            container.max_width = self.max_width
        if self.min_height is not None:
            container.min_height = self.min_height
        if self.max_height is not None:
            container.max_height = self.max_height

        return container
