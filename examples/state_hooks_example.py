"""Ejemplo práctico de los nuevos hooks reactivos de FletPlus."""

from __future__ import annotations

import flet as ft

from examples import ensure_project_root


ensure_project_root()

from fletplus import FletPlusApp  # noqa: E402
from fletplus.state import Signal, reactive, use_signal, use_state, watch  # noqa: E402


global_counter = Signal(0)


class ReactiveCounter(ft.UserControl):
    def __init__(self) -> None:
        super().__init__()
        self.global_signal = global_counter
        self._total_text = ft.Text()
        self._summary_text = ft.Text()
        self._hooks_registered = False

    @reactive
    def build(self) -> ft.Control:
        local = use_state(0)
        shared = use_signal(self.global_signal)

        local_text = ft.Text()
        local.bind_control(local_text, attr="value", transform=lambda value: f"Clicks locales: {value}")

        if not self._hooks_registered:
            def update_shared(value: int) -> None:
                self._total_text.value = f"Contador global: {value}"

            def update_summary(local_value: int, shared_value: int) -> None:
                self._summary_text.value = f"Suma reactiva: {local_value + shared_value}"

            watch(self.global_signal, update_shared)
            watch((local, shared), update_summary)
            self._hooks_registered = True

        def increment_local(_event) -> None:
            local.set(local.get() + 1)

        def increment_global(_event) -> None:
            self.global_signal.set(self.global_signal.get() + 1)

        return ft.Container(
            padding=20,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.PRIMARY),
            border_radius=16,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text("Hooks reactivos en acción", weight=ft.FontWeight.W_600, size=18),
                    local_text,
                    self._total_text,
                    self._summary_text,
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.FilledButton("Sumar local", on_click=increment_local),
                            ft.OutlinedButton("Sumar global", on_click=increment_global),
                        ],
                    ),
                ],
            ),
        )


def counter_view() -> ft.Control:
    return ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[ReactiveCounter()],
    )


def main(page: ft.Page) -> None:
    app = FletPlusApp(page, {"Inicio": counter_view}, title="Estado reactivo")
    app.build()


if __name__ == "__main__":
    ft.app(target=main)
