# Assets de {{ project_name }}

Este directorio se entrega solo con placeholders de texto seguros. Añade aquí iconos, fuentes o imágenes reales cuando los necesites y referencia sus rutas desde `src/frontend/assets.py` o `src/frontend/config.py`.

## Estructura

```text
assets/
├── fonts/     # fuentes locales (.ttf/.otf) -> FONTS_DIR
├── icons/     # iconos de app, escritorio, móvil y PWA -> ICONS_DIR
├── images/    # logos, ilustraciones y fotografías -> IMAGES_DIR
└── README.md
```

Las rutas base están centralizadas en `src/frontend/assets.py` (`ASSETS_DIR`, `FONTS_DIR`, `ICONS_DIR`, `IMAGES_DIR`).

## Fuentes locales

Coloca archivos `.ttf` u `.otf` dentro de `assets/fonts/` para que Flet pueda servirlos junto con la app. Después declara la familia en `src/frontend/config.py`:

```python
FONT_FAMILY = "Inter"
FONT_FALLBACK_FAMILIES = ("Roboto", "Arial", "sans-serif")
FONT_ASSETS = {
    "Inter": "assets/fonts/Inter-Regular.ttf",
}
FONT_WEIGHTS = ("w400", "w600", "w700")
FONT_STYLES = ("normal",)
```

Si declaras una ruta local que no existe, `FrontEndConfig.apply_to_page(page)` mostrará un aviso claro para ayudarte a corregirla.
