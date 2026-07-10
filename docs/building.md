# Compilación de aplicaciones FletPlus

El comando `fletplus build` empaqueta una aplicación según distintos objetivos,
aprovechando el empaquetado nativo de Flet.

```bash
fletplus build --target <web|desktop|mobile|android-apk|android-aab|ios|all>
```

## Flujo general

1. Se analizan los metadatos del proyecto desde `pyproject.toml` (nombre,
   versión, autores y descripción).
2. Se recopilan iconos y recursos estáticos ubicados en `assets/` o `static/`.
3. Se delega la compilación a `flet build` según el objetivo:
   - `flet build web` genera la versión web en `dist/web/`.
   - `flet build windows/macos/linux` construye artefactos de escritorio en `dist/desktop/`.
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

Genera artefactos para `web`, `desktop` y `android-apk`.

### Objetivo web

```bash
fletplus build --target web
```

Ejecuta internamente `python -m flet build web --output dist/web src/main.py` y
coloca los archivos listos para desplegar en un servidor estático.

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
