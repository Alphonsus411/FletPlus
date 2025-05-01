# fletplus/themes/theme_manager.py

import flet as ft

class ThemeManager:
    def __init__(self, page: ft.Page, primary_color=ft.colors.BLUE):
        self.page = page
        self.primary_color = primary_color
        self.dark_mode = False

    def apply_theme(self):
        self.page.theme = ft.Theme(
            color_scheme_seed=self.primary_color
        )
        self.page.theme_mode = ft.ThemeMode.DARK if self.dark_mode else ft.ThemeMode.LIGHT
        self.page.update()

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def set_primary_color(self, color):
        self.primary_color = color
        self.apply_theme()

