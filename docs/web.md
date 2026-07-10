# Despliegue web

FletPlus genera artefactos adicionales para despliegues web cada vez que se
ejecuta:

```bash
fletplus build --target web
```

Además del resultado de `flet build web`, la carpeta `dist/web/` contiene:

- `fletplus-deploy.json`, el manifiesto de despliegue.
- `deploy-static.sh`, una plantilla para servir archivos estáticos.
- `deploy-backend-python.sh`, una plantilla para proyectos con backend Python.

## Configuración `[tool.fletplus.web]`

```toml
[tool.fletplus.web]
base_url = "/"
backend_entrypoint = "backend/app.py"
static_dir = "dist/web"
pwa = false
env_file = ".env.local"
deploy_provider = "static"
```

| Clave | Uso |
| --- | --- |
| `base_url` | Prefijo público de la app; se pasa a Flet como `--base-url`. |
| `backend_entrypoint` | Punto de entrada Python para despliegues con backend. |
| `static_dir` | Directorio que debe publicar el servidor estático. |
| `pwa` | Marca declarativa para pipelines PWA. |
| `env_file` | Archivo que cargará la plantilla de backend antes de arrancar Python. |
| `deploy_provider` | Etiqueta del destino de despliegue (`static`, `nginx`, `external-proxy`, etc.). |

## Web estática

```toml
[tool.fletplus.web]
base_url = "/"
static_dir = "dist/web"
deploy_provider = "static"
```

```bash
fletplus build --target web
cd dist/web
./deploy-static.sh
```

Usa este perfil cuando todos los archivos pueden servirse desde un bucket,
CDN, GitHub Pages o un servidor HTTP sin procesos Python persistentes.

## Web con backend Python local

```toml
[tool.fletplus.web]
backend_entrypoint = "backend/app.py"
env_file = ".env.local"
deploy_provider = "python-local"
```

```bash
fletplus build --target web
./dist/web/deploy-backend-python.sh
```

La plantilla carga `env_file` con `source` y después ejecuta el entrypoint. Es un
punto de partida para desarrollo local, smoke tests o contenedores sencillos.

## Web detrás de proxy o servidor externo

```toml
[tool.fletplus.web]
base_url = "/portal/"
static_dir = "dist/web"
backend_entrypoint = "server/asgi.py"
env_file = ".env.production"
deploy_provider = "external-proxy"
```

Publica `static_dir` en el servidor externo y dirige las rutas dinámicas al
backend Python. El manifiesto sirve como contrato entre el build de FletPlus y la
configuración de infraestructura.

## Nota sobre PWA

`pwa = true` queda registrado en `fletplus-deploy.json` para que un pipeline o
hook externo pueda aplicar pasos PWA específicos. Si la guía PWA crece con
recetas de service worker, caché offline o instalación, conviene separarla en
`docs/pwa.md` y enlazarla desde esta página.
