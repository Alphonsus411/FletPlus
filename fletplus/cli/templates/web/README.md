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
