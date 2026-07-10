# Guía de proyectos fullstack con FletPlus

La plantilla `fullstack` crea un proyecto FletPlus con separación explícita entre interfaz, lógica Python local, contratos compartidos, documentación y despliegue.

## Crear un proyecto fullstack

Puedes generar la misma plantilla con `--target fullstack` o con `--template fullstack`:

```bash
fletplus create MiProducto --target fullstack --preset saas --palette zenith --theme-mode light --font Inter
# equivalente si quieres fijar solo la plantilla:
fletplus create MiProducto --template fullstack
```

El target generado se declara como `all` en `pyproject.toml` para mantener el build multipropósito, mientras la plantilla conserva metadatos propios de FletPlus para localizar cada capa.

## Estructura base

```text
MiProducto/
├── assets/
├── deploy/
│   └── README.md
├── docs/
│   └── README.md
├── pyproject.toml
├── requirements.txt
└── src/
    ├── main.py
    ├── backend/
    │   ├── __init__.py
    │   └── services.py
    ├── frontend/
    │   ├── assets.py
    │   ├── config.py
    │   ├── layout.py
    │   ├── routes.py
    │   └── theme.py
    └── shared/
        ├── __init__.py
        ├── config.py
        └── models.py
```

Responsabilidades recomendadas:

- `src/frontend/`: pantallas, rutas, tema, layout responsivo y referencias de assets.
- `src/backend/`: servicios Python, API local, adaptadores de datos o lógica de dominio.
- `src/shared/`: modelos, configuración y utilidades comunes entre frontend y backend.
- `docs/`: documentación generada o mantenida junto al proyecto.
- `deploy/`: scripts por plataforma, manifiestos y automatizaciones de release.

## Configuración generada

La plantilla incluye una sección `[tool.fletplus]` con rutas declarativas para herramientas internas o scripts de CI/CD:

```toml
[tool.fletplus]
app = "src/main.py"
default_target = "all"
backend_dir = "src/backend"
frontend_dir = "src/frontend"
shared_dir = "src/shared"
docs_dir = "docs"
deploy_dir = "deploy"
```

La configuración visual sigue viviendo en `[tool.fletplus.frontend]` y se consume desde `src/frontend/theme.py`, igual que en las plantillas `app`, `web`, `desktop` y `mobile`.

## Primer flujo de trabajo

1. Añade modelos compartidos en `src/shared/models.py`.
2. Implementa casos de uso o servicios locales en `src/backend/services.py`.
3. Consume esos servicios desde `src/main.py` o desde vistas/rutas en `src/frontend/`.
4. Documenta decisiones y contratos en `docs/`.
5. Añade scripts reproducibles en `deploy/` cuando el proyecto tenga un destino de publicación.

El ejemplo inicial ya conecta `src/main.py` con `backend.services.get_project_status()` para demostrar la frontera entre interfaz y lógica de dominio sin introducir dependencias externas.
