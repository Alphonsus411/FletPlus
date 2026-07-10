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
distinta con `--directorio`, un destino con `--target`, una plantilla explícita con `--template` (compatibilidad) y opciones visuales como `--preset`, `--palette`, `--theme-mode`, `--font` y `--layout-density`.

Archivos generados:

- `README.md` con instrucciones básicas.
- `requirements.txt` con dependencias mínimas.
- `.gitignore` preconfigurado.
- Paquete `src/` con un `main.py` listo para ejecutar.
- Configuración FrontEnd inicial basada en `FrontEndConfig` para paletas, fuentes, pantalla y layout responsive.


Opciones de generación más relevantes:

- `--target {web|desktop|mobile|app}`: selecciona el destino inicial y, si no se indica `--template`, también la plantilla base. `app` genera la plantilla multipropósito y escribe `default_target = "all"`.
- `--template {app|web|desktop|mobile}`: fuerza una plantilla concreta; se mantiene por compatibilidad con versiones anteriores.
- `--preset {dashboard|landing|admin|mobile_app|saas|...}`: selecciona un preset de tokens para spacing, radios, sombras y tipografía.
- `--palette {aurora|sunset|lagoon|...}`: sobreescribe la paleta recomendada por el preset. La lista procede del registro interno de paletas de FletPlus.
- `--theme-mode {light|dark|system}`: escribe el modo en `pyproject.toml` y en `src/frontend/config.py`; `system` activa seguimiento del tema de plataforma en runtime.
- `--font {Inter|Roboto|System}`: define la familia principal y fallbacks seguros en `src/frontend/config.py`.
- `--layout-density {compact|comfortable|spacious}`: ajusta densidad, `spacing` y `page_padding` generados.

Flujo de renderizado:

1. La CLI valida nombre de proyecto, paquete, target, preset, paleta, modo, fuente y densidad.
2. Construye un contexto de plantilla con `project_name`, `package_name`, `target_name`, `target_value`, `preset_name`, `palette_name`, `theme_mode`, `font_family`, `layout_density`, `spacing`, `page_padding`, `max_content_width` y tokens custom serializados.
3. `_copy_template_tree()` recorre `fletplus/cli/templates/<plantilla>` y reemplaza placeholders `{{ ... }}` en archivos de texto.
4. `pyproject.toml` recibe `[tool.fletplus.frontend]` como fuente oficial para `FrontEndConfig.from_pyproject()`.
5. `src/frontend/config.py` recibe los mismos valores como fallback editable para escenarios sin `pyproject.toml`.

Presets visuales disponibles para `--preset`:

- `dashboard`: usa la paleta `fjord`, densidad `compact`, spacing contenido, radios medios y sombras discretas para KPIs/tablas.
- `landing`: usa `solstice`, densidad `spacious`, spacing amplio, radios grandes y sombras expresivas para páginas de marketing.
- `admin`: usa `metropolis`, densidad `compact`, radios sobrios y sombras ligeras para backoffices y CRUDs.
- `mobile_app`: usa `aurora`, densidad `comfortable`, radios táctiles y sombras suaves para interfaces móviles.
- `saas`: usa `zenith`, densidad `comfortable`, spacing equilibrado y tipografía Inter para productos SaaS.
- `ecommerce`: usa `citrus`, densidad `comfortable`, radios de tarjeta y sombras de producto para catálogos y checkout.

Ejemplos de creación con preset:

```bash
fletplus create Analitica --preset dashboard
fletplus create Marketing --template web --preset landing
fletplus create Backoffice --template desktop --preset admin
fletplus create MiApp --template mobile --preset mobile_app
fletplus create ProductoSaas --preset saas
fletplus create Tienda --template web --preset ecommerce
```

El preset elegido se refleja en `pyproject.toml` y en `src/frontend/config.py`: la
paleta base alimenta `FrontEndConfig.palette`, la densidad alimenta
`layout_density`, y los tokens de spacing, radios, sombras y tipografía quedan
disponibles en `CUSTOM_TOKENS`.

Plantillas disponibles:

- `app`: punto de partida general.
- `web`: estructura inicial orientada a despliegue web.
- `desktop`: estructura inicial orientada a escritorio.
- `mobile`: estructura inicial orientada a móvil.

### `fletplus frontend-tasks`

Lista, sin crear ni modificar archivos, las tareas declarativas que devuelve
`FrontEndConfig.implementation_tasks()`. El comando construye una configuración
frontend con las mismas opciones visuales principales de `create` y renderiza
cada `FrontEndTask` con su nombre, destino, descripción, funciones relacionadas
y tokens principales.

Opciones principales:

- `--target {web|desktop|mobile|app|all}`: destino usado para resolver presets
  de pantalla y densidad.
- `--palette {aurora|sunset|lagoon|...}`: paleta registrada que alimenta la
  tarea `paleta`.
- `--font {Inter|Roboto|System}`: familia principal mostrada en la tarea
  `fuentes`.
- `--layout-density {compact|comfortable|spacious}`: densidad usada para
  construir la configuración antes de listar las tareas.

Ejemplo:

```bash
fletplus frontend-tasks --target web --palette zenith --font Inter --layout-density comfortable
```

Salida abreviada:

```text
Tareas FrontEndConfig
Target: web
- paleta [web]
  Descripción: Resolver paletas base y overrides por plataforma.
  Funciones: palette_for_target, palette_tokens
  Tokens principales: palette=zenith
```

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
`desktop`, `windows`, `macos`, `linux`, `desktop-all`, `android-apk`, `android-aab`, `ios` y el alias `mobile`) reutilizando
el flujo descrito en `docs/building.md`. El comando delega en `flet build` y
muestra un reporte individual por destino.

Opciones principales:

- `--target {web|desktop|windows|macos|linux|desktop-all|mobile|android-apk|android-aab|ios|all}`: define qué
  objetivo(s) compilar. La opción `mobile` es alias de `android-apk`; `desktop` resuelve la plataforma actual; `desktop-all` ejecuta `windows`, `macos` y `linux`; `all`
  ejecuta `web`, `desktop` y `android-apk`.
- `--app PATH`: permite indicar un punto de entrada diferente al valor
  predeterminado `src/main.py`, útil si tu proyecto organiza la aplicación en
  otro módulo.

Durante la ejecución se imprime un estado por objetivo en el formato `✅ web:
artefactos generados en dist/web/` o `❌ android-aab: ...`, lo que facilita
identificar rápidamente el resultado de cada empaquetador.

Además del modo tradicional, el comando entiende una configuración full-stack en
`[tool.fletplus]` con `backend_app`, `frontend_app`, `docs_dir`, `config_dir`,
`deployment_dir` e `include_python_packages`. Antes de cada target, esas rutas se
preparan en `build/<target>/` para que hooks o pipelines puedan consumir backend,
frontend, documentación, configuración y paquetes Python compartidos. Consulta el
[flujo full-stack opcional](./building.md#flujo-full-stack-opcional) para ver un
ejemplo completo.

Ejemplos prácticos:

```bash
fletplus build --target web
```

Genera la versión lista para despliegue estático en `dist/web/`, equivalente al
paso "Objetivo web" descrito en la guía de compilación.

```bash
fletplus build --target desktop --app src/app.py
```

Empaqueta la aplicación de escritorio para la plataforma actual con `flet build` tomando `src/app.py` como entrada.

```bash
fletplus build --target windows
fletplus build --target macos
fletplus build --target linux
fletplus build --target desktop-all
```

Genera builds de escritorio explícitos con `python -m flet build windows`, `python -m flet build macos` o `python -m flet build linux`; `desktop-all` ejecuta los tres y deja los artefactos en `dist/windows/`, `dist/macos/` y `dist/linux/`.

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
palette = "zenith"
mode = "light"
font_family = "Inter"
page_padding = 24
max_content_width = 1100
min_content_width = 320
spacing = 16
layout_density = "comfortable"
preset = "saas"
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
- `mode`: variante visual, `"light"`, `"dark"` o `"system"`.
- `font_family`: familia principal asignada al tema de Flet.
- `page_padding`: padding global aplicado a la página y al shell de contenido.
- `max_content_width` / `min_content_width`: límites para layouts centrados.
- `spacing`: separación base para componentes y helpers de layout.
- `layout_density`: `"compact"`, `"normal"`, `"comfortable"` o `"spacious"`.
- `preset`: nombre del preset visual usado para inicializar la plantilla.
- `target`: destino esperado de la plantilla o build (`web`, `desktop`,
  `mobile`, `app`, `all`, `android-apk`, `android-aab` o `ios`).

Las subsecciones son opcionales. `[tool.fletplus.frontend.fonts]` se traduce a
`font_assets`, y cualquier grupo bajo `[tool.fletplus.frontend.tokens.*]` se
fusiona en `theme_tokens` para que `FrontEndConfig.apply_to_page()` lo publique
en el `ThemeManager` activo.

### `fletplus installer`

Genera scripts de instalación por plataforma sin ejecutarlos. El objetivo es
entregar archivos auditables que creen un entorno virtual, instalen dependencias,
instalen el paquete local o el wheel más reciente de `dist/`, copien assets y
arranquen la aplicación. Para web, genera un script de build estático con
instrucciones para servir los artefactos.

Opciones principales:

- `--target {windows|macos|linux|web|all}`: plataforma para la que se generarán
  scripts. `all` crea scripts para todos los destinos soportados.
- `--project-dir PATH`: raíz del proyecto FletPlus. Por defecto es el directorio
  actual.
- `--output-dir PATH`: carpeta donde se escribirán los instaladores. Por defecto
  es `installers/`.
- `--app PATH`: ruta relativa al punto de entrada de la aplicación. Por defecto
  es `src/main.py`.
- `--assets-dir PATH`: ruta relativa de assets que el script copiará a
  `build/runtime_assets/` cuando exista. Por defecto es `assets`.
- `--package-spec PATH`: paquete local o ruta relativa a instalar si no se
  encuentra un wheel en `dist/`. Por defecto es `.`.
- `--include-bat`: genera un wrapper `install.bat` además de `install.ps1` para
  Windows.

Ejemplos:

```bash
fletplus installer --target all
fletplus installer --target windows --include-bat
fletplus installer --target web --output-dir deploy/installers
```

Archivos generados por plataforma:

- Windows: `installers/windows/install.ps1` y opcionalmente
  `installers/windows/install.bat`.
- macOS: `installers/macos/install.command`.
- Linux: `installers/linux/install.sh`, con lectura de `/etc/os-release` cuando
  esté disponible.
- Web: `installers/web/deploy_static.sh`.

El generador valida rutas relativas para evitar interpolación insegura, rechaza
segmentos `..` y no incluye operaciones destructivas como borrado de directorios
del proyecto. Consulta la guía completa en [`docs/installer.md`](./installer.md).
