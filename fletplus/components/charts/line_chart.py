from typing import List, Tuple, Optional

import flet as ft
import flet.canvas as cv

from fletplus.styles import Style
from .line_chart_rs import nearest_point as rs_nearest_point
from .line_chart_rs import screen_points as rs_screen_points
from .line_chart_rs import line_segments as rs_line_segments


def _screen_points_py(
    data: List[Tuple[float, float]],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    width: float,
    height: float,
    scale: float,
) -> List[Tuple[float, float]]:
    span_x = x_max - x_min
    span_y = y_max - y_min
    if span_x == 0:
        span_x = 1
    if span_y == 0:
        span_y = 1
    span_x *= scale
    span_y *= scale
    return [
        (
            (x - x_min) / span_x * width,
            height - (y - y_min) / span_y * height,
        )
        for x, y in data
    ]


def _screen_points(
    data: List[Tuple[float, float]],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    width: float,
    height: float,
    scale: float,
) -> List[Tuple[float, float]]:
    if rs_screen_points is not None:
        try:  # pragma: no cover - backend opcional
            return list(
                rs_screen_points(
                    data,
                    float(x_min),
                    float(x_max),
                    float(y_min),
                    float(y_max),
                    float(width),
                    float(height),
                    float(scale),
                )
            )
        except Exception:
            pass

    return _screen_points_py(data, x_min, x_max, y_min, y_max, width, height, scale)


def _nearest_point(points: List[Tuple[float, float]], x: float, y: float) -> Optional[Tuple[int, float]]:
    if not points:
        return None

    if rs_nearest_point is not None:
        try:  # pragma: no cover - backend opcional
            return rs_nearest_point(points, float(x), float(y))
        except Exception:
            pass

    return _nearest_point_py(points, x, y)


def _line_segments_py(points: List[Tuple[float, float]]) -> List[Tuple[float, float, float, float]]:
    return [
        (points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])
        for i in range(len(points) - 1)
    ]


def _line_segments(points: List[Tuple[float, float]]) -> List[Tuple[float, float, float, float]]:
    if rs_line_segments is not None:
        try:  # pragma: no cover - backend opcional
            return list(rs_line_segments(points))
        except Exception:
            pass

    return _line_segments_py(points)


def _nearest_point_py(
    points: List[Tuple[float, float]], x: float, y: float
) -> Optional[Tuple[int, float]]:
    if not points:
        return None

    dist, index = min(
        ((px - x) ** 2 + (py - y) ** 2, i) for i, (px, py) in enumerate(points)
    )
    return index, dist


class LineChart:
    """Gráfico de líneas interactivo basado en ``ft.Canvas``.

    Soporta zoom mediante scroll y muestra tooltips al pasar el ratón
    sobre el punto más cercano. Los ejes pueden personalizarse pasando
    rangos específicos.
    """

    def __init__(
        self,
        data: List[Tuple[float, float]],
        width: int = 400,
        height: int = 300,
        x_range: Optional[Tuple[float, float]] = None,
        y_range: Optional[Tuple[float, float]] = None,
        axis_color: str = ft.Colors.BLACK,
        style: Style | None = None,
    ) -> None:
        """Inicializa el gráfico de líneas.

        :param data: Lista de pares ``(x, y)``.
        :param width: Ancho del lienzo.
        :param height: Alto del lienzo.
        :param x_range: Rango manual para el eje X.
        :param y_range: Rango manual para el eje Y.
        :param axis_color: Color de los ejes.
        :param style: Estilo opcional aplicado al contenedor principal.
        """
        self.data = data
        self.width = width
        self.height = height
        self.axis_color = axis_color
        self.style = style

        self.x_min = x_range[0] if x_range else min(x for x, _ in data)
        self.x_max = x_range[1] if x_range else max(x for x, _ in data)
        self.y_min = y_range[0] if y_range else min(y for _, y in data)
        self.y_max = y_range[1] if y_range else max(y for _, y in data)

        self.scale: float = 1.0
        self.tooltip = ft.Text(visible=False, bgcolor=ft.Colors.WHITE)
        self.canvas = cv.Canvas(width=self.width, height=self.height)

        self._update_canvas()

    # ------------------------------------------------------------------
    def build(self) -> ft.Control:
        detector = ft.GestureDetector(
            content=self.canvas,
            on_scroll=self._on_wheel,
            on_hover=self._on_hover,
        )
        stack = ft.Stack([detector, ft.Container(self.tooltip, padding=5)])
        return self.style.apply(stack) if self.style else stack

    # ------------------------------------------------------------------
    def _on_wheel(self, e) -> None:
        """Zoom del gráfico según el scroll."""
        delta = getattr(e, "delta_y", 0)
        if delta < 0:
            self.scale *= 1.1
        elif delta > 0:
            self.scale /= 1.1
        self.scale = max(0.1, min(self.scale, 10))
        self._update_canvas()

    # ------------------------------------------------------------------
    def _on_hover(self, e) -> None:
        """Muestra un tooltip con el valor más cercano."""
        x = getattr(e, "local_x", 0)
        y = getattr(e, "local_y", 0)

        points = self._screen_points()
        if not points:
            return

        nearest = _nearest_point(points, x, y)
        if nearest is None:
            return

        index, _ = nearest
        data_pt = self.data[index]
        self.tooltip.value = f"{data_pt[0]}, {data_pt[1]}"
        self.tooltip.visible = True
        if self.tooltip.page:
            self.tooltip.update()

    # ------------------------------------------------------------------
    def _screen_points(self) -> List[Tuple[float, float]]:
        return _screen_points(
            self.data,
            self.x_min,
            self.x_max,
            self.y_min,
            self.y_max,
            self.width,
            self.height,
            self.scale,
        )

    # ------------------------------------------------------------------
    def _update_canvas(self) -> None:
        points = self._screen_points()
        shapes = []

        paint_axis = ft.Paint(stroke_width=1, color=self.axis_color)
        paint_line = ft.Paint(stroke_width=2, color=ft.Colors.BLUE)

        shapes.append(cv.Line(0, self.height, self.width, self.height, paint=paint_axis))
        shapes.append(cv.Line(0, 0, 0, self.height, paint=paint_axis))

        shapes.extend(
            cv.Line(x1, y1, x2, y2, paint=paint_line)
            for x1, y1, x2, y2 in _line_segments(points)
        )

        self.canvas.shapes = shapes
