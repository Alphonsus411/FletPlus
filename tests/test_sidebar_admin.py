import flet as ft
from fletplus.components.sidebar_admin import SidebarAdmin

def test_sidebar_admin_build_and_selection():
    selected = []

    def on_select(index):
        selected.append(index)

    menu_items = [
        {"title": "Inicio", "icon": ft.icons.HOME},
        {"title": "Usuarios", "icon": ft.icons.PEOPLE},
    ]

    sidebar = SidebarAdmin(menu_items=menu_items, on_select=on_select)
    control = sidebar.build()

    # Comprobar que se construye un Container con Column interna
    assert isinstance(control, ft.Container)
    assert isinstance(control.content, ft.Column)
    assert len(sidebar.tiles) == 2  # Se crearon dos ListTile

    # Simular evento con un objeto dummy que tiene e.control.page.update()
    class DummyPage:
        def update(self): pass

    class DummyControl:
        page = DummyPage()

    class DummyEvent:
        control = DummyControl()

    # Ejecutar selección
    sidebar._select_item(1, DummyEvent())

    assert sidebar.selected_index == 1
    assert selected == [1]
    assert sidebar.tiles[1].selected is True
