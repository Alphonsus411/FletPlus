import flet as ft
from fletplus.components.responsive_grid import ResponsiveGrid

def test_responsive_grid_builds_correctly():
    # Crear una lista de widgets dummy
    items = [
        ft.Text(f"Elemento {i}") for i in range(4)
    ]

    # Breakpoints definidos manualmente
    breakpoints = {
        0: 1,
        600: 2,
        900: 4
    }

    grid = ResponsiveGrid(children=items, breakpoints=breakpoints, spacing=5)

    # Simular un ancho de 900px (esperamos 4 columnas)
    layout = grid.build(page_width=900)

    # Validaciones
    assert isinstance(layout, ft.ResponsiveRow)
    assert len(layout.controls) == len(items)

    # Cada contenedor debe tener col=3 (12/4 columnas)
    for container in layout.controls:
        assert isinstance(container, ft.Container)
        assert container.col == 3


def test_responsive_grid_handles_none_width():
    grid = ResponsiveGrid(children=[ft.Text("Elemento")])

    layout = grid.build(page_width=None)

    assert isinstance(layout, ft.ResponsiveRow)
    assert all(isinstance(control, ft.Container) for control in layout.controls)
