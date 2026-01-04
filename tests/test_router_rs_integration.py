import pytest

from fletplus.router import Route, Router
from fletplus.router import router as router_mod

router_rs = pytest.importorskip("fletplus.router.router_rs")


def _normalize(results):
    normalized = []
    for path_nodes in results:
        normalized.append([(node.full_path, params) for node, params in path_nodes])
    return normalized


def test_rust_and_python_match_dynamic_params():
    router = Router(
        [
            Route(path="/users/<user_id>", view=lambda match: match.path),
            Route(path="/users/<user_id>/posts/<post_id>", view=lambda match: match.path),
        ]
    )

    paths = ["/users/42", "/users/5/posts/99"]
    rust_results = [_normalize(router_rs._match(router._root, path)) for path in paths]
    py_results = [_normalize(router_mod._match_py(router._root, path)) for path in paths]

    assert rust_results == py_results


def test_rust_and_python_match_nested_routes():
    router = Router(
        [
            Route(
                path="/app",
                view=lambda match: match.path,
                children=[Route(path="settings/profile", view=lambda match: match.path)],
            )
        ]
    )

    rust_results = _normalize(router_rs._match(router._root, "/app/settings/profile"))
    py_results = _normalize(router_mod._match_py(router._root, "/app/settings/profile"))

    assert rust_results == py_results


def test_rust_match_returns_empty_for_missing_routes():
    router = Router([Route(path="/", view=lambda match: match.path)])

    rust_results = router_rs._match(router._root, "/missing/route")
    py_results = router_mod._match_py(router._root, "/missing/route")

    assert rust_results == py_results == []
