"""Panel interactivo para ajustar preferencias de accesibilidad."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import flet as ft

from fletplus.themes.theme_manager import ThemeManager
from fletplus.utils.accessibility import AccessibilityPreferences
from fletplus.utils.responsive_manager import ResponsiveManager


_ACCESSIBLE_SURFACE = getattr(ft.Colors, "ON_SURFACE", ft.Colors.BLUE_GREY_900)


@dataclass(slots=True)
class _ToggleSpec:
    """Describe la configuración visual de un interruptor."""

    title: str
    description: str
    attribute: str
    tooltip: str


class AccessibilityPanel:
    """Colección de controles para configurar accesibilidad en cualquier dispositivo.

    El panel adapta su distribución según el ancho de la página para resultar
    cómodo en móviles, escritorio o web, y aplica inmediatamente los cambios en
    :class:`AccessibilityPreferences` para mejorar la experiencia de personas
    con baja visión o limitaciones auditivas.
    """

    def __init__(
        self,
        *,
        preferences: AccessibilityPreferences | None = None,
        theme: ThemeManager | None = None,
        horizontal_breakpoint: int = 720,
        on_change: Callable[[AccessibilityPreferences], None] | None = None,
    ) -> None:
        self.preferences = preferences or AccessibilityPreferences()
        self.theme = theme
        self.horizontal_breakpoint = horizontal_breakpoint
        self.on_change = on_change

        self._page: ft.Page | None = None
        self._manager: ResponsiveManager | None = None
        self._layout_mode: str = "column"

        self._root: ft.Container | None = None
        self._options_host: ft.Container | None = None
        self._text_scale_display = ft.Text("1.0×", weight=ft.FontWeight.W_600)
        self._text_scale_slider: ft.Slider | None = None
        self._toggles: list[_ToggleSpec] = [
            _ToggleSpec(
                "Alto contraste",
                "Incrementa el contraste y resalta elementos enfocados.",
                "high_contrast",
                "Mejora la legibilidad para baja visión",
            ),
            _ToggleSpec(
                "Reducir animaciones",
                "Minimiza transiciones para personas sensibles al movimiento.",
                "reduce_motion",
                "Reduce efectos de movimiento",
            ),
            _ToggleSpec(
                "Mostrar subtítulos",
                "Activa mensajes textuales para eventos relevantes.",
                "enable_captions",
                "Facilita seguimiento a usuarios con sordera o hipoacusia",
            ),
        ]

        self._cards: list[ft.Container] = []

    # ------------------------------------------------------------------
    def build(self, page: ft.Page) -> ft.Control:
        """Crea el panel y lo vincula al ``page`` recibido."""

        self._page = page
        self._create_controls()
        self._apply_preferences()
        self._set_orientation("row" if (page.width or 0) >= self.horizontal_breakpoint else "column")

        callbacks = {
            0: self._handle_width_change,
            self.horizontal_breakpoint: self._handle_width_change,
        }
        self._manager = ResponsiveManager(page, breakpoints=callbacks)
        return self._root or ft.Container()

    # ------------------------------------------------------------------
    def set_text_scale(self, value: float) -> None:
        """Actualiza manualmente el escalado de texto."""

        scale = round(max(0.8, min(2.0, value)), 2)
        if self.preferences.text_scale == scale:
            return
        self.preferences.text_scale = scale
        self._text_scale_display.value = f"{scale:.1f}×"
        if self._text_scale_slider is not None:
            self._text_scale_slider.value = scale
        self._apply_preferences()

    def toggle_high_contrast(self, enabled: bool) -> None:
        self._handle_toggle("high_contrast", enabled)

    def toggle_reduce_motion(self, enabled: bool) -> None:
        self._handle_toggle("reduce_motion", enabled)

    def toggle_captions(self, enabled: bool) -> None:
        self._handle_toggle("enable_captions", enabled)

    # ------------------------------------------------------------------
    @property
    def orientation(self) -> str:
        """Devuelve la distribución actual del panel (``row`` o ``column``)."""

        return self._layout_mode

    @property
    def control(self) -> ft.Control | None:
        """Devuelve el control raíz generado al llamar :meth:`build`."""

        return self._root

    # ------------------------------------------------------------------
    def _create_controls(self) -> None:
        slider = ft.Slider(
            min=0.8,
            max=1.8,
            divisions=5,
            value=self.preferences.text_scale,
            label="{value}×",
            tooltip="Escala global del texto",
        )
        slider.on_change = lambda e: self.set_text_scale(
            float(e.data or getattr(e.control, "value", self.preferences.text_scale))
        )
        self._text_scale_slider = slider

        heading = ft.Column(
            spacing=2,
            controls=[
                ft.Text(
                    "Preferencias de accesibilidad",
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    "Ajusta la experiencia visual y auditiva en todos los dispositivos.",
                    size=13,
                    color=ft.Colors.with_opacity(0.75, _ACCESSIBLE_SURFACE),
                ),
            ],
        )

        slider_card = self._build_card(
            title="Escala de texto",
            description="Incrementa el tamaño base utilizado por los temas.",
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Valor actual"),
                            self._text_scale_display,
                        ],
                    ),
                    slider,
                ],
            ),
        )

        toggle_cards: list[ft.Container] = []
        for spec in self._toggles:
            toggle = ft.Switch(
                value=bool(getattr(self.preferences, spec.attribute)),
                label=spec.title,
                tooltip=spec.tooltip,
            )
            toggle.on_change = lambda e, attr=spec.attribute: self._handle_toggle(
                attr,
                bool(
                    getattr(e.control, "value", None)
                    if e.control is not None
                    else e.data in {"true", "True", True}
                ),
            )
            toggle_cards.append(
                self._build_card(
                    title=spec.title,
                    description=spec.description,
                    content=toggle,
                )
            )

        self._cards = [slider_card, *toggle_cards]
        self._options_host = ft.Container()

        body = ft.Column(
            spacing=16,
            controls=[heading, self._options_host],
        )
        self._root = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            border_radius=12,
            content=body,
            tooltip="Panel para configurar accesibilidad",
        )

    # ------------------------------------------------------------------
    def _build_card(self, *, title: str, description: str, content: ft.Control) -> ft.Container:
        return ft.Container(
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.04, _ACCESSIBLE_SURFACE),
            padding=ft.padding.all(12),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text(title, weight=ft.FontWeight.W_600),
                    ft.Text(description, size=12, color=ft.Colors.with_opacity(0.7, _ACCESSIBLE_SURFACE)),
                    content,
                ],
            ),
        )

    # ------------------------------------------------------------------
    def _handle_toggle(self, attribute: str, enabled: bool) -> None:
        if bool(getattr(self.preferences, attribute)) == bool(enabled):
            return
        setattr(self.preferences, attribute, bool(enabled))
        self._apply_preferences()

    def _apply_preferences(self) -> None:
        if not self._page:
            return
        self.preferences.apply(self._page, self.theme)
        if self.on_change:
            self.on_change(self.preferences)

    def _handle_width_change(self, width: int) -> None:
        self._set_orientation("row" if width >= self.horizontal_breakpoint else "column")

    def _set_orientation(self, mode: str) -> None:
        if self._layout_mode == mode and self._options_host and self._options_host.content:
            return
        self._layout_mode = mode
        if not self._options_host:
            return

        for card in self._cards:
            card.expand = 1 if mode == "row" else False

        if mode == "row":
            layout = ft.Row(
                controls=self._cards,
                spacing=12,
                run_spacing=12,
                wrap=True,
            )
        else:
            layout = ft.Column(
                controls=self._cards,
                spacing=12,
            )
        self._options_host.content = layout
        if self._page:
            self._page.update()
