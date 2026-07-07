# {{ project_name }}

Aplicación desktop generada con la CLI de FletPlus. La plantilla incluye configuración de ventana mediante `fletplus.utils.flet_compat.safe_set_window_attr` y un layout amplio con barra lateral y área de trabajo.

## Requisitos

- Python 3.9 o superior
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
