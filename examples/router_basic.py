"""Ejemplo mínimo de uso del Router de FletPlus."""

import flet as ft

from fletplus import FletPlusApp, Route, Router, LayoutInstance


def dashboard_layout(_match):
    content_slot = ft.Container(expand=True, padding=20)
    shell = ft.Column(
        [
            ft.Text("Panel de control", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(opacity=0.2),
            content_slot,
        ],
        expand=True,
        spacing=12,
    )

    def mount(child: ft.Control | None) -> None:
        content_slot.content = child

    return LayoutInstance(root=shell, _mount=mount)


def build_router() -> Router:
    return Router(
        [
            Route(path="/", view=lambda match: ft.Text("Bienvenido a FletPlus")),
            Route(
                path="/dashboard",
                layout=dashboard_layout,
                children=[
                    Route(path="overview", name="Overview", view=lambda match: ft.Text("Resumen")),
                    Route(
                        path="users/<user_id>",
                        name="Detalle de usuario",
                        view=lambda match: ft.Text(f"Usuario activo: {match.param('user_id')}")
                    ),
                ],
            ),
        ]
    )


def main(page: ft.Page) -> None:
    router = build_router()
    sidebar_items = [
        {"title": "Inicio", "icon": ft.Icons.HOME, "path": "/"},
        {
            "title": "Dashboard",
            "icon": ft.Icons.DASHBOARD,
            "path": "/dashboard/overview",
            "match": "/dashboard",
        },
    ]

    app = FletPlusApp(page, router, sidebar_items=sidebar_items, title="Router Demo")
    app.build()


if __name__ == "__main__":
    ft.app(target=main)
