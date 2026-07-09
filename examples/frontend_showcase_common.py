"""Helpers compartidos para las demos frontend por plataforma."""
from __future__ import annotations
from dataclasses import dataclass
import flet as ft
from examples._bootstrap import ensure_project_root
ensure_project_root()
from fletplus import FrontEndConfig  # noqa: E402
from fletplus.components import AdaptiveDestination, AdaptiveNavigationLayout, EmptyState, LoadingState, ResponsiveContainer, ResponsiveGrid, ResponsiveGridItem, SuccessState  # noqa: E402
from fletplus.styles import Style  # noqa: E402
from fletplus.utils.responsive_style import ResponsiveStyle  # noqa: E402

@dataclass(frozen=True)
class ShowcaseProfile:
    """Configuración visual de una demo frontend."""
    title: str
    eyebrow: str
    description: str
    width: int
    platform_label: str
    asset_fit: ft.ImageFit = ft.ImageFit.COVER

PALETTE = {"primary": "#2563EB", "secondary": "#7C3AED", "tertiary": "#14B8A6", "surface": "#F8FAFC", "surface_variant": "#E2E8F0", "background": "#EEF2FF", "error": "#DC2626"}

def _card(title: str, value: str, icon: str, accent: str) -> ft.Container:
    return ft.Container(padding=18, border_radius=18, bgcolor=ft.Colors.with_opacity(0.10, accent), border=ft.border.all(1, ft.Colors.with_opacity(0.22, accent)), content=ft.Column([ft.Icon(icon, color=accent, size=28), ft.Text(value, size=26, weight=ft.FontWeight.BOLD), ft.Text(title, size=13, opacity=0.75)], spacing=8, tight=True))

def _status_strip(theme) -> ft.Control:
    return ft.ResponsiveRow([
        ft.Container(LoadingState(theme=theme, title="Sincronizando").build(None), col={"xs": 12, "md": 4}),
        ft.Container(SuccessState(theme=theme, title="Publicado").build(None), col={"xs": 12, "md": 4}),
        ft.Container(EmptyState(theme=theme, title="Sin alertas", description="Los estados futuros encajan en el mismo bloque.").build(None), col={"xs": 12, "md": 4}),
    ], spacing=12, run_spacing=12)

def build_showcase(page: ft.Page, profile: ShowcaseProfile) -> None:
    """Construye una demo con navegación, tema y layout responsive."""
    page.title = profile.title
    page.width = page.width or profile.width
    page.theme_mode = ft.ThemeMode.LIGHT
    page.assets_dir = "examples/assets"
    page.scroll = ft.ScrollMode.AUTO
    frontend = FrontEndConfig(palette=PALETTE, page_padding=16, max_content_width=1180, font_family="Inter", theme_tokens={"colors": {"surface_soft": ft.Colors.with_opacity(0.08, PALETTE["primary"]), "muted": "#64748B"}, "spacing": {"default": 16}, "typography": {"title_size": 30, "body_size": 15}})
    theme = frontend.apply_to_page(page)

    def toggle_theme(_event: ft.ControlEvent) -> None:
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        page.update()

    hero_style = ResponsiveStyle(width={0: Style(padding=18, border_radius=22), 720: Style(padding=28, border_radius=28), 1040: Style(padding=34, border_radius=32)}, base=Style(bgcolor=ft.Colors.with_opacity(0.08, PALETTE["secondary"])))

    def metrics_grid() -> ft.Control:
        return ResponsiveGrid(items=[
            ResponsiveGridItem(_card("Conversión", "8.4%", ft.Icons.INSIGHTS, PALETTE["primary"]), span_devices={"mobile": 12, "tablet": 6, "desktop": 3}),
            ResponsiveGridItem(_card("Sesiones", "24K", ft.Icons.GROUP, PALETTE["secondary"]), span_devices={"mobile": 12, "tablet": 6, "desktop": 3}),
            ResponsiveGridItem(_card("Latencia", "96ms", ft.Icons.SPEED, PALETTE["tertiary"]), span_devices={"mobile": 12, "tablet": 6, "desktop": 3}),
            ResponsiveGridItem(_card("Tareas", "312", ft.Icons.TASK_ALT, ft.Colors.ORANGE), span_devices={"mobile": 12, "tablet": 6, "desktop": 3}),
        ], spacing=14, run_spacing=14).build(page.width)

    def overview() -> ft.Control:
        hero = ResponsiveContainer(ft.ResponsiveRow([
            ft.Container(ft.Column([ft.Text(profile.eyebrow.upper(), size=12, weight=ft.FontWeight.BOLD, color=PALETTE["secondary"]), ft.Text("Frontend listo para producción", size=34, weight=ft.FontWeight.BOLD), ft.Text(profile.description, size=16, opacity=0.8), ft.Row([ft.FilledButton("Explorar"), ft.OutlinedButton("Documentación")], wrap=True)], spacing=12), col={"xs": 12, "md": 7}),
            ft.Container(ft.Image(src="fletplus_showcase.svg", fit=profile.asset_fit, border_radius=20), col={"xs": 12, "md": 5}),
        ], spacing=18, run_spacing=18), hero_style).build(page)
        return ft.Column([hero, metrics_grid()], spacing=18)

    def content_builder(index: int, device: str) -> ft.Control:
        sections = [overview(), ft.Column([ft.Text("Tarjetas responsivas", size=28, weight=ft.FontWeight.BOLD), metrics_grid()], spacing=16), ft.Column([ft.Text("Estados de UI", size=28, weight=ft.FontWeight.BOLD), _status_strip(theme)], spacing=16)]
        return ft.Container(sections[index], padding=18, expand=True)

    header = ft.Row([ft.Text(profile.platform_label, size=20, weight=ft.FontWeight.BOLD), ft.Container(expand=True), ft.TextButton("Light / Dark", icon=ft.Icons.DARK_MODE, on_click=toggle_theme)])
    layout = AdaptiveNavigationLayout(destinations=[AdaptiveDestination("Inicio", ft.Icons.HOME_OUTLINED, ft.Icons.HOME), AdaptiveDestination("Tarjetas", ft.Icons.DASHBOARD_OUTLINED, ft.Icons.DASHBOARD), AdaptiveDestination("Estados", ft.Icons.CHECK_CIRCLE_OUTLINE, ft.Icons.CHECK_CIRCLE)], content_builder=content_builder, header=header, theme=theme, floating_action_button=ft.FloatingActionButton(icon=ft.Icons.ADD, text="Crear"))
    page.add(layout.build(page))
