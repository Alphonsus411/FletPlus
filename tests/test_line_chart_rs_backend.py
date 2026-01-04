import pytest
from fletplus.components.charts import line_chart as lc

backend = pytest.importorskip("fletplus.components.charts.line_chart_rs")

if backend.screen_points is None:  # pragma: no cover - entorno sin compilación Rust
    pytest.skip("backend Rust no disponible", allow_module_level=True)


def test_rust_matches_python_normal_range():
    data = [(0.0, 0.0), (1.0, 2.0), (2.0, 1.0)]
    args = (0.0, 2.0, 0.0, 2.0, 400.0, 300.0, 1.0)

    rust_points = backend.screen_points(data, *args)
    python_points = lc._screen_points_py(data, *args)

    assert rust_points == pytest.approx(python_points)

    rust_nearest = backend.nearest_point(rust_points, 100.0, 150.0)
    python_nearest = lc._nearest_point_py(python_points, 100.0, 150.0)

    assert rust_nearest == python_nearest


def test_rust_matches_zero_span_and_extreme_scale():
    data = [(1.0, 2.0), (1.0, 3.0)]
    args_zero_span = (1.0, 1.0, 2.0, 3.0, 200.0, 100.0, 1.0)

    rust_zero = backend.screen_points(data, *args_zero_span)
    py_zero = lc._screen_points_py(data, *args_zero_span)
    assert rust_zero == pytest.approx(py_zero)

    args_extreme_scale = (0.0, 2.0, -1.0, 1.0, 200.0, 100.0, 0.001)
    rust_scaled = backend.screen_points(data, *args_extreme_scale)
    py_scaled = lc._screen_points_py(data, *args_extreme_scale)
    assert rust_scaled == pytest.approx(py_scaled)

    rust_nearest = backend.nearest_point(rust_scaled, 0.0, 0.0)
    py_nearest = lc._nearest_point_py(py_scaled, 0.0, 0.0)
    assert rust_nearest == py_nearest
