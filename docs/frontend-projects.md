# Guía de proyectos frontend con FletPlus

Esta guía resume cómo iniciar, organizar y personalizar proyectos frontend de FletPlus para web, escritorio y móvil. Los ejemplos son breves y están basados en las plantillas oficiales de `fletplus/cli/templates/{web,desktop,mobile}`.

## Planificación y backlog frontend

La planificación operativa de tareas frontend vive en el [Roadmap frontend](frontend-roadmap.md). Allí se agrupan los bloques de paletas, pantalla/viewport, layout, fuentes/tipografía, assets, plantillas CLI, componentes y validación, con un criterio de finalización explícito por bloque: tests, documentación y ejemplo funcional.

El backlog histórico y transversal se conserva en [`TAREAS_IMPLEMENTACION.md`](TAREAS_IMPLEMENTACION.md). Cuando una tarea de esta guía detecte deuda de arquitectura, CI/CD, seguridad o release que exceda el alcance frontend, registra la deuda en el backlog general y deja en el roadmap solo la referencia o decisión de producto.

## Plantilla fullstack

Si tu proyecto necesita separar interfaz, lógica Python local, modelos compartidos, documentación y despliegue desde el inicio, usa la guía específica de [proyectos fullstack](fullstack-projects.md). La plantilla se genera con `fletplus create MiProducto --target fullstack` o `fletplus create MiProducto --template fullstack`.

## Crear un proyecto por destino

Todos los proyectos se crean con `fletplus create`. Usa `--target` para elegir el destino inicial y añade opciones visuales cuando quieras dejar la marca definida desde el primer commit.

### Web

```bash
fletplus create MiWeb --target web --preset landing --palette blue --theme-mode light --font Inter --layout-density comfortable
cd MiWeb
fletplus run
fletplus build --target web
```

La plantilla web incluye un punto de entrada preparado para navegador, scroll automático, registro PWA y generación de `manifest.json` y `service_worker.js` antes de iniciar la app:

```python
frontend: FrontEndConfig = create_frontend_config()
PWA_DIR = Path("web")
PWA_ASSETS = ["/", "manifest.json", "service_worker.js"]


def main(page: ft.Page) -> None:
    page.title = "MiWeb"
    page.scroll = ft.ScrollMode.AUTO
    frontend.apply_to_page(page)
    register_pwa(page, "manifest.json", "service_worker.js")
    page.add(build_home(page))
```

### Escritorio

```bash
fletplus create Backoffice --target desktop --preset admin --palette slate --theme-mode dark --font Inter
cd Backoffice
fletplus run
fletplus build --target desktop
```

La plantilla desktop prioriza ventana redimensionable, ancho mínimo y un layout con sidebar persistente:

```python
def configure_window(page: ft.Page) -> None:
    safe_set_window_attr(page, "width", 1280)
    safe_set_window_attr(page, "height", 820)
    safe_set_window_attr(page, "min_width", 960)
    safe_set_window_attr(page, "min_height", 640)
    safe_set_window_attr(page, "resizable", True)
```

### Móvil

```bash
fletplus create MiApp --target mobile --preset mobile_app --palette indigo --theme-mode system --font Inter --layout-density compact
cd MiApp
fletplus run
fletplus build --target mobile
```

La plantilla móvil usa densidad compacta, `NavigationBar` y un contenedor seguro para pantallas pequeñas:

```python
def build_navigation() -> ft.NavigationBar:
    return ft.NavigationBar(
        destinations=[
            make_navigation_bar_destination(icon=get_flet_icon("HOME", "home"), label="Inicio"),
            make_navigation_bar_destination(icon=get_flet_icon("SEARCH", "search"), label="Buscar"),
            make_navigation_bar_destination(icon=get_flet_icon("PERSON", "person"), label="Perfil"),
        ],
        height=64,
    )
```


## Matriz preset + target

`FrontEndConfig.from_mapping()` usa los presets visuales registrados como base inicial y después aplica los valores explícitos declarados por CLI o `pyproject.toml`. Si necesitas construir la misma configuración desde código, `FrontEndConfig.from_preset()` es una factory fina sobre `from_mapping()` y conserva la misma precedencia de overrides. Esto evita un sistema paralelo: `--preset` alimenta los mismos campos que se consumen durante la ejecución (`palette`, `layout_density`, `typography_tokens`, `theme_tokens`, `page_padding`, `max_content_width` y `spacing`).

| Preset recomendado | Target habitual | Paleta base | Densidad base | Padding / spacing esperados | Ancho máximo esperado | Uso principal |
| --- | --- | --- | --- | --- | --- | --- |
| `landing` | `web` | `solstice` | `spacious` | `40 / 20` | `1280` | Marketing, landing pages y hero sections. |
| `dashboard` | `web` | `fjord` | `compact` | `28 / 12` | `1280` | KPIs, analítica y tarjetas densas. |
| `admin` | `desktop` | `metropolis` | `compact` | `24 / 12` | `1180` | Backoffices, CRUDs y tablas con navegación lateral. |
| `saas` | `web` o `desktop` | `zenith` | `comfortable` | `32 / 16` | `1280` en web, `1180` en desktop | Productos SaaS, onboarding y áreas de cuenta. |
| `ecommerce` | `web` | `citrus` | `comfortable` | `24 / 16` | `1280` | Catálogos, fichas de producto y checkout. |
| `mobile_app` | `mobile`, `android-apk`, `android-aab` o `ios` | `aurora` | `comfortable` | `16 / 16` | `480` | Apps móviles táctiles y navegación inferior. |

Regla de precedencia: el preset rellena valores por defecto, pero cualquier valor explícito gana. Por ejemplo, `fletplus create Backoffice --target desktop --preset admin --palette slate --layout-density comfortable` conserva la estructura del preset `admin`, pero usa `slate` y densidad `comfortable` en la configuración generada.

## Estructura recomendada

Una plantilla nueva queda separada por responsabilidades para que la app crezca sin mezclar configuración visual, rutas y vistas:

```text
MiProyecto/
├── assets/
├── pyproject.toml
├── requirements.txt
└── src/
    ├── main.py
    └── frontend/
        ├── assets.py
        ├── config.py
        ├── layout.py
        ├── routes.py
        └── theme.py
```

Recomendaciones prácticas:

- Mantén `src/main.py` como composición de alto nivel: configurar página, aplicar tema y montar la primera vista.
- Usa `src/frontend/config.py` para tokens editables de marca, paletas, fuentes, spacing y límites de ancho.
- Usa `src/frontend/theme.py` para transformar la configuración declarativa en `FrontEndConfig` y aplicarla a Flet.
- Usa `src/frontend/layout.py` para helpers responsive reutilizables.
- Usa `src/frontend/routes.py` para rutas y pantallas iniciales; extrae vistas grandes a módulos como `src/frontend/views/`.
- Centraliza rutas a imágenes, fuentes e iconos locales en `src/frontend/assets.py`.

## Paletas

Define la paleta desde CLI o en `config.py`/`pyproject.toml`. Las plantillas exponen valores claros para cambiar el tema sin tocar todas las vistas:

```python
PALETTE_NAME = "blue"
PALETTE_MODE = "light"
DEFAULT_CUSTOM_TOKENS = {
    "colors": {"brand": "#2563EB", "surface_soft": "#F8FAFC"},
    "spacing": {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32},
    "radii": {"card": 18, "pill": 999},
}
```

Usa tokens semánticos (`brand`, `surface_soft`, `card`, `pill`) en lugar de colores sueltos dentro de cada control. Así puedes cambiar la identidad visual desde un solo archivo.


## Paletas por plataforma

Además de elegir una paleta base con `palette`, puedes declarar overrides por destino con `platform_palettes`. `palette_for_target(<target>)` parte siempre de los tokens base de `palette_tokens()` y después fusiona solo las claves específicas de la plataforma, por lo que tokens como `on_primary`, `on_surface`, `error`, `success` o `focus_ring` siguen disponibles aunque no aparezcan en el override.

Ejemplo mínimo en `pyproject.toml` para cubrir `web`, `desktop`, `mobile`, `android-apk`, `android-aab` e `ios`:

```toml
[tool.fletplus.frontend]
palette = "aurora"
mode = "light"
target = "web"

[tool.fletplus.frontend.platform_palettes.web]
primary = "#2563EB"
secondary = "#14B8A6"
background = "#F8FAFC"
surface = "#FFFFFF"

[tool.fletplus.frontend.platform_palettes.desktop]
primary = "#4F46E5"
secondary = "#0EA5E9"
background = "#EEF2FF"
surface = "#FFFFFF"

[tool.fletplus.frontend.platform_palettes.mobile]
primary = "#7C3AED"
secondary = "#EC4899"
background = "#FAF5FF"
surface = "#FFFFFF"

[tool.fletplus.frontend.platform_palettes.android-apk]
primary = "#16A34A"
secondary = "#84CC16"
background = "#F0FDF4"
surface = "#FFFFFF"

[tool.fletplus.frontend.platform_palettes.android-aab]
primary = "#059669"
secondary = "#10B981"
background = "#ECFDF5"
surface = "#FFFFFF"

[tool.fletplus.frontend.platform_palettes.ios]
primary = "#0A84FF"
secondary = "#5E5CE6"
background = "#F2F2F7"
surface = "#FFFFFF"
```

Uso desde código compartido:

```python
from fletplus.frontend import FrontEndConfig

frontend = FrontEndConfig.from_pyproject()
web_palette = frontend.palette_for_target("web")
desktop_palette = frontend.palette_for_target("desktop")
mobile_palette = frontend.palette_for_target("mobile")

assert web_palette["primary"] == "#2563EB"
assert "on_primary" in web_palette  # token heredado de palette_tokens()
```

Para builds nativos puedes resolver directamente el destino que estés empaquetando:

```python
android_apk_palette = frontend.palette_for_target("android-apk")
android_aab_palette = frontend.palette_for_target("android-aab")
ios_palette = frontend.palette_for_target("ios")
```

## Fuentes

Las plantillas separan familia principal, fallback y assets locales:

```python
FONT_FAMILY = "Inter"
FONT_FALLBACK_FAMILIES = ("Arial", "sans-serif")
FONT_ASSETS = {
    # "Inter": "assets/fonts/Inter-Regular.ttf",
}
FONT_WEIGHTS = ("w400", "w600", "w700")
```

Para usar una fuente propia:

1. Copia los `.ttf`/`.otf` a `assets/fonts/`.
2. Registra el archivo en `FONT_ASSETS` o en `[tool.fletplus.frontend.font.assets]`.
3. Ajusta `FONT_FAMILY`, los fallbacks y los pesos disponibles.
4. Ejecuta la app y revisa que `frontend.apply_to_page(page)` se mantenga en `main()`.

Ejemplo completo en `pyproject.toml` con fuente local, fallbacks y metadatos de pesos/estilos:

```toml
[tool.fletplus.frontend.font]
family = "Inter"
fallback_families = ["Roboto", "Arial", "sans-serif"]
weights = ["w400", "w600", "w700"]
styles = ["normal", "italic"]

[tool.fletplus.frontend.font.assets]
Inter = "assets/fonts/Inter-Regular.ttf"
InterSemiBold = "assets/fonts/Inter-SemiBold.ttf"
InterBold = "assets/fonts/Inter-Bold.ttf"
```

`FrontEndConfig.apply_to_page(page)` registra los assets en `page.fonts`, compone `Theme.font_family` como `Inter, Roboto, Arial, sans-serif` y avisa si un archivo local declarado no existe. Los pesos no cargan archivos por sí solos: documentan qué variantes has incluido para mantener alineados diseño, QA y configuración.

## Tipografía responsive

`FrontEndConfig` incluye roles tipográficos base para `display`, `headline`, `title`, `body`, `label` y `caption`. Los componentes de layout reutilizables aplican esos roles con `text_style()` cuando renderizan texto directamente: `HeroSection` usa `label`, `display` y `body`; `Section` usa `title` y `body`; `ToolbarSection` puede convertir textos simples a controles con rol `label`; y `FooterSection` permite `caption` para metadatos o copyright.

Puedes sobrescribir la escala por dispositivo o declarar roles personalizados en `[tool.fletplus.frontend.typography_tokens]`. Los nombres de dispositivo soportados son `mobile`, `tablet`, `desktop` y `large_desktop`:

```toml
[tool.fletplus.frontend.typography_tokens.caption.mobile]
size = 11
weight = "w400"
line_height = 1.35

[tool.fletplus.frontend.typography_tokens.caption.desktop]
size = 13
weight = "w400"
line_height = 1.32

[tool.fletplus.frontend.typography_tokens.badge.mobile]
size = 10
weight = "w600"
line_height = 1.2

[tool.fletplus.frontend.typography_tokens.badge.tablet]
size = 11
weight = "w600"
line_height = 1.2

[tool.fletplus.frontend.typography_tokens.badge.desktop]
size = 12
weight = "w700"
line_height = 1.18

[tool.fletplus.frontend.typography_tokens.badge.large_desktop]
size = 14
weight = "w700"
line_height = 1.16
```

Uso desde componentes o vistas propias:

```python
frontend = FrontEndConfig.from_pyproject()
width = int(page.width or frontend.max_content_width)

caption = ft.Text("Actualizado hace 2 min", style=frontend.text_style("caption", width))
badge = ft.Text("Beta", style=frontend.text_style("badge", width))
tokens = frontend.resolved_typography_tokens()
```

Si un rol personalizado no define todos los dispositivos, `resolve_typography()` usa la variante del perfil activo y cae a `desktop`, `mobile` o `{}` según disponibilidad. Para textos de navegación, badges o ayudas contextuales, crea roles semánticos (`nav_item`, `badge`, `helper`) en lugar de reutilizar tamaños hardcodeados.

## Responsive layout

Cada plantilla incluye helpers para consultar el perfil activo, orientación, densidad, padding seguro y ancho máximo:

```python
def responsive_shell(content: ft.Control, page: ft.Page, frontend: FrontEndConfig) -> ft.Container:
    info = viewport_info(
        page,
        profiles=frontend.responsive_profiles,
        fallback_width=frontend.max_content_width,
        padding_base=frontend.page_padding,
    )
    return max_width_container(content, page, frontend)
```

Buenas prácticas por destino:

- **Web**: limita el ancho con `build_content_shell`, usa filas con `wrap=True` y prepara cards para diferentes columnas.
- **Escritorio**: combina sidebar, panel principal y panel secundario; respeta `min_width` para evitar interfaces comprimidas.
- **Móvil**: usa `SafeArea` cuando esté disponible, densidad compacta y navegación inferior táctil.

## Rutas

La plantilla inicial usa el router declarativo de FletPlus con dos rutas mínimas:

```python
def create_router() -> Router:
    return Router(
        routes=[Route(path="/", view=home_view), Route(path="/about", view=about_view)]
    )
```

Para crecer el proyecto:

- Añade una función por pantalla (`dashboard_view`, `settings_view`, `profile_view`).
- Mantén rutas cortas y predecibles (`/`, `/settings`, `/profile`).
- Si una vista requiere estado o datos, encapsula la carga en un componente y deja la ruta como punto de composición.

## Assets

Las plantillas crean `assets/README.md` y una referencia centralizada:

```python
ASSETS_DIR = Path("assets")
PLACEHOLDER_README = ASSETS_DIR / "README.md"
```

Organiza los assets por tipo:

```text
assets/
├── fonts/
├── icons/
├── images/
└── README.md
```

Recomendaciones:

- Usa nombres estables (`logo_primary.png`, `hero_dashboard.webp`, `Inter-Regular.ttf`).
- Evita rutas hardcodeadas repetidas; exporta constantes desde `frontend/assets.py`.
- Para web/PWA, revisa que los iconos requeridos estén disponibles antes de desplegar.

## Estados de UI

Define estados visuales consistentes para carga, vacío, error y éxito. Un patrón simple es crear helpers pequeños por estado:

```python
def empty_state(title: str, message: str) -> ft.Control:
    return ft.Container(
        padding=24,
        content=ft.Column(
            controls=[ft.Text(title, style=ft.TextThemeStyle.TITLE_MEDIUM), ft.Text(message)],
            spacing=8,
        ),
    )
```

Checklist recomendado:

- **Loading**: usa skeletons o `ProgressRing` en zonas acotadas, no bloquees toda la página si no es necesario.
- **Empty**: explica qué falta y ofrece una acción primaria.
- **Error**: muestra el problema en lenguaje claro y una acción de reintento.
- **Success**: confirma la acción sin interrumpir el flujo; usa banners o snackbars.

## Build y despliegue

Comandos habituales:

```bash
fletplus build --target web
fletplus build --target desktop
fletplus build --target mobile
```

Flujo sugerido antes de publicar:

1. Ejecuta la app localmente con `fletplus run`.
2. Verifica rutas principales y breakpoints.
3. Comprueba assets y fuentes locales.
4. Ejecuta el build del target final.
5. Publica el directorio generado según tu plataforma de despliegue.

Notas por destino:

- **Web**: valida `web/manifest.json`, `web/service_worker.js`, rutas públicas y estrategia de hosting estático.
- **Escritorio**: revisa tamaño inicial, mínimos de ventana, iconos y empaquetado por sistema operativo.
- **Móvil**: valida navegación táctil, SafeArea, densidad compacta y assets de tienda antes de generar paquetes Android/iOS.

## Personalización rápida

Para cambiar marca, colores y fuente en pocos minutos:

1. **Marca visible**: cambia `page.title` y los textos principales en `src/main.py`.
2. **Color principal**: cambia `PALETTE_NAME` y `DEFAULT_CUSTOM_TOKENS["colors"]["brand"]` en `src/frontend/config.py`.
3. **Modo de tema**: ajusta `PALETTE_MODE` a `light`, `dark` o `system`.
4. **Fuente**: cambia `FONT_FAMILY`, añade fallbacks y registra archivos en `FONT_ASSETS` si son locales.
5. **Espaciado y densidad**: ajusta `SPACING`, `PAGE_PADDING` y `LAYOUT_DENSITY`.
6. **Logo e iconos**: copia los archivos a `assets/images/` o `assets/icons/` y expórtalos desde `src/frontend/assets.py`.

Ejemplo mínimo de rebranding:

```python
PALETTE_NAME = "indigo"
PALETTE_MODE = "dark"
FONT_FAMILY = "Inter"
DEFAULT_CUSTOM_TOKENS = {
    "colors": {"brand": "#7C3AED", "surface_soft": "#111827"},
    "spacing": {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32},
    "radii": {"card": 20, "pill": 999},
}
```
