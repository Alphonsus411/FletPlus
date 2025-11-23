# CLI de FletPlus

La línea de comandos `fletplus` facilita el ciclo de vida de una aplicación construida
con FletPlus. Tras instalar el paquete podrás ejecutar el comando `fletplus`
desde cualquier terminal.

## Instalación

```bash
pip install fletplus
```

## Comandos disponibles

### `fletplus create <nombre>`

Genera una estructura base para comenzar un nuevo proyecto. Por defecto el
directorio se crea dentro de la carpeta actual, aunque puedes indicar una ruta
distinta con `--directorio`.

Archivos generados:

- `README.md` con instrucciones básicas.
- `requirements.txt` con dependencias mínimas.
- `.gitignore` preconfigurado.
- Paquete `src/` con un `main.py` listo para ejecutar.

### `fletplus run`

Inicia el servidor de desarrollo con recarga automática y DevTools activado.
Opciones relevantes:

- `--app PATH`: Archivo principal de la aplicación (por defecto `src/main.py`).
- `--port PORT`: Puerto HTTP para abrir la vista web (por defecto `8550`).
- `--no-devtools`: Desactiva DevTools.
- `--watch PATH`: Carpeta a monitorear para la recarga (por defecto el directorio actual).

El comando mantiene un observador de archivos usando `watchdog`; cada vez que se
detecta un cambio se reinicia el proceso `flet run` con la opción `--devtools`.

### `fletplus profile`

Ejecuta flujos internos con `cProfile` para detectar cuellos de botella dentro
del propio paquete y genera un reporte en texto plano.

Opciones principales:

- `--flow`: permite seleccionar uno o varios flujos (`router`, `scaffold`,
  `responsive`). Si no se especifica, se ejecutan todos.
- `--output`: ruta del archivo donde se guardará el reporte (por defecto
  `profile-report.txt`).
- `--sort`: columna por la que ordenar el reporte de `pstats` (`tottime`,
  `cumtime`, `ncalls` o `calls`).
- `--limit`: número de filas a mostrar al imprimir el reporte.

Ejemplos prácticos:

```bash
fletplus profile --output build/profile.txt --sort cumtime --limit 30
```

Genera un perfil ordenado por tiempo acumulado y lo guarda en `build/profile.txt`.

```bash
fletplus profile --flow router --flow responsive --limit 10
```

Perfilado parcial ejecutando únicamente los flujos de navegación y utilidades
responsivas, mostrando las 10 filas más relevantes.

### `fletplus build`

Compila la aplicación para los distintos objetivos soportados (`web`,
`desktop`, `mobile`) reutilizando el flujo descrito en `docs/building.md`. El
comando coordina los empaquetadores oficiales y muestra un reporte individual
por destino.

Opciones principales:

- `--target {web|desktop|mobile|all}`: define qué objetivo(s) compilar. La
  opción `all` ejecuta la cadena completa y deja los artefactos en `dist/web/`,
  `dist/desktop/` y `dist/mobile/` respectivamente.
- `--app PATH`: permite indicar un punto de entrada diferente al valor
  predeterminado `src/main.py`, útil si tu proyecto organiza la aplicación en
  otro módulo.

Durante la ejecución se imprime un estado por objetivo en el formato `✅ web:
artefactos generados en dist/web/` o `❌ desktop: falta PyInstaller`, lo que
facilita identificar rápidamente el resultado de cada empaquetador.

Ejemplos prácticos:

```bash
fletplus build --target web
```

Genera la versión lista para despliegue estático en `dist/web/`, equivalente al
paso "Objetivo web" descrito en la guía de compilación.

```bash
fletplus build --target desktop --app src/app.py
```

Empaqueta la aplicación de escritorio con PyInstaller tomando `src/app.py` como
entrada y dejando los binarios en `dist/desktop/`.

```bash
fletplus build --target mobile
```

Produce el paquete móvil mediante Briefcase y coloca los artefactos generados
en `dist/mobile/`.

> **Nota de compatibilidad:** asegúrate de tener instaladas las herramientas
> externas necesarias (`PyInstaller` para `desktop` y `Briefcase` para
> `mobile`). Para más detalles y requisitos adicionales, consulta la [guía de
> compilación](./building.md).
