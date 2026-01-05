from __future__ import annotations

import flet as ft
import pytest

from fletplus.components import responsive_grid
from fletplus.components.responsive_grid import ResponsiveGrid, ResponsiveGridItem
from fletplus.components.responsive_grid_rs import plan_items
from fletplus.styles import Style
from fletplus.utils.responsive_style import ResponsiveStyle


@pytest.mark.skipif(plan_items is None, reason="Extensión nativa no disponible")
def test_native_plan_items_matches_python_logic():
    items = [
        ResponsiveGridItem(
            ft.Text("Desktop"),
            span=6,
            visible_devices=["desktop"],
        ),
        ResponsiveGridItem(
            ft.Text("Flex"),
            span_breakpoints={0: 12, 800: 4},
            hidden_devices=["tablet"],
        ),
        ResponsiveGridItem(
            ft.Text("Styled"),
            span_devices={"mobile": 12, "desktop": 3},
            min_width=500,
            responsive_style=ResponsiveStyle(width={0: Style(bgcolor="#fff")}),
        ),
    ]

    width = 900
    columns = 3
    device = "desktop"

    payload = [
        {
            "index": idx,
            "span": item.span,
            "span_breakpoints": dict(item.span_breakpoints or {}),
            "span_devices": dict(item.span_devices or {}),
            "visible_devices": list(item.visible_devices) if item.visible_devices else None,
            "hidden_devices": list(item.hidden_devices) if item.hidden_devices else None,
            "min_width": item.min_width,
            "max_width": item.max_width,
            "has_responsive_style": isinstance(item.responsive_style, (ResponsiveStyle, dict)),
        }
        for idx, item in enumerate(items)
    ]

    native_result = plan_items(width, columns, device, payload)
    expected = [
        {
            "index": idx,
            "col": item.resolve_span(width, columns, device),
            "has_responsive_style": isinstance(item.responsive_style, (ResponsiveStyle, dict)),
        }
        for idx, item in enumerate(items)
        if item.is_visible(width, device)
    ]

    assert native_result == expected


def test_build_row_uses_native_descriptors(monkeypatch):
    grid = ResponsiveGrid(items=[ResponsiveGridItem(ft.Text("A"), span=6)])

    def fake_planner(width: int, columns: int, device: str, payload: object):  # noqa: ARG001
        return [{"index": 0, "col": 5, "has_responsive_style": False}]

    monkeypatch.setattr(responsive_grid, "_plan_grid_items_native", fake_planner)

    row = grid._build_row(800)
    assert len(row.controls) == 1
    assert row.controls[0].col == 5
