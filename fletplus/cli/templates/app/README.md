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

La plantilla separa responsabilidades para que puedas crecer sin reescribir el entrypoint:

- `src/theme.py`: cambia `PALETTE_NAME`, `PALETTE_MODE`, `FONT_FAMILY`, `FONT_ASSETS` y `CUSTOM_TOKENS` para ajustar paletas, modo claro/oscuro, fuentes y tokens propios.
- `src/layout.py`: centraliza el shell responsivo, el ancho máximo, helpers de `spacing()` y detección de orientación. Ajusta aquí los breakpoints indirectamente modificando la `FrontEndConfig` o sus perfiles responsivos.
- `src/routes.py`: contiene un ejemplo mínimo con `fletplus.router.Route` y `Router`; añade nuevas rutas o sustituye `render_initial_route()` por navegación persistente cuando la app crezca.
- `src/assets.py` y `assets/README.md`: documentan assets placeholder seguros. Añade binarios reales solo cuando los necesites.
- `src/main.py`: compone tema, layout y rutas para arrancar la aplicación.

Para cambiar layout y breakpoints, empieza por `page_padding`, `max_content_width`, `min_content_width`, `spacing` y `layout_density` en `src/theme.py`; después adapta `responsive_shell()`, `max_width_container()` u `orientation()` en `src/layout.py` si tu producto requiere reglas específicas por dispositivo.
