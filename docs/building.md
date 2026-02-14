# Compilación de aplicaciones FletPlus

El comando `fletplus build` empaqueta una aplicación según distintos objetivos,
aprovechando herramientas conocidas del ecosistema Python.

```bash
fletplus build --target <web|desktop|mobile|all>
```

## Flujo general

1. Se analizan los metadatos del proyecto desde `pyproject.toml` (nombre,
   versión, autores y descripción).
2. Se recopilan iconos y recursos estáticos ubicados en `assets/` o `static/`.
3. Se delega la compilación a la herramienta adecuada:
   - `flet build web` genera la versión web en `dist/web/`.
   - `PyInstaller` construye binarios de escritorio en `dist/desktop/`.
   - `briefcase package android` produce artefactos móviles en `dist/mobile/`.
4. Cada backend reporta su resultado individual.

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

Genera artefactos para los tres destinos (`web`, `desktop`, `mobile`).

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

## Variables de entorno auxiliares

Durante la fase móvil se exponen dos variables de entorno útiles para recetas
personalizadas de Briefcase:

- `FLETPLUS_METADATA`: ruta al archivo `metadata.json` generado en la carpeta de
  compilación temporal.
- `FLETPLUS_ICON`: ruta al icono preparado por el adaptador.

Estas variables pueden consumirse desde scripts o configuraciones externas para
ajustar el empaquetado sin modificar el código fuente.
