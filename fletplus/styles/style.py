"""Herramientas de estilo para controles de Flet."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

import flet as ft


_NOT_SET = object()


@dataclass(init=False)
class Style:
    """Define estilos para un control de Flet.

    Los parámetros corresponden a propiedades de :class:`ft.Container` y se
    utilizan para envolver un control con dichos estilos. Cualquiera de ellos
    puede omitirse. Si un campo se declara explícitamente con ``None``, se
    considera intencional para permitir limpiar la propiedad en estilos
    responsivos.

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
        >>> style = Style(width=100, height=50, bgcolor=ft.Colors.BLUE,
        ...              border_top=ft.Colors.RED, border_style="dashed",
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

    margin: Optional[Any]
    margin_top: Optional[Any]
    margin_right: Optional[Any]
    margin_bottom: Optional[Any]
    margin_left: Optional[Any]

    padding: Optional[Any]
    padding_top: Optional[Any]
    padding_right: Optional[Any]
    padding_bottom: Optional[Any]
    padding_left: Optional[Any]

    bgcolor: Optional[Any]
    border_radius: Optional[Any]
    border_color: Optional[Any]
    border_top: Optional[Any]
    border_right: Optional[Any]
    border_bottom: Optional[Any]
    border_left: Optional[Any]
    border_style: Optional[str]
    border_width: int | float
    text_style: Optional[Any]
    background_image: Optional[str]
    width: Optional[int | float]
    height: Optional[int | float]
    min_width: Optional[int | float]
    max_width: Optional[int | float]
    min_height: Optional[int | float]
    max_height: Optional[int | float]
    shadow: Optional[Any]
    gradient: Optional[Any]
    alignment: Optional[Any]
    opacity: Optional[float]
    transform: Optional[Any]
    transition: Optional[Any]
    _declared_fields: set[str] = field(init=False, repr=False)

    def __init__(
        self,
        margin: Optional[Any] = _NOT_SET,
        margin_top: Optional[Any] = _NOT_SET,
        margin_right: Optional[Any] = _NOT_SET,
        margin_bottom: Optional[Any] = _NOT_SET,
        margin_left: Optional[Any] = _NOT_SET,
        padding: Optional[Any] = _NOT_SET,
        padding_top: Optional[Any] = _NOT_SET,
        padding_right: Optional[Any] = _NOT_SET,
        padding_bottom: Optional[Any] = _NOT_SET,
        padding_left: Optional[Any] = _NOT_SET,
        bgcolor: Optional[Any] = _NOT_SET,
        border_radius: Optional[Any] = _NOT_SET,
        border_color: Optional[Any] = _NOT_SET,
        border_top: Optional[Any] = _NOT_SET,
        border_right: Optional[Any] = _NOT_SET,
        border_bottom: Optional[Any] = _NOT_SET,
        border_left: Optional[Any] = _NOT_SET,
        border_style: Optional[str] = _NOT_SET,
        border_width: int | float = 1,
        text_style: Optional[Any] = _NOT_SET,
        background_image: Optional[str] = _NOT_SET,
        width: Optional[int | float] = _NOT_SET,
        height: Optional[int | float] = _NOT_SET,
        min_width: Optional[int | float] = _NOT_SET,
        max_width: Optional[int | float] = _NOT_SET,
        min_height: Optional[int | float] = _NOT_SET,
        max_height: Optional[int | float] = _NOT_SET,
        shadow: Optional[Any] = _NOT_SET,
        gradient: Optional[Any] = _NOT_SET,
        alignment: Optional[Any] = _NOT_SET,
        opacity: Optional[float] = _NOT_SET,
        transform: Optional[Any] = _NOT_SET,
        transition: Optional[Any] = _NOT_SET,
    ) -> None:
        declared: set[str] = set()

        def set_value(name: str, value: Any) -> None:
            if value is _NOT_SET:
                setattr(self, name, None)
                return
            declared.add(name)
            setattr(self, name, value)

        set_value("margin", margin)
        set_value("margin_top", margin_top)
        set_value("margin_right", margin_right)
        set_value("margin_bottom", margin_bottom)
        set_value("margin_left", margin_left)
        set_value("padding", padding)
        set_value("padding_top", padding_top)
        set_value("padding_right", padding_right)
        set_value("padding_bottom", padding_bottom)
        set_value("padding_left", padding_left)
        set_value("bgcolor", bgcolor)
        set_value("border_radius", border_radius)
        set_value("border_color", border_color)
        set_value("border_top", border_top)
        set_value("border_right", border_right)
        set_value("border_bottom", border_bottom)
        set_value("border_left", border_left)
        set_value("border_style", border_style)
        set_value("text_style", text_style)
        set_value("background_image", background_image)
        set_value("width", width)
        set_value("height", height)
        set_value("min_width", min_width)
        set_value("max_width", max_width)
        set_value("min_height", min_height)
        set_value("max_height", max_height)
        set_value("shadow", shadow)
        set_value("gradient", gradient)
        set_value("alignment", alignment)
        set_value("opacity", opacity)
        set_value("transform", transform)
        set_value("transition", transition)
        self.border_width = border_width
        self._declared_fields = declared

    def declared_fields(self) -> set[str]:
        """Devuelve los campos declarados explícitamente en el estilo."""

        return set(self._declared_fields)

    def declares_container_attr(self, attr: str) -> bool:
        """Indica si ``attr`` fue declarado explícitamente en el estilo.

        Esto permite distinguir entre un campo no definido y uno definido como
        ``None`` cuando se aplican estilos responsivos.
        """

        declared = self._declared_fields
        if attr == "margin":
            return bool(
                {"margin", "margin_top", "margin_right", "margin_bottom", "margin_left"} & declared
            )
        if attr == "padding":
            return bool(
                {"padding", "padding_top", "padding_right", "padding_bottom", "padding_left"}
                & declared
            )
        if attr == "border":
            return bool(
                {
                    "border_color",
                    "border_top",
                    "border_right",
                    "border_bottom",
                    "border_left",
                    "border_style",
                }
                & declared
            )
        if attr in {"image_src", "image_fit"}:
            return "background_image" in declared
        if attr == "animate":
            return "transition" in declared
        if attr in {"scale", "rotate", "offset"}:
            return "transform" in declared
        return attr in declared

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
                except Exception as exc:
                    logger.exception("Error applying text style: %s", exc)

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
