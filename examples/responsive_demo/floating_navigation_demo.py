"""Demostración de navegación flotante responsiva usando FletPlusApp."""

import flet as ft

from fletplus import FletPlusApp, FloatingMenuOptions, ResponsiveNavigationConfig


def _section(title: str, description: str, icon: str) -> ft.Control:
    return ft.Container(
        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.PRIMARY),
        padding=ft.Padding(24, 32, 24, 32),
        border_radius=ft.border_radius.all(26),
        content=ft.Column(
            spacing=16,
            controls=[
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(icon, size=28, color=ft.Colors.PRIMARY),
                        ft.Text(title, size=22, weight=ft.FontWeight.W_600),
                    ],
                ),
                ft.Text(description, size=14, color=ft.Colors.with_opacity(0.8, ft.Colors.ON_SURFACE)),
                ft.Row(
                    controls=[
                        ft.Chip(label=ft.Text("breakpoints")),
                        ft.Chip(label=ft.Text("animaciones")),
                        ft.Chip(label=ft.Text("floating menu")),
                    ]
                ),
            ],
        ),
    )


def home_view() -> ft.Control:
    return ft.Column(
        spacing=24,
        controls=[
            ft.Text("Menú flotante activado bajo 680px", size=18, weight=ft.FontWeight.W_600),
            ft.Text(
                "Reduce el ancho de la ventana para ver cómo el menú lateral se convierte en un botón flotante que abre un panel deslizante.",
                color=ft.Colors.with_opacity(0.75, ft.Colors.ON_SURFACE),
            ),
            _section(
                "Resumen",
                "Configura la posición, ancho y color del panel flotante utilizando FloatingMenuOptions.",
                ft.Icons.DASHBOARD,
            ),
        ],
    )


def analytics_view() -> ft.Control:
    return ft.Column(
        spacing=20,
        controls=[
            ft.Text("Analítica", size=18, weight=ft.FontWeight.W_600),
            ft.ProgressRing(value=0.72, width=120, height=120),
            ft.Text("Los accesos móviles aumentaron 35% tras habilitar el menú flotante."),
        ],
    )


def profile_view() -> ft.Control:
    return ft.Column(
        spacing=18,
        controls=[
            ft.Text("Perfil de usuario", size=18, weight=ft.FontWeight.W_600),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.PHONE_ANDROID),
                title=ft.Text("Preferir navegación flotante en móviles"),
                subtitle=ft.Text("Se activa automáticamente por debajo del breakpoint configurado."),
            ),
            ft.Switch(label="Notificar cambios de diseño", value=True),
        ],
    )


floating_options = FloatingMenuOptions(
    width=320,
    horizontal_margin=18,
    vertical_margin=24,
    fab_icon=ft.Icons.MENU_OPEN,
)

responsive_nav = ResponsiveNavigationConfig(
    mobile_breakpoint=760,
    tablet_breakpoint=1024,
    floating_breakpoint=680,
    floating_options=floating_options,
)


def main(page: ft.Page) -> None:
    app = FletPlusApp(
        page,
        {
            "Inicio": home_view,
            "Analítica": analytics_view,
            "Perfil": profile_view,
        },
        sidebar_items=[
            {"title": "Inicio", "icon": ft.Icons.HOME},
            {"title": "Analítica", "icon": ft.Icons.INSIGHTS},
            {"title": "Perfil", "icon": ft.Icons.PERSON},
        ],
        title="Demo navegación flotante",
        responsive_navigation=responsive_nav,
    )
    app.build()


if __name__ == "__main__":
    ft.app(target=main)
