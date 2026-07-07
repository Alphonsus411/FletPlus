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
