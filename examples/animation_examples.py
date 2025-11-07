from __future__ import annotations

import flet as ft

from fletplus import (
    AnimatedContainer,
    FadeIn,
    FletPlusApp,
    Scale,
    SlideTransition,
    animation_controller_context,
)


def animated_dashboard() -> ft.Control:
    controller = animation_controller_context.get()
    expanded_state = {"expanded": False}

    def toggle_card(_e: ft.ControlEvent) -> None:
        expanded_state["expanded"] = not expanded_state["expanded"]
        if controller:
            controller.trigger("card_expand" if expanded_state["expanded"] else "card_collapse")

    hero = FadeIn(
        ft.Text("Animaciones con FletPlus", size=24, weight=ft.FontWeight.BOLD),
        duration=480,
        curve=ft.AnimationCurve.EASE_IN_OUT,
    )
    subtitle = SlideTransition(
        ft.Text("Coordinadas con AnimationController y contextos"),
        begin=ft.transform.Offset(0, 0.2),
        end=ft.transform.Offset(0, 0),
    )
    pulse_button = Scale(
        ft.ElevatedButton("Lanzar pulso", on_click=lambda _e: controller and controller.trigger("pulse")),
        trigger="pulse",
        reverse_trigger=None,
        begin=ft.transform.Scale(1, 1),
        end=ft.transform.Scale(1.1, 1.1),
    )
    animated_card = AnimatedContainer(
        ft.Column(
            controls=[
                ft.Text("Panel informativo"),
                ft.Text("Cambia su tamaño con eventos personalizados."),
            ],
            tight=True,
        ),
        duration=360,
        curve=ft.AnimationCurve.EASE_IN_OUT,
        begin={"padding": ft.padding.all(12), "bgcolor": ft.Colors.with_opacity(0.05, ft.Colors.BLUE)},
        end={"padding": ft.padding.all(24), "bgcolor": ft.Colors.with_opacity(0.15, ft.Colors.BLUE)},
        trigger="card_expand",
        reverse_trigger="card_collapse",
    )

    toggle = ft.OutlinedButton("Alternar tarjeta", on_click=toggle_card)

    return ft.Column(
        spacing=20,
        controls=[hero, subtitle, pulse_button, animated_card, toggle],
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )


def main(page: ft.Page) -> None:
    page.title = "Demo animaciones FletPlus"
    routes = {"/": animated_dashboard}
    FletPlusApp(page, routes, title="Animaciones FletPlus")


if __name__ == "__main__":
    ft.app(target=main)
