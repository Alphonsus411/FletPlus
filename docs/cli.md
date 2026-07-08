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
distinta con `--directorio` y una plantilla con `--template`.

Archivos generados:

- `README.md` con instrucciones básicas.
- `requirements.txt` con dependencias mínimas.
- `.gitignore` preconfigurado.
- Paquete `src/` con un `main.py` listo para ejecutar.
- Configuración FrontEnd inicial basada en `FrontEndConfig` para paletas, fuentes, pantalla y layout responsive.

Plantillas disponibles:

- `app`: punto de partida general.
- `web`: estructura inicial orientada a despliegue web.
- `desktop`: estructura inicial orientada a escritorio.
- `mobile`: estructura inicial orientada a móvil.

### `fletplus run`

Inicia el servidor de desarrollo con recarga automática y DevTools activado.
Opciones relevantes:

- `--app PATH`: Archivo principal de la aplicación (por defecto `src/main.py`).
- `--port PORT`: Puerto HTTP para abrir la vista web (por defecto `8550`).
- `--no-devtools`: Desactiva DevTools.
- `--watch PATH`: Carpeta a monitorear para la recarga (por defecto el directorio actual).

El comando mantiene un observador de archivos usando `watchdog`; cada vez que se
detecta un cambio se reinicia el proceso `flet run` con la opción `--devtools`.
> **Nota:** `watchdog` es una dependencia opcional usada para la recarga
> automática de `fletplus run`. Puedes instalarla con el extra `cli`
> (`pip install -e .[cli]`) o combinarlo con desarrollo (`pip install -e .[dev,cli]`).

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
`desktop`, `android-apk`, `android-aab`, `ios` y el alias `mobile`) reutilizando
el flujo descrito en `docs/building.md`. El comando delega en `flet build` y
muestra un reporte individual por destino.

Opciones principales:

- `--target {web|desktop|mobile|android-apk|android-aab|ios|all}`: define qué
  objetivo(s) compilar. La opción `mobile` es alias de `android-apk`; `all`
  ejecuta `web`, `desktop` y `android-apk`.
- `--app PATH`: permite indicar un punto de entrada diferente al valor
  predeterminado `src/main.py`, útil si tu proyecto organiza la aplicación en
  otro módulo.

Durante la ejecución se imprime un estado por objetivo en el formato `✅ web:
artefactos generados en dist/web/` o `❌ android-aab: ...`, lo que facilita
identificar rápidamente el resultado de cada empaquetador.

Ejemplos prácticos:

```bash
fletplus build --target web
```

Genera la versión lista para despliegue estático en `dist/web/`, equivalente al
paso "Objetivo web" descrito en la guía de compilación.

```bash
fletplus build --target desktop --app src/app.py
```

Empaqueta la aplicación de escritorio con `flet build` tomando `src/app.py` como
entrada y dejando los artefactos en `dist/desktop/`.

```bash
fletplus build --target mobile
```

Produce un APK mediante `flet build apk` y coloca los artefactos generados en
`dist/android-apk/`. Usa `--target android-aab` o `--target ios` para generar
artefactos AAB o IPA.

> **Nota de compatibilidad:** asegúrate de tener instaladas las herramientas
> requeridas por Flet para cada plataforma objetivo. Para más detalles y
> requisitos adicionales, consulta la [guía de compilación](./building.md).

## Configuración oficial `[tool.fletplus.frontend]`

Las plantillas generadas por `fletplus create` incluyen una sección oficial de
frontend en `pyproject.toml`. `FrontEndConfig.from_pyproject()` lee esa tabla y
valida tipos, modo visual, densidad y destino antes de crear la configuración:

```toml
[tool.fletplus.frontend]
palette = "material"
mode = "light"
font_family = "Roboto"
page_padding = 24
max_content_width = 1100
min_content_width = 320
spacing = 16
layout_density = "comfortable"
target = "web"

[tool.fletplus.frontend.fonts]
Inter = "assets/fonts/Inter.ttf"

[tool.fletplus.frontend.tokens.colors]
primary = "#2563EB"
surface = "#FFFFFF"

[tool.fletplus.frontend.tokens.spacing]
page = 24
section = 32
```

Campos principales:

- `palette`: paleta registrada que se aplicará mediante `ThemeManager`.
- `mode`: variante visual, `"light"` o `"dark"`.
- `font_family`: familia principal asignada al tema de Flet.
- `page_padding`: padding global aplicado a la página y al shell de contenido.
- `max_content_width` / `min_content_width`: límites para layouts centrados.
- `spacing`: separación base para componentes y helpers de layout.
- `layout_density`: `"compact"`, `"normal"`, `"comfortable"` o `"spacious"`.
- `target`: destino esperado de la plantilla o build (`web`, `desktop`,
  `mobile`, `app`, `all`, `android-apk`, `android-aab` o `ios`).

Las subsecciones son opcionales. `[tool.fletplus.frontend.fonts]` se traduce a
`font_assets`, y cualquier grupo bajo `[tool.fletplus.frontend.tokens.*]` se
fusiona en `theme_tokens` para que `FrontEndConfig.apply_to_page()` lo publique
en el `ThemeManager` activo.
