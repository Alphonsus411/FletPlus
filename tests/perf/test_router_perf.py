"""Benchmarks ligeros para el enrutador."""
from __future__ import annotations

import time

import flet as ft
import pytest

from fletplus.router import Route, Router


def _build_nested_router() -> Router:
    def make_leaf(label: str):
        return Route(path=label, view=lambda match, lbl=label: ft.Text(f"{lbl}:{match.path}"))

    settings_children = [make_leaf("general"), make_leaf("security"), make_leaf("notifications")]
    user_children = [Route(path="<user_id>", children=[make_leaf("profile"), make_leaf("activity")])]

    router = Router(
        [
            Route(path="/", view=lambda match: ft.Text("root")),
            Route(
                path="/dashboard",
                view=lambda match: ft.Text("dashboard"),
                children=[Route(path="reports", children=[make_leaf("sales"), make_leaf("ops")])],
            ),
            Route(path="/settings", children=settings_children),
            Route(path="/users", children=user_children),
        ]
    )
    return router


@pytest.mark.perf
@pytest.mark.parametrize("repeats", [50])
@pytest.mark.parametrize("paths", [[
    "/dashboard/reports/sales",
    "/dashboard/reports/ops",
    "/settings/security",
    "/settings/general",
    "/users/42/profile",
    "/users/7/activity",
]])
def test_router_perf_baseline(paths: list[str], repeats: int, capsys: pytest.CaptureFixture[str]):
    router = _build_nested_router()

    def measure_go():
        start = time.perf_counter()
        for _ in range(repeats):
            for path in paths:
                router.go(path)
        return (time.perf_counter() - start) / (repeats * len(paths))

    def measure_replace():
        start = time.perf_counter()
        for _ in range(repeats):
            for path in paths:
                router.replace(path)
        return (time.perf_counter() - start) / (repeats * len(paths))

    go_avg = measure_go()
    replace_avg = measure_replace()

    # Validación funcional mínima tras las iteraciones de rendimiento
    assert router.current_path == paths[-1]
    assert isinstance(router.active_match.node.view_builder(router.active_match), ft.Text)

    metrics = {
        "paths": len(paths),
        "repeats": repeats,
        "avg_go_seconds": go_avg,
        "avg_replace_seconds": replace_avg,
    }
    print(f"Router benchmark: {metrics}")
    captured = capsys.readouterr()
    assert "Router benchmark" in captured.out
    assert all(value > 0 for value in metrics.values() if isinstance(value, float))
