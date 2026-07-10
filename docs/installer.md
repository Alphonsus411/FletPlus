# Guía de instaladores FletPlus

`fletplus installer` crea scripts de instalación por plataforma para distribuir o
preparar una aplicación FletPlus sin ejecutar acciones durante la generación. Los
archivos resultantes están pensados para revisarse, versionarse o adjuntarse a un
paquete de entrega.

## Generación rápida

```bash
fletplus installer --target all
```

El comando escribe los scripts en `installers/`:

```text
installers/
├── linux/install.sh
├── macos/install.command
├── web/deploy_static.sh
└── windows/install.ps1
```

Para añadir un wrapper clásico de Windows:

```bash
fletplus installer --target windows --include-bat
```

## Qué hacen los scripts

Los scripts generados siguen un flujo no destructivo:

1. Resuelven el directorio del proyecto validado durante la generación.
2. Crean `.venv` si no existe.
3. Actualizan `pip` dentro del virtualenv.
4. Instalan `requirements.txt` si está presente.
5. Instalan el wheel más reciente de `dist/*.whl` cuando existe; si no, instalan
   el paquete local indicado con `--package-spec`.
6. Copian los assets configurados a `build/runtime_assets/` cuando la carpeta de
   assets existe.
7. Ejecutan la app con `python -m flet run <app>` en escritorio o generan el
   build web con `python -m flet build web`.

## Destinos soportados

### Windows

Genera `install.ps1`. Con `--include-bat`, también genera `install.bat`, que solo
invoca el script PowerShell.

```bash
fletplus installer --target windows --include-bat
```

### macOS

Genera `install.command`, marcado como ejecutable en sistemas POSIX.

```bash
fletplus installer --target macos
```

### Linux

Genera `install.sh`, marcado como ejecutable en sistemas POSIX. Cuando existe
`/etc/os-release`, imprime la distribución detectada para facilitar soporte y
troubleshooting.

```bash
fletplus installer --target linux
```

### Web

Genera `deploy_static.sh`, que instala dependencias y ejecuta `flet build web`.
El script muestra una instrucción local para servir artefactos estáticos con
`python -m http.server`.

```bash
fletplus installer --target web
```

## Opciones de rutas

Todas las rutas de aplicación, assets y paquete alternativo deben ser relativas y
seguras. El generador rechaza rutas absolutas, segmentos `..` y caracteres fuera
del conjunto permitido (`letras`, `números`, `.`, `_`, `-` y separadores de
ruta).

```bash
fletplus installer \
  --target linux \
  --project-dir . \
  --output-dir installers \
  --app src/main.py \
  --assets-dir assets \
  --package-spec .
```

## Seguridad

El generador aplica varias protecciones:

- No ejecuta los scripts generados.
- Valida que `--project-dir` exista y sea un directorio.
- Valida rutas relativas usadas dentro de los scripts.
- No interpola nombres de proyecto en comandos ejecutables.
- No genera comandos destructivos como `rm -rf`, `Remove-Item` o borrado de
  carpetas del proyecto.
- Usa variables con comillas en los scripts POSIX y `Join-Path` en PowerShell.

Aun así, revisa siempre los scripts antes de ejecutarlos en equipos de usuarios o
infraestructura productiva.
