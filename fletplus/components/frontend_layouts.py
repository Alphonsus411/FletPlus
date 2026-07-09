"""Componentes de layout frontend basados en perfiles y tokens de FletPlus."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import flet as ft

from fletplus.frontend.config import FrontEndConfig
from fletplus.utils.device_profiles import DeviceProfile, get_device_profile
from fletplus.utils.flet_compat import get_page_width

if TYPE_CHECKING:
    from fletplus.themes.theme_manager import ThemeManager

SpacingValue = int | float | ft.Padding | Mapping[str, int | float] | None
DeviceMap = Mapping[str, int | float | None]
TextLike = ft.Control | str


def _frontend_config(config: FrontEndConfig | None) -> FrontEndConfig:
    return config or FrontEndConfig()


def _text_style(
    config: FrontEndConfig | None, role: str, page: ft.Page
) -> ft.TextStyle:
    return _frontend_config(config).text_style(role, int(get_page_width(page) or 0))


def _text_control(
    value: TextLike, *, config: FrontEndConfig | None, role: str, page: ft.Page
) -> ft.Control:
    if isinstance(value, str):
        return ft.Text(value, style=_text_style(config, role, page))
    return value


def _device_key(name: str) -> str:
    return str(name).strip().lower()


def _token(
    theme: "ThemeManager | None", group: str, name: str, default: object = None
) -> object:
    if theme is None:
        return default
    tokens = getattr(theme, "tokens", {})
    effective = getattr(theme, "_effective_tokens", tokens)
    if isinstance(effective, Mapping):
        group_tokens = effective.get(group, {})
        if isinstance(group_tokens, Mapping) and name in group_tokens:
            return group_tokens[name]
    if isinstance(tokens, Mapping):
        group_tokens = tokens.get(group, {})
        if isinstance(group_tokens, Mapping):
            return group_tokens.get(name, default)
    return default


def _color(
    theme: "ThemeManager | None", token: str | None, default: str | None = None
) -> str | None:
    if not token:
        return default
    if theme is not None:
        value = theme.get_color(token, None)
        if isinstance(value, str):
            return value
    return default if default is not None else token


def _number(value: object, default: int | float) -> int | float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _padding(value: SpacingValue, fallback: int | float) -> ft.Padding:
    if isinstance(value, ft.Padding):
        return value
    if isinstance(value, Mapping):
        return ft.Padding(
            _number(value.get("left"), fallback),
            _number(value.get("top"), fallback),
            _number(value.get("right"), fallback),
            _number(value.get("bottom"), fallback),
        )
    amount = _number(value, fallback) if value is not None else fallback
    return ft.Padding(amount, amount, amount, amount)


@dataclass(slots=True)
class LayoutTokens:
    """Valores resueltos para el perfil activo de un layout frontend."""

    profile: DeviceProfile
    spacing: int
    padding: ft.Padding
    max_width: int | None
    columns: int


def resolve_layout_tokens(
    page: ft.Page,
    *,
    config: FrontEndConfig | None = None,
    theme: "ThemeManager | None" = None,
    spacing: int | None = None,
    padding: SpacingValue = None,
    max_width: int | None = None,
    columns: int | None = None,
    spacing_by_device: DeviceMap | None = None,
    padding_by_device: Mapping[str, SpacingValue] | None = None,
    max_width_by_device: DeviceMap | None = None,
    columns_by_device: Mapping[str, int] | None = None,
    profiles: Sequence[DeviceProfile] | None = None,
) -> LayoutTokens:
    """Resuelve spacing, padding, ancho máximo y columnas para la página."""

    frontend = config or FrontEndConfig()
    width = int(get_page_width(page) or frontend.max_content_width)
    active_profiles = tuple(profiles or frontend.responsive_profiles)
    profile = get_device_profile(width, active_profiles)
    name = _device_key(profile.name)
    screen_tokens = config.screen_tokens_for_page(page) if config is not None else {}

    theme_spacing = _token(theme, "spacing", "default", frontend.spacing)
    base_spacing = int(_number(theme_spacing, frontend.spacing))
    token_spacing = screen_tokens.get("spacing")
    resolved_spacing = (
        int(_number(token_spacing, base_spacing))
        if token_spacing is not None
        else base_spacing
    )
    if spacing_by_device and spacing_by_device.get(name) is not None:
        resolved_spacing = int(_number(spacing_by_device[name], resolved_spacing))
    if spacing is not None:
        resolved_spacing = int(spacing)

    base_padding = frontend.page_padding
    token_padding = screen_tokens.get("padding", screen_tokens.get("page_padding"))
    resolved_padding_value: SpacingValue = (
        token_padding if token_padding is not None else base_padding
    )
    if padding_by_device and name in padding_by_device:
        resolved_padding_value = padding_by_device[name]
    if padding is not None:
        resolved_padding_value = padding
    resolved_padding = _padding(resolved_padding_value, base_padding)

    if "max_width" in screen_tokens:
        token_max_width = screen_tokens["max_width"]
        resolved_max_width = (
            None
            if token_max_width is None
            else int(_number(token_max_width, frontend.max_content_width))
        )
    else:
        resolved_max_width = frontend.max_content_width
    if max_width_by_device and name in max_width_by_device:
        device_width = max_width_by_device[name]
        resolved_max_width = (
            None
            if device_width is None
            else int(
                _number(device_width, resolved_max_width or frontend.max_content_width)
            )
        )
    if max_width is not None:
        resolved_max_width = max_width

    token_columns = screen_tokens.get("columns")
    resolved_columns = (
        int(_number(token_columns, profile.columns))
        if token_columns is not None
        else profile.columns
    )
    if columns_by_device and name in columns_by_device:
        resolved_columns = int(columns_by_device[name])
    if columns is not None:
        resolved_columns = columns

    return LayoutTokens(
        profile,
        resolved_spacing,
        resolved_padding,
        resolved_max_width,
        resolved_columns,
    )


@dataclass(slots=True)
class Section:
    """Sección vertical con cabecera opcional y tokens responsive."""

    content: ft.Control | Sequence[ft.Control] = field(default_factory=tuple)
    title: str | None = None
    subtitle: str | None = None
    actions: Sequence[ft.Control] = field(default_factory=tuple)
    config: FrontEndConfig | None = None
    theme: "ThemeManager | None" = None
    spacing: int | None = None
    padding: SpacingValue = None
    max_width: int | None = None
    spacing_by_device: DeviceMap | None = None
    padding_by_device: Mapping[str, SpacingValue] | None = None
    max_width_by_device: DeviceMap | None = None
    bgcolor_token: str | None = None
    bgcolor: str | None = None
    border_radius: int | float | ft.BorderRadius | None = None

    def build(self, page: ft.Page) -> ft.Container:
        tokens = resolve_layout_tokens(
            page,
            config=self.config,
            theme=self.theme,
            spacing=self.spacing,
            padding=self.padding,
            max_width=self.max_width,
            spacing_by_device=self.spacing_by_device,
            padding_by_device=self.padding_by_device,
            max_width_by_device=self.max_width_by_device,
        )
        controls: list[ft.Control] = []
        if self.title or self.subtitle or self.actions:
            title_controls: list[ft.Control] = []
            if self.title:
                title_controls.append(
                    ft.Text(self.title, style=_text_style(self.config, "title", page))
                )
            if self.subtitle:
                title_controls.append(
                    ft.Text(self.subtitle, style=_text_style(self.config, "body", page))
                )
            controls.append(
                ft.Row(
                    [ft.Column(title_controls, spacing=4, expand=True), *self.actions],
                    spacing=tokens.spacing,
                )
            )
        if isinstance(self.content, Sequence) and not isinstance(
            self.content, ft.Control
        ):
            controls.extend(self.content)
        else:
            controls.append(self.content)  # type: ignore[arg-type]
        return ft.Container(
            content=ft.Column(controls, spacing=tokens.spacing),
            padding=tokens.padding,
            width=tokens.max_width,
            bgcolor=_color(self.theme, self.bgcolor_token, self.bgcolor),
            border_radius=self.border_radius,
            alignment=ft.alignment.center,
        )


@dataclass(slots=True)
class CardGrid:
    """Grid de tarjetas que calcula columnas por perfil de dispositivo."""

    cards: Sequence[ft.Control]
    config: FrontEndConfig | None = None
    theme: "ThemeManager | None" = None
    spacing: int | None = None
    padding: SpacingValue = None
    max_width: int | None = None
    columns: int | None = None
    spacing_by_device: DeviceMap | None = None
    padding_by_device: Mapping[str, SpacingValue] | None = None
    max_width_by_device: DeviceMap | None = None
    columns_by_device: Mapping[str, int] | None = None

    def build(self, page: ft.Page) -> ft.Container:
        tokens = resolve_layout_tokens(
            page,
            config=self.config,
            theme=self.theme,
            spacing=self.spacing,
            padding=self.padding,
            max_width=self.max_width,
            columns=self.columns,
            spacing_by_device=self.spacing_by_device,
            padding_by_device=self.padding_by_device,
            max_width_by_device=self.max_width_by_device,
            columns_by_device=self.columns_by_device,
        )
        run_width = (
            None
            if tokens.max_width is None
            else max(
                1,
                int(
                    (tokens.max_width - (tokens.spacing * (tokens.columns - 1)))
                    / max(1, tokens.columns)
                ),
            )
        )
        return ft.Container(
            width=tokens.max_width,
            padding=tokens.padding,
            content=ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=card,
                        col={
                            "xs": 12,
                            "sm": max(1, 12 // max(1, min(tokens.columns, 12))),
                        },
                        width=run_width,
                    )
                    for card in self.cards
                ],
                spacing=tokens.spacing,
                run_spacing=tokens.spacing,
            ),
        )


@dataclass(slots=True)
class HeroSection(Section):
    """Sección destacada para portadas, landing pages o estados vacíos."""

    headline: str = ""
    description: str | None = None
    eyebrow: str | None = None
    primary_action: ft.Control | None = None
    secondary_action: ft.Control | None = None
    media: ft.Control | None = None

    def build(self, page: ft.Page) -> ft.Container:
        cfg = self.config or FrontEndConfig()
        width = get_page_width(page)
        body: list[ft.Control] = []
        if self.eyebrow:
            body.append(ft.Text(self.eyebrow, style=cfg.text_style("label", width)))
        body.append(ft.Text(self.headline, style=cfg.text_style("display", width)))
        if self.description:
            body.append(ft.Text(self.description, style=cfg.text_style("body", width)))
        actions = [
            control
            for control in (self.primary_action, self.secondary_action)
            if control is not None
        ]
        if actions:
            body.append(ft.Row(actions, spacing=12, wrap=True))
        content: ft.Control = (
            ft.Row([ft.Column(body, spacing=12, expand=True), self.media], spacing=24)
            if self.media
            else ft.Column(body, spacing=12)
        )
        self.content = content
        return Section.build(self, page)


@dataclass(slots=True)
class ToolbarSection(Section):
    """Barra de herramientas responsive con acciones alineadas."""

    leading: TextLike | None = None
    trailing: Sequence[TextLike] = field(default_factory=tuple)
    text_role: str = "label"

    def build(self, page: ft.Page) -> ft.Container:
        row_controls = []
        if self.leading:
            row_controls.append(
                ft.Container(
                    content=_text_control(
                        self.leading, config=self.config, role=self.text_role, page=page
                    ),
                    expand=True,
                )
            )
        row_controls.extend(
            _text_control(control, config=self.config, role=self.text_role, page=page)
            for control in self.trailing
        )
        self.content = ft.Row(
            row_controls,
            spacing=self.spacing or (self.config or FrontEndConfig()).spacing,
            wrap=True,
        )
        return Section.build(self, page)


@dataclass(slots=True)
class FooterSection(Section):
    """Pie de página con enlaces o metadatos."""

    links: Sequence[TextLike] = field(default_factory=tuple)
    caption: str | None = None
    caption_role: str = "caption"
    link_role: str = "label"

    def build(self, page: ft.Page) -> ft.Container:
        controls = (
            [self.content]
            if isinstance(self.content, ft.Control)
            else list(self.content)
        )
        if self.caption:
            controls.append(
                ft.Text(
                    self.caption,
                    style=_text_style(self.config, self.caption_role, page),
                )
            )
        if self.links:
            controls.append(
                ft.Row(
                    [
                        _text_control(
                            link, config=self.config, role=self.link_role, page=page
                        )
                        for link in self.links
                    ],
                    spacing=self.spacing or (self.config or FrontEndConfig()).spacing,
                    wrap=True,
                )
            )
        self.content = controls
        return Section.build(self, page)


@dataclass(slots=True)
class PageShell:
    """Shell de página que centra contenido y aplica límites responsive."""

    sections: Sequence[ft.Control | Section]
    config: FrontEndConfig | None = None
    theme: "ThemeManager | None" = None
    spacing: int | None = None
    padding: SpacingValue = None
    max_width: int | None = None
    spacing_by_device: DeviceMap | None = None
    padding_by_device: Mapping[str, SpacingValue] | None = None
    max_width_by_device: DeviceMap | None = None
    bgcolor_token: str | None = "background"
    bgcolor: str | None = None

    def build(self, page: ft.Page) -> ft.Container:
        tokens = resolve_layout_tokens(
            page,
            config=self.config,
            theme=self.theme,
            spacing=self.spacing,
            padding=self.padding,
            max_width=self.max_width,
            spacing_by_device=self.spacing_by_device,
            padding_by_device=self.padding_by_device,
            max_width_by_device=self.max_width_by_device,
        )
        built = [
            section.build(page) if hasattr(section, "build") else section
            for section in self.sections
        ]
        return ft.Container(
            expand=True,
            bgcolor=_color(self.theme, self.bgcolor_token, self.bgcolor),
            alignment=ft.alignment.top_center,
            content=ft.Container(
                width=tokens.max_width,
                padding=tokens.padding,
                content=ft.Column(
                    built, spacing=tokens.spacing, scroll=ft.ScrollMode.AUTO
                ),
            ),
        )


__all__ = [
    "LayoutTokens",
    "resolve_layout_tokens",
    "PageShell",
    "Section",
    "CardGrid",
    "HeroSection",
    "ToolbarSection",
    "FooterSection",
]
