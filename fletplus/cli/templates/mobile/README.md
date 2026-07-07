# {{ project_name }}

Aplicación mobile generada con la CLI de FletPlus. La plantilla prioriza pantallas pequeñas: navegación inferior compacta, safe-area cuando está disponible y `FrontEndConfig` con ancho y espaciado reducidos.

## Requisitos

- Python 3.9 o superior
- Flet `>=0.80,<0.86` (misma política de versión que `fletplus`)
- Dependencias listadas en `requirements.txt`

## Ejecución mobile en desarrollo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fletplus run
```

Para revisar el comportamiento responsive durante desarrollo, reduce el ancho de la ventana o usa las herramientas de dispositivo del navegador si ejecutas en modo web.

## Build mobile

```bash
fletplus build --target mobile
```

Completa los metadatos, iconos y permisos específicos de Android/iOS antes de publicar en tiendas.

## Estructura inicial

La plantilla separa responsabilidades para que puedas crecer sin reescribir el entrypoint:

- `src/theme.py`: cambia `PALETTE_NAME`, `PALETTE_MODE`, `FONT_FAMILY`, `FONT_ASSETS` y `CUSTOM_TOKENS` para ajustar paletas, modo claro/oscuro, fuentes y tokens propios.
- `src/layout.py`: centraliza el shell responsivo, el ancho máximo, helpers de `spacing()` y detección de orientación. Ajusta aquí los breakpoints indirectamente modificando la `FrontEndConfig` o sus perfiles responsivos.
- `src/routes.py`: contiene un ejemplo mínimo con `fletplus.router.Route` y `Router`; añade nuevas rutas o sustituye `render_initial_route()` por navegación persistente cuando la app crezca.
- `src/assets.py` y `assets/README.md`: documentan assets placeholder seguros. Añade binarios reales solo cuando los necesites.
- `src/main.py`: compone tema, layout y rutas para arrancar la aplicación.

Para cambiar layout y breakpoints, empieza por `page_padding`, `max_content_width`, `min_content_width`, `spacing` y `layout_density` en `src/theme.py`; después adapta `responsive_shell()`, `max_width_container()` u `orientation()` en `src/layout.py` si tu producto requiere reglas específicas por dispositivo.
