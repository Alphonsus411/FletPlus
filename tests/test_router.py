import flet as ft
import pytest

from fletplus.router import Route, Router, layout_from_attribute


def test_router_static_navigation():
    router = Router(
        [
            Route(path="/home", view=lambda match: ft.Text("Home")),
            Route(path="/about", view=lambda match: ft.Text("About")),
        ]
    )

    results: list[ft.Control] = []
    router.observe(lambda _match, control: results.append(control))

    router.go("/home")
    assert isinstance(results[-1], ft.Text)
    assert results[-1].value == "Home"
    assert router.current_path == "/home"

    router.go("/about")
    assert isinstance(results[-1], ft.Text)
    assert results[-1].value == "About"
    assert router.current_path == "/about"

    router.back()
    assert isinstance(results[-1], ft.Text)
    assert results[-1].value == "Home"
    assert router.current_path == "/home"

    router.replace("/about")
    assert isinstance(results[-1], ft.Text)
    assert results[-1].value == "About"
    assert router.current_path == "/about"


def test_router_dynamic_params():
    router = Router(
        [
            Route(
                path="/users/<user_id>",
                view=lambda match: ft.Text(f"Usuario {match.param('user_id')}")
            ),
        ]
    )
    captured: list[ft.Text] = []
    router.observe(lambda _match, control: captured.append(control))

    router.go("/users/42")
    assert captured[-1].value == "Usuario 42"

    router.go("/users/99")
    assert captured[-1].value == "Usuario 99"

    router.back()
    assert captured[-1].value == "Usuario 42"


def test_router_nested_layout_persistence():
    container = ft.Container()

    def dashboard_layout(match):
        return layout_from_attribute(container, "content")

    router = Router(
        [
            Route(
                path="/dashboard",
                layout=dashboard_layout,
                children=[
                    Route(path="overview", view=lambda match: ft.Text("Overview")),
                    Route(path="settings", view=lambda match: ft.Text("Settings")),
                ],
            )
        ]
    )

    rendered: list[ft.Control] = []
    router.observe(lambda _match, control: rendered.append(control))

    router.go("/dashboard/overview")
    first_control = rendered[-1]
    assert first_control is container
    assert isinstance(container.content, ft.Text)
    assert container.content.value == "Overview"

    router.go("/dashboard/settings")
    assert rendered[-1] is container
    assert container.content.value == "Settings"


def test_router_unsubscribe():
    router = Router([Route(path="/", view=lambda match: ft.Text("Root"))])
    triggered = []
    unsubscribe = router.observe(lambda _match, _control: triggered.append(True))

    router.go("/")
    assert triggered

    unsubscribe()
    router.go("/")
    assert len(triggered) == 1


def test_router_invalid_route():
    router = Router()

    with pytest.raises(ValueError):
        router.go("/unknown")
