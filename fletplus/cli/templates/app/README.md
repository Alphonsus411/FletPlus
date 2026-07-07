# {{ project_name }}

Aplicación multipropósito generada con la CLI de FletPlus. Esta plantilla es el punto de partida general para proyectos que todavía no están orientados a un target concreto.

El punto de entrada está en `src/main.py`, donde se define `main`, se aplica `FrontEndConfig` y se invoca `ft.app` para iniciar la interfaz.

## Requisitos

- Python 3.10 o superior
- Flet `>=0.80,<0.86` (misma política de versión que `fletplus`)
- Dependencias listadas en `requirements.txt`

## Ejecución en desarrollo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fletplus run
```

## Build multipropósito

Usa el build por defecto cuando quieras empaquetar sin fijar un target específico:

```bash
fletplus build
```

Si más adelante eliges un target, puedes migrar el layout tomando como referencia las plantillas `web`, `desktop` o `mobile`.

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
