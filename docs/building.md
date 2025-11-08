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

