# {{ project_name }}

Aplicación web generada con la CLI de FletPlus. La plantilla incluye configuración de página para navegador, registro PWA y generación inicial de `manifest.json` y `service_worker.js` en el directorio `web/`.

## Requisitos

- Python 3.9 o superior
- Flet `>=0.80,<0.86` (misma política de versión que `fletplus`)
- Dependencias listadas en `requirements.txt`

## Ejecución web en desarrollo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fletplus run --web
```

También puedes ejecutar directamente el entrypoint para abrir el navegador y regenerar los recursos PWA iniciales:

```bash
python src/main.py
```

## Build para navegador/PWA

```bash
fletplus build --target web
```

Antes de publicar, reemplaza los iconos vacíos del manifest por tus assets reales y sirve `manifest.json` y `service_worker.js` desde el mismo origen que la aplicación.

## Estructura inicial

La plantilla separa responsabilidades para que puedas crecer sin reescribir el entrypoint:

- `src/theme.py`: cambia `PALETTE_NAME`, `PALETTE_MODE`, `FONT_FAMILY`, `FONT_ASSETS` y `CUSTOM_TOKENS` para ajustar paletas, modo claro/oscuro, fuentes y tokens propios.
- `src/layout.py`: centraliza el shell responsivo, el ancho máximo, helpers de `spacing()` y detección de orientación. Ajusta aquí los breakpoints indirectamente modificando la `FrontEndConfig` o sus perfiles responsivos.
- `src/routes.py`: contiene un ejemplo mínimo con `fletplus.router.Route` y `Router`; añade nuevas rutas o sustituye `render_initial_route()` por navegación persistente cuando la app crezca.
- `src/assets.py` y `assets/README.md`: documentan assets placeholder seguros. Añade binarios reales solo cuando los necesites.
- `src/main.py`: compone tema, layout y rutas para arrancar la aplicación.

Para cambiar layout y breakpoints, empieza por `page_padding`, `max_content_width`, `min_content_width`, `spacing` y `layout_density` en `src/theme.py`; después adapta `responsive_shell()`, `max_width_container()` u `orientation()` en `src/layout.py` si tu producto requiere reglas específicas por dispositivo.
