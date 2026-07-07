# {{ project_name }}

Aplicación desktop generada con la CLI de FletPlus. La plantilla incluye configuración de ventana mediante `fletplus.utils.flet_compat.safe_set_window_attr` y un layout amplio con barra lateral y área de trabajo.

## Requisitos

- Python 3.10 o superior
- Flet `>=0.80,<0.86` (misma política de versión que `fletplus`)
- Dependencias listadas en `requirements.txt`

## Ejecución desktop en desarrollo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fletplus run
```

## Build de escritorio

```bash
fletplus build --target desktop
```

Ajusta `configure_window()` en `src/main.py` para cambiar tamaño inicial, mínimos, centrado o comportamiento de redimensionado según el sistema operativo de destino.

## Estructura inicial

La plantilla separa responsabilidades para que puedas crecer sin reescribir el entrypoint:

- `src/theme.py`: cambia `PALETTE_NAME`, `PALETTE_MODE`, `FONT_FAMILY`, `FONT_ASSETS` y `CUSTOM_TOKENS` para ajustar paletas, modo claro/oscuro, fuentes y tokens propios.
- `src/layout.py`: centraliza el shell responsivo, el ancho máximo, helpers de `spacing()` y detección de orientación. Ajusta aquí los breakpoints indirectamente modificando la `FrontEndConfig` o sus perfiles responsivos.
- `src/routes.py`: contiene un ejemplo mínimo con `fletplus.router.Route` y `Router`; añade nuevas rutas o sustituye `render_initial_route()` por navegación persistente cuando la app crezca.
- `src/assets.py` y `assets/README.md`: documentan assets placeholder seguros. Añade binarios reales solo cuando los necesites.
- `src/main.py`: compone tema, layout y rutas para arrancar la aplicación.

Para cambiar layout y breakpoints, empieza por `page_padding`, `max_content_width`, `min_content_width`, `spacing` y `layout_density` en `src/theme.py`; después adapta `responsive_shell()`, `max_width_container()` u `orientation()` en `src/layout.py` si tu producto requiere reglas específicas por dispositivo.
