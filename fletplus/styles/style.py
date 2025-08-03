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

    Parámetros
    ----------
    margin, margin_top, margin_right, margin_bottom, margin_left
        Márgenes externos del control. Los valores individuales tienen
        prioridad sobre ``margin``.
    padding, padding_top, padding_right, padding_bottom, padding_left
        Relleno interno del control. Los valores individuales tienen prioridad
        sobre ``padding``.
    border_color, border_top, border_right, border_bottom, border_left,
    border_style
        Color y estilo del borde. ``border_style`` acepta ``"solid"``,
        ``"dashed"`` o ``"dotted"`` y se traduce a
        :class:`ft.BorderSideStyle` cuando está disponible.
    background_image
        Ruta o URL de una imagen de fondo.

    Ejemplos
    --------
    Aplicar un borde punteado y márgenes individuales::

        >>> import flet as ft
        >>> from fletplus.styles import Style
        >>> style = Style(width=100, height=50, bgcolor=ft.colors.BLUE,
        ...              border_top=ft.colors.RED, border_style="dashed",
        ...              margin_left=10, padding_top=5)
        >>> container = style.apply(ft.Text("hola"))
        >>> container.width, container.height
        (100, 50)

    Usar una imagen de fondo que cubra todo el contenedor::

        >>> img_style = Style(background_image="https://example.com/bg.png")
        >>> img_container = img_style.apply(ft.Text("hola"))
        >>> img_container.image_src
        'https://example.com/bg.png'
    """

    margin: Optional[Any] = None
    margin_top: Optional[Any] = None
    margin_right: Optional[Any] = None
    margin_bottom: Optional[Any] = None
    margin_left: Optional[Any] = None

    padding: Optional[Any] = None
    padding_top: Optional[Any] = None
    padding_right: Optional[Any] = None
    padding_bottom: Optional[Any] = None
    padding_left: Optional[Any] = None

    bgcolor: Optional[Any] = None
    border_radius: Optional[Any] = None
    border_color: Optional[Any] = None
    border_top: Optional[Any] = None
    border_right: Optional[Any] = None
    border_bottom: Optional[Any] = None
    border_left: Optional[Any] = None
    border_style: Optional[str] = None
    border_width: int | float = 1
    text_style: Optional[Any] = None
    background_image: Optional[str] = None
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

        if any(
            v is not None
            for v in [self.margin_top, self.margin_right, self.margin_bottom, self.margin_left]
        ):
            container_kwargs["margin"] = ft.margin.only(
                left=self.margin_left or 0,
                top=self.margin_top or 0,
                right=self.margin_right or 0,
                bottom=self.margin_bottom or 0,
            )
        elif self.margin is not None:
            container_kwargs["margin"] = self.margin

        if any(
            v is not None
            for v in [self.padding_top, self.padding_right, self.padding_bottom, self.padding_left]
        ):
            container_kwargs["padding"] = ft.padding.only(
                left=self.padding_left or 0,
                top=self.padding_top or 0,
                right=self.padding_right or 0,
                bottom=self.padding_bottom or 0,
            )
        elif self.padding is not None:
            container_kwargs["padding"] = self.padding

        if self.bgcolor is not None:
            container_kwargs["bgcolor"] = self.bgcolor
        if self.border_radius is not None:
            container_kwargs["border_radius"] = self.border_radius

        if (
            self.border_color is not None
            or self.border_top is not None
            or self.border_right is not None
            or self.border_bottom is not None
            or self.border_left is not None
            or self.border_style is not None
        ):
            side_fields = getattr(ft.border.BorderSide, "__dataclass_fields__", {})

            def make_side(color: Any) -> Optional[ft.border.BorderSide]:
                if color is None and self.border_color is None:
                    return None
                kwargs = {"width": self.border_width}
                if color is not None:
                    kwargs["color"] = color
                elif self.border_color is not None:
                    kwargs["color"] = self.border_color
                if (
                    self.border_style is not None
                    and "style" in side_fields
                ):
                    style_map = {
                        "solid": getattr(ft.BorderSideStyle, "SOLID", "solid"),
                        "dashed": getattr(ft.BorderSideStyle, "DASHED", "dashed"),
                        "dotted": getattr(ft.BorderSideStyle, "DOTTED", "dotted"),
                    }
                    kwargs["style"] = style_map.get(self.border_style, self.border_style)
                return ft.border.BorderSide(**kwargs)

            container_kwargs["border"] = ft.border.only(
                top=make_side(self.border_top),
                right=make_side(self.border_right),
                bottom=make_side(self.border_bottom),
                left=make_side(self.border_left),
            )
        elif self.border_color is not None:
            container_kwargs["border"] = ft.border.all(self.border_width, self.border_color)

        if self.background_image is not None:
            container_kwargs["image_src"] = self.background_image
            container_kwargs.setdefault("image_fit", ft.ImageFit.COVER)
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
