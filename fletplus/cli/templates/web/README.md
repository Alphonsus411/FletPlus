# {{ project_name }}

Aplicación web generada con la CLI de FletPlus. La plantilla incluye configuración de página para navegador, registro PWA y generación inicial de `manifest.json` y `service_worker.js` en el directorio `web/`.

## Requisitos

- Python 3.10 o superior
- Flet `>=0.80,<0.86` (misma política de versión que `fletplus`)
- Dependencias listadas en `requirements.txt`

## Ejecución web en desarrollo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fletplus run --app src/main.py
```

También puedes ejecutar directamente el entrypoint para abrir el navegador y regenerar los recursos PWA iniciales:

```bash
python src/main.py
```

## Build para navegador/PWA

```bash
fletplus build --target web
```

La plantilla ya incluye `web/manifest.json` y `web/service_worker.js`; antes de publicar, añade iconos reales al manifest y sirve ambos archivos desde el mismo origen que la aplicación.

## Opciones generadas por la CLI

Este proyecto fue renderizado con estas opciones iniciales:

- Target: `{{ target_name }}` (`target = "{{ target_value }}"` en `pyproject.toml`).
- Preset visual: `{{ preset_name }}`.
- Paleta: `{{ palette_name }}`.
- Modo de tema: `{{ theme_mode }}` (`light`, `dark` o `system`).
- Fuente principal: `{{ font_family }}`.
- Densidad de layout: `{{ layout_density }}`.
- Espaciado base: `{{ spacing }}` px y padding de página: `{{ page_padding }}` px.

Puedes regenerar un proyecto equivalente con una variante de:

```bash
fletplus create {{ project_name }} --target {{ target_name }} --preset {{ preset_name }} --palette {{ palette_name }} --theme-mode {{ theme_mode }} --font {{ font_family }} --layout-density {{ layout_density }}
```

La configuración queda duplicada intencionalmente en `pyproject.toml` para el runtime y en `src/frontend/config.py` como fallback editable.

## Estructura inicial

La plantilla mantiene `src/main.py` como entrypoint específico de plataforma y delega la configuración visual en `src/frontend/`:

- `src/frontend/config.py`: punto principal de personalización. Cambia `PALETTE_NAME`, `PALETTE_MODE`, `FONT_FAMILY`, `FONT_ASSETS`, `CUSTOM_TOKENS`, `PAGE_PADDING`, `MAX_CONTENT_WIDTH`, `MIN_CONTENT_WIDTH`, `SPACING` y `LAYOUT_DENSITY` para ajustar colores, modo claro/oscuro, fuentes, tokens, densidad visual y anchuras.
- `src/frontend/theme.py`: construye `FrontEndConfig` a partir de `pyproject.toml` y de los fallbacks declarados en `config.py`. Normalmente solo necesitas tocarlo si quieres cambiar cómo se fusionan los tokens o las fuentes.
- `src/frontend/layout.py`: centraliza el shell responsivo, el ancho máximo, helpers de `spacing()` y detección de orientación. Ajusta aquí reglas de layout por dispositivo cuando no baste con modificar `config.py`.
- `src/frontend/assets.py` y `assets/README.md`: centralizan rutas de assets seguros. Declara aquí directorios, imágenes, iconos o fuentes reutilizables antes de referenciarlos desde las vistas.
- `src/frontend/routes.py`: contiene un ejemplo mínimo con `fletplus.router.Route` y `Router`; añade nuevas rutas, cambia textos o sustituye `render_initial_route()` por navegación persistente cuando la app crezca.
- `src/main.py`: conserva el arranque propio de la plataforma y compone tema, layout y rutas importando desde `frontend.*`.

### Personalización rápida

- **Colores y tokens:** edita `CUSTOM_TOKENS["colors"]` en `src/frontend/config.py`; puedes añadir claves como `success`, `warning` o `surface_muted` y consumirlas desde tus vistas.
- **Fuentes:** cambia `FONT_FAMILY` y registra archivos en `FONT_ASSETS`, por ejemplo `{"Inter": "assets/fonts/Inter-Regular.ttf"}`. Copia los binarios bajo `assets/fonts/`.
- **Densidad visual:** ajusta `LAYOUT_DENSITY`, `SPACING` y `PAGE_PADDING` para alternar entre interfaces compactas, cómodas o espaciosas.
- **Assets:** declara constantes en `src/frontend/assets.py` si una imagen, icono o fuente se reutiliza en varias pantallas; mantiene rutas relativas a `assets/`.
- **Rutas:** añade nuevas funciones de vista y entradas `Route(path="/...", view=...)` en `src/frontend/routes.py`.

Para cambiar layout y breakpoints, empieza por `PAGE_PADDING`, `MAX_CONTENT_WIDTH`, `MIN_CONTENT_WIDTH`, `SPACING` y `LAYOUT_DENSITY` en `src/frontend/config.py`; después adapta `responsive_shell()`, `max_width_container()` u `orientation()` en `src/frontend/layout.py` si tu producto requiere reglas específicas por dispositivo.

## Ejemplo: usar una fuente local

1. Copia tu archivo `.ttf` u `.otf` a `assets/fonts/`, por ejemplo `assets/fonts/Inter-Regular.ttf`.
2. Edita `src/frontend/config.py`:

```python
FONT_FAMILY = "Inter"
FONT_FALLBACK_FAMILIES = ("Roboto", "Arial", "sans-serif")
FONT_ASSETS = {"Inter": "assets/fonts/Inter-Regular.ttf"}
FONT_WEIGHTS = ("w400", "w600", "w700")
FONT_STYLES = ("normal",)
```

`create_frontend_config()` registra esos assets mediante `FrontEndConfig.apply_to_page(page)`, que los copia a `page.fonts` y establece la familia en `page.theme`.
