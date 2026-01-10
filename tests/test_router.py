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


def test_router_prefers_static_over_dynamic():
    static_view = ft.Text("Static settings")

    router = Router(
        [
            Route(
                path="/items/<item_id>",
                view=lambda match: ft.Text(f"Item {match.param('item_id')}")
            ),
            Route(path="/items/settings", view=lambda match: static_view),
        ]
    )

    rendered: list[ft.Control] = []
    router.observe(lambda _match, control: rendered.append(control))

    router.go("/items/settings")
    assert rendered[-1] is static_view

    router.go("/items/42")
    assert isinstance(rendered[-1], ft.Text)
    assert rendered[-1].value == "Item 42"


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


def test_router_dynamic_param_collision():
    router = Router()
    router.register(Route(path="/items/<item_id>", view=lambda match: ft.Text("Item")))

    with pytest.raises(ValueError, match="Colisión de parámetros dinámicos"):
        router.register(Route(path="/items/<other_id>", view=lambda match: ft.Text("Otro")))


def test_router_match_consistency_between_impls():
    router = Router(
        [
            Route(path="/static", view=lambda match: ft.Text("Static")),
            Route(path="/items/<item_id>", view=lambda match: ft.Text(match.param("item_id"))),
        ]
    )

    from fletplus.router import router as router_mod

    paths = ["/static", "/items/1", "/items/abc"]

    def normalize(results):
        normalized = []
        for path_nodes in results:
            normalized.append([(node.full_path, params) for node, params in path_nodes])
        return normalized

    base_results = [normalize(router._match(path)) for path in paths]
    py_results = [normalize(router_mod._match_py(router._root, path)) for path in paths]

    # Si la implementación en C está disponible, verificamos también su salida.
    cy_module = router_mod._router_cy
    if cy_module is not None:
        cy_results = [normalize(cy_module._match(router._root, path)) for path in paths]
        assert cy_results == base_results

    assert py_results == base_results
