import flet as ft
from fletplus.components.charts import LineChart
from types import SimpleNamespace


def test_line_chart_build_and_interactions():
    data = [(0, 0), (1, 2), (2, 1)]
    chart = LineChart(data, x_range=(0, 2), y_range=(0, 2))
    control = chart.build()

    # Verificar construcción
    assert isinstance(control, ft.Stack)
    assert len(chart.canvas.shapes) == len(data) - 1 + 2  # líneas + ejes

    # Zoom con scroll
    before = chart.scale
    chart._on_wheel(SimpleNamespace(delta_y=-1))
    assert chart.scale > before

    # Tooltip al pasar el ratón
    chart._on_hover(SimpleNamespace(local_x=0, local_y=chart.height))
    assert chart.tooltip.visible
    assert chart.tooltip.value.startswith("0")


def test_line_chart_axis_customization():
    data = [(0, 0)]
    chart = LineChart(data, x_range=(0, 10), y_range=(-1, 1))
    assert chart.x_min == 0
    assert chart.x_max == 10
    assert chart.y_min == -1
    assert chart.y_max == 1
