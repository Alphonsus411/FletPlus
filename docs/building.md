# Compilación de aplicaciones FletPlus

El comando `fletplus build` empaqueta una aplicación según distintos objetivos,
aprovechando el empaquetado nativo de Flet.

```bash
fletplus build --target <web|desktop|windows|macos|linux|desktop-all|mobile|android-apk|android-aab|ios|all>
```

## Flujo general

1. Se analizan los metadatos del proyecto desde `pyproject.toml` (nombre,
   versión, autores y descripción).
2. Se recopilan iconos y recursos estáticos ubicados en `assets/` o `static/`.
3. Se delega la compilación a `flet build` según el objetivo:
   - `flet build web` genera la versión web en `dist/web/`.
   - `flet build windows`, `flet build macos` o `flet build linux` construyen artefactos de escritorio en `dist/windows/`, `dist/macos/` o `dist/linux/`.
   - `flet build apk` produce APKs en `dist/android-apk/`.
   - `flet build aab` produce Android App Bundles en `dist/android-aab/`.
   - `flet build ipa` produce artefactos iOS en `dist/ios/`.
4. Cada target reporta su resultado individual.

Si alguno de los empaquetadores falla, el comando finaliza con un error
indicando qué objetivo no se pudo generar.

## Configuración de compilación (Cython)

La configuración del empaquetado vive en `pyproject.toml` y la selección de
módulos Cython en `build_config.yaml`.

- `pyproject.toml` define metadatos, backend de build y artefactos incluidos en
  distribución.
- `build_config.yaml` lista los módulos candidatos a compilar con Cython para
  los builds locales.

Para mantener compatibilidad al instalar desde fuente sin Cython, conserva los
artefactos `*.c` versionados junto a sus `.pyx`. Si cambias un módulo Cython,
regenera el listado con `tools/select_cython_modules.py` (o `make
update-build-config`) y ejecuta `make build` para encadenar `update-build-config`,
`build-rust` y `python -m build` en el flujo actual.

Antes de ejecutar ese flujo en local, instala el extra opcional de build con `pip install .[build]` (incluye `build` y `cython`).

## Ejemplos de uso

### Compilación completa

```bash
fletplus build
```

Genera artefactos para `web`, el alias `desktop` (la plataforma actual) y `android-apk`.

### Objetivo web

```bash
fletplus build --target web
```

Ejecuta internamente `python -m flet build web --output dist/web src/main.py` y
coloca los archivos listos para desplegar en un servidor estático.

### Objetivos de escritorio por plataforma

```bash
fletplus build --target windows
fletplus build --target macos
fletplus build --target linux
fletplus build --target desktop-all
```

`desktop` se mantiene como alias de la plataforma actual, mientras que `desktop-all` resuelve la matriz soportada (`windows`, `macos` y `linux`). Cada opción invoca internamente `python -m flet build <plataforma>` y escribe en `dist/<plataforma>/`.

### Seleccionar el punto de entrada

```bash
fletplus build --target desktop --app path/to/app.py
```

Permite especificar un archivo distinto al predeterminado `src/main.py`.

## Flujo full-stack opcional

`fletplus build` conserva el modo clásico basado en un único punto de entrada,
por ejemplo `fletplus build --app src/main.py`, pero también puede preparar una
carpeta de staging con componentes de una aplicación full-stack antes de invocar
`flet build`.

La configuración vive en `[tool.fletplus]`:

```toml
[tool.fletplus]
app = "src/main.py"
backend_app = "backend/api.py"
frontend_app = "frontend/app.py"
docs_dir = "docs"
config_dir = "config"
deployment_dir = "deploy"
include_python_packages = ["shared", "packages/domain"]
```

Claves soportadas:

- `backend_app`: archivo o carpeta con el punto de entrada del backend Python.
- `frontend_app`: archivo o carpeta con el componente frontend que debe viajar
  con el build.
- `docs_dir`: carpeta de documentación que se copia al staging.
- `config_dir`: carpeta de configuración o ejemplos de entorno, como
  `.env.example`.
- `deployment_dir`: carpeta con manifiestos de despliegue, Dockerfiles o
  recetas de infraestructura.
- `include_python_packages`: lista de paquetes Python compartidos que se copian
  sin ejecutar instalación ni compilación.

Antes de lanzar cada adaptador, FletPlus prepara `build/<target>/` con:

- `metadata.json`, iconos y assets como en el flujo existente.
- `backend/`, `frontend/`, `docs/`, `config/` y `deployment/` cuando sus rutas
  existen.
- `python-packages/` con los paquetes declarados en `include_python_packages`.
- `fullstack.json` como manifiesto mínimo de los paquetes Python copiados.

Esta fase es deliberadamente estática: copia archivos y carpetas para que hooks,
scripts externos o pipelines de CI puedan consumirlos, pero no sustituye el
empaquetador de Flet ni ejecuta builds reales de backend/documentación.

## Variables de entorno auxiliares

Durante la fase móvil se exponen dos variables de entorno útiles para recetas
personalizadas de Flet/build hooks:

- `FLETPLUS_METADATA`: ruta al archivo `metadata.json` generado en la carpeta de
  compilación temporal.
- `FLETPLUS_ICON`: ruta al icono preparado por el adaptador.

Estas variables pueden consumirse desde scripts o configuraciones externas para
ajustar el empaquetado sin modificar el código fuente.

### Objetivos móviles explícitos

```bash
fletplus build --target android-apk
fletplus build --target android-aab
fletplus build --target ios
```

`mobile` se conserva como alias retrocompatible de `android-apk`.

## Manifiesto de despliegue web

Cuando el objetivo es `web`, FletPlus ejecuta el build nativo de Flet y añade
artefactos propios en `dist/web/` para que el resultado pueda publicarse de
forma estática o combinarse con un backend Python:

- `fletplus-deploy.json`: manifiesto estable con metadatos del proyecto,
  configuración web, rutas resueltas, modo de despliegue y comandos sugeridos.
- `deploy-static.sh`: plantilla mínima para servir `dist/web/` con
  `python -m http.server` durante pruebas locales o smoke tests de CI.
- `deploy-backend-python.sh`: plantilla para arrancar un backend Python asociado
  al build, cargando `env_file` si se configuró.

La configuración vive en `[tool.fletplus.web]`:

```toml
[tool.fletplus.web]
base_url = "/app/"
backend_entrypoint = "server/main.py"
static_dir = "dist/web"
pwa = true
env_file = ".env.production"
deploy_provider = "external-proxy"
```

Claves soportadas:

- `base_url`: prefijo público donde se servirá la aplicación. También se pasa a
  `flet build web --base-url` cuando está definido.
- `backend_entrypoint`: archivo Python que arranca el backend asociado al build.
  Si se omite, el manifiesto queda en modo `static` salvo que el proyecto use
  otros hooks externos.
- `static_dir`: carpeta que debe publicar el proveedor estático; por defecto es
  `dist/web`.
- `pwa`: marca declarativa para pipelines que tratan el build como PWA. FletPlus
  no fuerza el registro del service worker desde el build, pero deja la decisión
  registrada en el manifiesto.
- `env_file`: archivo de variables de entorno para la plantilla de backend.
- `deploy_provider`: etiqueta libre para CI/CD (`static`, `nginx`, `vercel`,
  `external-proxy`, etc.).

### Ejemplo: web estática

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

El manifiesto resultante usa `deployment.mode = "static"` y apunta a `dist/web`
como directorio publicable.

### Ejemplo: web con backend Python local

```toml
[tool.fletplus]
backend_app = "backend/app.py"

[tool.fletplus.web]
base_url = "/"
backend_entrypoint = "backend/app.py"
env_file = ".env.local"
deploy_provider = "python-local"
```

```bash
fletplus build --target web
./dist/web/deploy-backend-python.sh
```

El manifiesto usa `deployment.mode = "backend-python"`, resuelve la ruta absoluta
del backend y deja un comando sugerido `python backend/app.py` para herramientas
externas.

### Ejemplo: web detrás de proxy o servidor externo

```toml
[tool.fletplus.web]
base_url = "/portal/"
static_dir = "dist/web"
backend_entrypoint = "server/asgi.py"
env_file = ".env.production"
deploy_provider = "external-proxy"
```

En este modo, publica `dist/web/` bajo el prefijo `/portal/` en Nginx, Apache,
Caddy o el servidor equivalente y proxyfica las rutas dinámicas hacia el backend
Python. El manifiesto conserva `base_url`, `static_dir`, `backend_entrypoint` y
`deploy_provider` para que el pipeline de infraestructura pueda validar que el
proxy coincide con el build generado.

## Build full-stack

Usa este flujo cuando el proyecto fue creado con `fletplus create --template fullstack` o cuando `[tool.fletplus]` declara backend, frontend y carpetas auxiliares. El build no inicia servicios: prepara una carpeta de staging por objetivo, copia los recursos declarados y después delega el empaquetado de UI a Flet.

```bash
fletplus create my-saas --template fullstack
cd my-saas
fletplus build --target web
```

Para construir la experiencia completa de distribución local puedes combinar el build web con el target de escritorio de la plataforma actual:

```bash
fletplus build --target web
fletplus build --target desktop
```

Recomendaciones:

- Declara `backend_app`, `frontend_app`, `deployment_dir`, `config_dir` e `include_python_packages` en `pyproject.toml` para que el staging sea reproducible.
- Versiona ejemplos de entorno, como `.env.example`, pero no secretos reales.
- Usa `deployment_dir` para Dockerfiles, manifiestos de orquestación, scripts de reverse proxy o recetas CI/CD.

## Build Windows

El target Windows genera artefactos de escritorio en `dist/windows/` y está pensado para ejecutarse desde Windows cuando se necesite un binario nativo revisable en esa plataforma.

```bash
fletplus build --target windows
```

Notas operativas:

- Ejecuta el comando en Windows para evitar depender de cross-compilation no soportada por el toolchain nativo.
- Si vas a distribuir a usuarios finales, genera después un instalador con `fletplus installer --target windows --include-bat`.
- Valida el resultado en una máquina limpia o en una VM con la versión mínima de Windows que soporte tu producto.

## Build macOS

El target macOS escribe el resultado en `dist/macos/` y debe ejecutarse en macOS para producir artefactos compatibles con el ecosistema de firma, notarización y empaquetado de Apple.

```bash
fletplus build --target macos
```

Notas operativas:

- Usa un runner macOS en CI si necesitas automatizar builds firmados.
- Mantén certificados, perfiles y credenciales de notarización fuera del repositorio.
- Genera el script de instalación con `fletplus installer --target macos` cuando necesites una receta automatizada para testers.

## Build Linux

El target Linux genera artefactos en `dist/linux/` desde un entorno Linux compatible con la distribución objetivo o con una imagen base equivalente.

```bash
fletplus build --target linux
```

Notas operativas:

- Compila en la misma familia de distribución que usarán tus usuarios cuando dependas de bibliotecas del sistema.
- Usa contenedores o runners dedicados para estabilizar versiones de Python, Flet y dependencias nativas.
- Genera instaladores con `fletplus installer --target linux` para automatizar virtualenv, dependencias y arranque.

## Build web

El target web genera una aplicación publicable en `dist/web/` y añade manifiestos de despliegue FletPlus cuando existe configuración `[tool.fletplus.web]`.

```bash
fletplus build --target web
```

Flujos habituales:

- Web estática: publica `dist/web/` en un hosting estático, CDN, bucket o servidor Nginx.
- Web con backend: publica `dist/web/` como frontend y arranca el backend declarado en `backend_entrypoint` detrás del mismo dominio o de un proxy externo.
- PWA: declara `pwa = true` para que tus pipelines traten el artefacto como aplicación web instalable cuando tu configuración de Flet lo permita.

Consulta también [Despliegue de aplicaciones FletPlus](deployment.md) para ejemplos separados con y sin backend.

## Limitaciones de cross-compilation

FletPlus expone aliases prácticos como `desktop`, `desktop-all` y `all`, pero no convierte automáticamente un sistema operativo en otro toolchain nativo. La compatibilidad real depende de Flet, Flutter, Python, dependencias nativas y requisitos de firma de cada plataforma.

Reglas recomendadas:

- Compila Windows en Windows, macOS en macOS y Linux en Linux cuando el artefacto vaya a producción.
- Usa `desktop-all` solo como matriz de objetivos cuando el entorno disponga de las herramientas necesarias para cada plataforma.
- No asumas que wheels con extensiones nativas, librerías del sistema o certificados de firma funcionarán fuera de su plataforma origen.
- Para CI, define jobs separados por sistema operativo y sube cada carpeta `dist/<target>/` como artefacto independiente.
