# Despliegue de aplicaciones FletPlus

Esta guía complementa [`docs/building.md`](building.md) y describe cómo publicar artefactos generados con `fletplus build`, especialmente en proyectos web creados con `fletplus create --template fullstack`.

## Crear un proyecto full-stack de referencia

```bash
fletplus create my-product --template fullstack
cd my-product
```

El template full-stack separa la experiencia frontend, el backend Python y los recursos de despliegue para que el build pueda copiar cada bloque al staging antes de generar artefactos.

## Despliegue web sin backend

Usa este modo cuando la aplicación solo necesita archivos estáticos o consume APIs externas ya desplegadas.

```toml
[tool.fletplus.web]
base_url = "/"
static_dir = "dist/web"
deploy_provider = "static"
```

```bash
fletplus build --target web
cd dist/web
python -m http.server 8000
```

Después de validar localmente, publica el contenido de `dist/web/` en tu proveedor estático. Ejemplos típicos son un bucket con CDN, Nginx, Apache, GitHub Pages o cualquier plataforma que sirva HTML, JavaScript, CSS y assets.

## Despliegue web con backend Python

Usa este modo cuando la UI web debe desplegarse junto a una API, proceso ASGI/WSGI, worker o servidor Python propio.

```toml
[tool.fletplus]
backend_app = "backend/app.py"
deployment_dir = "deploy"
config_dir = "config"

[tool.fletplus.web]
base_url = "/"
static_dir = "dist/web"
backend_entrypoint = "backend/app.py"
env_file = ".env.production"
deploy_provider = "external-proxy"
```

```bash
fletplus build --target web
./dist/web/deploy-backend-python.sh
```

En producción, lo habitual es servir `dist/web/` desde un servidor estático o proxy inverso y ejecutar el backend como servicio separado. Mantén secretos en variables de entorno gestionadas por la plataforma, no en el repositorio.

## Instalador automatizado por entorno

Si además necesitas entregar scripts para preparar equipos o servidores, genera instaladores por sistema operativo:

```bash
fletplus installer --target linux
fletplus installer --target macos
fletplus installer --target windows --include-bat
fletplus installer --target web
```

Consulta [`docs/installer.md`](installer.md) para el detalle de cada script generado.

## Checklist previo a publicar

- Ejecuta `fletplus build --target web` desde un entorno reproducible.
- Revisa `dist/web/fletplus-deploy.json` para confirmar `base_url`, modo de despliegue y rutas resueltas.
- Verifica que los assets esperados estén en `dist/web/`.
- Comprueba que `.env.production` o su equivalente se gestione fuera del repositorio si contiene secretos.
- Prueba el backend y el frontend detrás del mismo proxy antes de promocionar a producción.
