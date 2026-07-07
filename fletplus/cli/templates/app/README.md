# {{ project_name }}

Aplicación multipropósito generada con la CLI de FletPlus. Esta plantilla es el punto de partida general para proyectos que todavía no están orientados a un target concreto.

El punto de entrada está en `src/main.py`, donde se define `main`, se aplica `FrontEndConfig` y se invoca `ft.app` para iniciar la interfaz.

## Requisitos

- Python 3.9 o superior
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
