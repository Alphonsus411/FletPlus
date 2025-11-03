# 🚀 FletPlus

**FletPlus** es una librería de componentes visuales y utilidades para acelerar el desarrollo de interfaces modernas en Python usando [Flet](https://flet.dev).  
Proporciona un conjunto de controles personalizables como tablas inteligentes, grillas responsivas, barras laterales, gestores de tema y estructura modular de apps.

---

## 📦 Instalación

```bash
pip install fletplus
```
- Incluye sistema de estilos, botones personalizados y utilidades de diseño responsivo.
- **Requiere Python 3.9+ y flet>=0.27.0**

## 🧩 Componentes incluidos

| Componente      | Descripción                                       |
|----------------|---------------------------------------------------|
| `SmartTable`   | Tabla con paginación y ordenamiento integrados   |
| `SidebarAdmin` | Menú lateral dinámico con ítems y selección       |
| `ResponsiveGrid` | Distribución de contenido adaptable a pantalla |
| `ResponsiveContainer` | Aplica estilos según breakpoints definidos |
| `AdaptiveNavigationLayout` | Shell con navegación que cambia entre barra inferior, riel o columna según la plataforma |
| `UniversalAdaptiveScaffold` | Estructura integral con navegación adaptable, panel secundario y controles de accesibilidad integrados |
| `LineChart`   | Gráfico de líneas interactivo basado en Canvas   |
| `ThemeManager` | Gestión centralizada de modo claro/oscuro        |
| `FletPlusApp`  | Estructura base para apps con navegación y tema  |
| `SystemTray`   | Icono de bandeja del sistema con eventos         |
| `PrimaryButton` / `SecondaryButton` / `IconButton` | Conjunto de botones tematizados y personalizables |
| `ResponsiveVisibility` | Oculta o muestra controles según tamaño u orientación |

## 🔁 Gestión de estado reactivo

FletPlus incorpora un módulo `fletplus.state` con primitivas reactivas ligeras
para compartir datos entre componentes sin acoplarlos al árbol de controles.

```python
import flet as ft
from fletplus import FletPlusApp, Signal, Store


store = Store({"count": 0})


def counter_view():
    label = ft.Text()
    store.bind("count", label, attr="value", transform=lambda v: f"Total: {v}")

    def increment(_):
        store.update("count", lambda value: value + 1)

    return ft.Column(
        controls=[
            label,
            ft.ElevatedButton("Sumar", on_click=increment),
        ]
    )


def main(page: ft.Page):
    app = FletPlusApp(page, {"Inicio": counter_view}, state=store)
    app.build()


ft.app(target=main)
```

- `Signal` expone los métodos `.get()` y `.set()` junto con `signal.bind_control`
  para sincronizar atributos de controles Flet y ejecutar `update()`
  automáticamente.
- `Store` centraliza señales nombradas y ofrece `store.subscribe()` y
  `store.derive()` para escuchar *snapshots* inmutables o crear señales
  derivadas.

# 📝 Logging

FletPlus utiliza el módulo estándar `logging` para registrar mensajes de la
biblioteca. De forma predeterminada, `FletPlusApp.start` configura un registro
básico a nivel `INFO`.

Para cambiar el nivel de salida en tu aplicación, ajusta `logging` antes de
iniciar FletPlus:

```python
import logging
from fletplus.core import FletPlusApp

logging.basicConfig(level=logging.DEBUG)

FletPlusApp.start(routes)
```

# 🎨 Sistema de estilos

El dataclass `Style` permite envolver cualquier control de Flet dentro de un
`Container` aplicando márgenes, padding, colores y bordes de forma declarativa.

```python
import flet as ft
from fletplus.styles import Style

def main(page: ft.Page):
    estilo = Style(padding=20, bgcolor=ft.Colors.AMBER_100, border_radius=10)
    saludo = estilo.apply(ft.Text("Hola estilo"))
    page.add(saludo)

ft.app(target=main)
```

# 🖱️ Botones personalizados

Incluye tres variantes listas para usar: `PrimaryButton`, `SecondaryButton` e
`IconButton`, que aprovechan los tokens definidos en `ThemeManager` y aceptan
`Style` para ajustes adicionales.

```python
import flet as ft
from fletplus.components.buttons import PrimaryButton, SecondaryButton, IconButton
from fletplus.themes.theme_manager import ThemeManager

def main(page: ft.Page):
    theme = ThemeManager(page, tokens={"typography": {"button_size": 16}})
    theme.apply_theme()
    page.add(
        PrimaryButton("Guardar", icon=ft.Icons.SAVE, theme=theme),
        SecondaryButton("Cancelar", theme=theme),
        IconButton(ft.Icons.DELETE, label="Eliminar", theme=theme),
    )

ft.app(target=main)
```

# 🌓 Gestor de temas

`ThemeManager` permite centralizar los tokens de estilo y alternar entre modo claro y oscuro.

### Nuevas paletas predefinidas

Además de las variantes originales ahora dispones de un catálogo ampliado con
paletas listas para aplicar en cualquier dispositivo:

* `aurora`
* `sunset`
* `lagoon`
* `midnight` – tonos profundos azul marino con acentos cian para dashboards nocturnos
* `sakura` – gradientes pastel inspirados en cerezos para interfaces creativas
* `selva` – verdes botánicos con acentos lima ideales para proyectos sostenibles
* `marina` – combinación de azules oceánicos con turquesas pensada para interfaces de analítica y streaming de datos
* `terracotta` – tierra quemada con acentos turquesa para sitios editoriales cálidos
* `cyberwave` – neones futuristas para paneles nocturnos
* `zenith` – azules corporativos con destellos dorados
* `oasis` – desértica con turquesas refrescantes
* `lumen` – estética minimalista iluminada con ámbar
* `solstice` – transición cálida del amanecer equilibrada con azules vibrantes
* `noir` – monocromo elegante con acentos eléctricos para experiencias premium

Todas ellas incluyen tokens de gradiente `gradients.app_header` compatibles con el encabezado adaptable del layout.

## 📁 Cargar tokens/paletas desde JSON o YAML

Las paletas pueden definirse en un archivo **JSON** o **YAML** con las claves `light` y `dark`.
Además de `primary`, FletPlus reconoce grupos semánticos como `info`,
`success`, `warning` y `error` con tonos `_100` ... `_900` que luego se
pueden consultar o modificar dinámicamente mediante `get_token` y
`set_token`.

**palette.json**
```json
{
  "light": {"primary": "#2196F3"},
  "dark": {"primary": "#0D47A1"}
}
```

**palette.yaml**
```yaml
light:
  primary: "#2196F3"
dark:
  primary: "#0D47A1"
```

### Grupos de colores semánticos

Además de la clave `primary`, se pueden definir grupos de estado con distintos tonos.
Los grupos admitidos son `info`, `success`, `warning` y `error`, cada uno con
tonos `100` a `900`:

```json
{
  "light": {
    "info": {
      "100": "#BBDEFB",
      "500": "#2196F3",
      "900": "#0D47A1"
    },
    "success": {
      "100": "#C8E6C9",
      "500": "#4CAF50",
      "900": "#1B5E20"
    },
    "warning": {
      "100": "#FFECB3",
      "500": "#FFC107",
      "900": "#FF6F00"
    },
    "error": {
      "100": "#FFCDD2",
      "500": "#F44336",
      "900": "#B71C1C"
    }
  }
}
```

`load_palette_from_file` aplanará automáticamente estas secciones en claves
como `info_100` o `warning_500`. Revisa el archivo
[`palette_extended.json`](examples/palette_extended.json) para una paleta
completa con todos los tonos.

## 📐 Grid adaptable por dispositivo

El nuevo `ResponsiveGridItem` permite definir *span* personalizados tanto por
breakpoint como por tipo de dispositivo (móvil, tablet, escritorio). También
puedes asignar estilos responsivos a cada item mediante `ResponsiveStyle`.

```python
import flet as ft
from fletplus.components import ResponsiveGrid, ResponsiveGridItem
from fletplus.styles import Style
from fletplus.utils.responsive_style import ResponsiveStyle

grid = ResponsiveGrid(
    items=[
        ResponsiveGridItem(
            ft.Text("Destacado"),
            span_devices={"mobile": 12, "tablet": 6, "desktop": 4},
            responsive_style=ResponsiveStyle(
                width={800: Style(padding=ft.Padding(24, 24, 24, 24))}
            ),
        ),
        ResponsiveGridItem(ft.Text("Complemento"), span_breakpoints={0: 12, 900: 4}),
    ],
    run_spacing=24,
)
```

Nuevas capacidades del grid responsivo:

- **Perfiles ampliados**: puedes pasar `device_profiles` personalizados o usar los
  predeterminados que ahora incluyen `large_desktop`, ideal para monitores
  ultraanchos. El parámetro `device_columns` te permite mapear cuántas columnas
  debe renderizar cada perfil sin reescribir breakpoints manuales.
- **Espaciado inteligente**: activa `adaptive_spacing=True` para que el padding
  entre tarjetas y el `run_spacing` crezcan gradualmente en tabletas, escritorios
  y grandes pantallas, manteniendo densidades legibles.
- **Cabeceras configurables**: define `header_layout="centered"` o
  `header_layout="split"` para cambiar la distribución de título, metadatos y
  acciones. También puedes aportar una imagen o degradado mediante
  `section_background_image`, `section_overlay_color` y
  `section_gradient_token` para crear secciones tipo "hero" en la web.
- **Orientación consciente**: los parámetros `section_orientation_backgrounds`
  y `section_orientation_gradient_tokens` permiten alternar fondos y degradados
  distintos al rotar la pantalla entre modo retrato y paisaje, manteniendo un
  diseño coherente en smartphones y tablets.
- **Densidad adaptable**: con `section_gap_by_device` y
  `section_max_content_width_by_device` puedes fijar espacios y anchos máximos
  específicos para móvil, tablet, escritorio y monitores ultraanchos sin crear
  contenedores manuales.
- **Márgenes contextuales**: controla el aire alrededor de cada sección con
  `section_margin` y `section_margin_by_orientation`, ideal para interfaces
  móviles en las que necesitas reducir bordes en modo retrato y ampliarlos en
  pantallas de escritorio.
- **Cabeceras dinámicas**: personaliza el fondo de la cabecera mediante
  `header_background_by_device`, `header_background_by_orientation` y los nuevos
  mapas de degradado `header_gradient_by_device`,
  `header_gradient_tokens_by_device` y `header_gradient_tokens_by_orientation`.
- **Acciones adaptadas al contexto**: ajusta la alineación de botones y filtros
  del encabezado con `header_actions_alignment`, así como mapas por dispositivo
  u orientación para mejorar la ergonomía en smartphones y escritorios.

## 🧭 Encabezados más expresivos

`AdaptiveNavigationLayout` detecta automáticamente los gradientes definidos en
`ThemeManager` y envuelve el encabezado dentro de un contenedor estilizado con
sombras suaves, bordes redondeados y soporte para botones de menú cuando se usa
en móviles. Puedes aportar tu propio `Style` o `ResponsiveStyle` a través del
parámetro `header_style`, o especificar tokens de color alternativos mediante
`header_background_token`.

El componente `AdaptiveAppHeader` también evoluciona para escenarios
multiplataforma:

- Ajusta automáticamente la maquetación según la orientación (`layout_by_orientation`)
  para mantener acciones en línea en escritorio y apilarlas en móviles.
- Permite alternar la posición del *hero* con `hero_position` o forzar un ancho
  máximo por dispositivo (`hero_max_height_by_device`), logrando portadas más
  cinematográficas en web sin sacrificar legibilidad en teléfonos.
- Aplica relaciones de aspecto (`hero_aspect_ratio`) y rellenos adaptativos
  para que ilustraciones, gráficos o vídeos se escalen de forma uniforme al
  compartir la misma base de código entre web, escritorio y apps móviles.

## 🔄 Ejemplo completo con ThemeManager

El siguiente ejemplo muestra cómo cargar la paleta y alternar entre modo claro y oscuro:

```python
import flet as ft
from fletplus.themes.theme_manager import ThemeManager, load_palette_from_file
import yaml


def main(page: ft.Page):
    # Cargar tokens de colores desde JSON
    colors = load_palette_from_file("palette.json", mode="light")

    # Si prefieres YAML:
    # with open("palette.yaml", "r", encoding="utf-8") as fh:
    #     colors = yaml.safe_load(fh)["light"]

    theme = ThemeManager(page, tokens={"colors": colors})
    theme.apply_theme()

    # Botón para alternar entre modo claro y oscuro
    toggle = ft.IconButton(
        ft.Icons.DARK_MODE,
        on_click=lambda _: theme.toggle_dark_mode(),
    )
    page.add(ft.Text("Modo actual"), toggle)


ft.app(target=main)
```

# 📱 Diseño responsivo por dispositivo

Con `ResponsiveVisibility` se puede mostrar u ocultar un control según el
ancho, alto u orientación de la página, facilitando interfaces adaptables.

```python
import flet as ft
from fletplus.utils.responsive_visibility import ResponsiveVisibility

def main(page: ft.Page):
    txt = ft.Text("Solo en pantallas anchas")
    ResponsiveVisibility(page, txt, width_breakpoints={0: False, 800: True})
    page.add(txt)

ft.app(target=main)
```

# ♿ Interfaz adaptable y accesible

- **`AdaptiveNavigationLayout`** alterna automáticamente entre barra de
  navegación inferior, riel lateral extendido o compactado y columnas
  adaptadas según el breakpoint detectado (`mobile`, `tablet` o `desktop`).
  El *callback* `content_builder` recibe el nombre del dispositivo activo para
  ajustar cada vista.
- **`AccessibilityPreferences`** facilita activar alto contraste, escalado de
  texto, reducción de transiciones y mostrar captions textuales pensados para
  personas con limitaciones visuales o auditivas.
- **`AccessibilityPanel`** ofrece un panel interactivo de controles (escala de
  texto, alto contraste, animaciones y subtítulos) que se redistribuye según el
  ancho disponible y puede incorporarse en páginas web, escritorios o móviles.
- Los **perfiles de dispositivo** expuestos en `fletplus.utils` indican el
  número recomendado de columnas y permiten reaccionar a cambios de tamaño sin
  reescribir breakpoints manualmente.

## 🌐 UniversalAdaptiveScaffold: UI universal y accesible

`UniversalAdaptiveScaffold` combina navegación adaptable, paneles secundarios
y controles de accesibilidad pensados para lector de pantalla y personas con
baja audición. En móviles muestra una barra inferior accesible; en tabletas un
`NavigationRail` compacto y en escritorio habilita un riel expandido junto a un
panel lateral con información o herramientas.

Novedades recientes del scaffold universal:

- **Modo `large_desktop`**: al detectar resoluciones ultraanchas se activa un
  tercer panel lateral que puede mostrar simultáneamente el panel de
  accesibilidad (auto habilitable) y el secundario de contenido.
- **Cabecera tematizada**: la barra superior lee automáticamente el token
  `gradients.app_header` del `ThemeManager` (o el que indiques mediante
  `app_bar_gradient_token`) y ajusta padding según el dispositivo, aportando una
  estética consistente en web y escritorio.
- **Control de anchura**: usa `desktop_max_content_width` para fijar el ancho
  máximo del contenido central y `large_desktop_panel_width` para definir cuánto
  ocupa el panel auxiliar en monitores grandes.

```python
import flet as ft
from fletplus.components import (
    AdaptiveNavigationItem,
    UniversalAdaptiveScaffold,
    AccessibilityPanel,
)
from fletplus.utils.accessibility import AccessibilityPreferences


def main(page: ft.Page):
    prefs = AccessibilityPreferences(enable_captions=True, text_scale=1.1)
    items = [
        AdaptiveNavigationItem("home", "Inicio", ft.Icons.HOME_OUTLINED),
        AdaptiveNavigationItem("reports", "Reportes", ft.Icons.INSIGHTS_OUTLINED),
        AdaptiveNavigationItem("settings", "Ajustes", ft.Icons.SETTINGS_OUTLINED),
    ]

    scaffold = UniversalAdaptiveScaffold(
        navigation_items=items,
        accessibility=prefs,
        accessibility_panel=AccessibilityPanel(preferences=prefs),
        page_title="Panel adaptable",
        header_controls=[ft.Text("Estado del sistema", size=14)],
        content_builder=lambda item, _: ft.Text(f"Vista: {item.label}"),
        secondary_panel_builder=lambda item: ft.Text(f"Panel lateral de {item.label}"),
    )

    page.add(scaffold.build(page))


ft.app(target=main)
```

```python
import flet as ft
from fletplus.components import AccessibilityPanel, AdaptiveDestination, AdaptiveNavigationLayout
from fletplus.utils.accessibility import AccessibilityPreferences


def main(page: ft.Page):
    prefs = AccessibilityPreferences(enable_captions=True, text_scale=1.1)
    panel = AccessibilityPanel(preferences=prefs)

    layout = AdaptiveNavigationLayout(
        [
            AdaptiveDestination("Inicio", ft.Icons.HOME_OUTLINED),
            AdaptiveDestination("Reportes", ft.Icons.INSERT_CHART_OUTLINED),
        ],
        lambda index, device: ft.Text(f"Vista {index} en {device}"),
        accessibility=prefs,
        accessibility_panel=panel,
    )

    page.add(layout.build(page))


ft.app(target=main)
```

## 🎨 Estilos responsivos

Para aplicar diferentes estilos según el tamaño u orientación de la página se
puede combinar :class:`ResponsiveManager` con :class:`ResponsiveStyle`.

```python
import flet as ft
from fletplus.styles import Style
from fletplus.utils import ResponsiveManager, ResponsiveStyle

def main(page: ft.Page):
    texto = ft.Text("Hola")
    estilos = ResponsiveStyle(width={0: Style(text_style=ft.TextStyle(size=10)), 600: Style(text_style=ft.TextStyle(size=20))})
    manager = ResponsiveManager(page)
    manager.register_styles(texto, estilos)
    page.add(texto)

ft.app(target=main)
```

# 🧱 ResponsiveContainer

`ResponsiveContainer` simplifica la aplicación de estilos responsivos a un control
sin manejar manualmente las señales de tamaño de la página.

```python
import flet as ft
from fletplus.components.responsive_container import ResponsiveContainer
from fletplus.styles import Style
from fletplus.utils.responsive_style import ResponsiveStyle

def main(page: ft.Page):
    estilos = ResponsiveStyle(width={0: Style(padding=10), 600: Style(padding=30)})
    contenedor = ResponsiveContainer(ft.Text("Hola"), estilos)
    page.add(contenedor.build(page))

ft.app(target=main)
```

# 🧪 Ejemplo rápido

```python
import flet as ft
from fletplus.components.smart_table import SmartTable
from fletplus.styles import Style

def main(page: ft.Page):
    rows = [
        ft.DataRow(cells=[ft.DataCell(ft.Text("1")), ft.DataCell(ft.Text("Alice"))]),
        ft.DataRow(cells=[ft.DataCell(ft.Text("2")), ft.DataCell(ft.Text("Bob"))]),
    ]
    table = SmartTable(["ID", "Nombre"], rows, style=Style(bgcolor=ft.Colors.AMBER_50))
    page.add(table.build())

ft.app(target=main)
```

## 📈 Ejemplo de LineChart

```python
import flet as ft
from fletplus.components.charts import LineChart
from fletplus.styles import Style

def main(page: ft.Page):
    datos = [(0, 0), (1, 3), (2, 1), (3, 4)]
    grafico = LineChart(datos, style=Style(padding=10))
    page.add(grafico.build())

ft.app(target=main)
```

## 🔔 Ejemplo de SystemTray

```python
from fletplus.desktop.system_tray import SystemTray

tray = SystemTray(icon="icon.png", menu=["Abrir", "Salir"])
tray.on_click(lambda: print("Clic en el icono"))
tray.show()
```
# 🔧 Estructura del proyecto

fletplus/
├── components/
│   ├── smart_table.py
│   ├── sidebar_admin.py
│   └── responsive_grid.py
├── themes/
│   └── theme_manager.py
├── core.py  ← Clase FletPlusApp

# 📋 Tests

Todos los componentes aceptan un argumento opcional `style` de tipo
[`Style`](./fletplus/styles/style.py) para envolver la estructura principal con
propiedades de margen, color de fondo y más. Los tests cubren estos
comportamientos (ver carpeta tests/).

```bash
pytest --cov=fletplus
```

# 📱 Modo móvil

> **Nota**: Para compilar y ejecutar en Android o iOS, es necesario tener configurado el entorno de Flet para cada plataforma. Consulta la [documentación oficial de instalación](https://flet.dev/docs/install/) y los [requisitos de despliegue móvil](https://flet.dev/docs/guides/mobile/) antes de generar tu app.

# 🌐 Construcción PWA

Para generar los archivos necesarios de una PWA se incluye el módulo
`fletplus.web.pwa`. Un flujo típico de build sería:

```python
from fletplus.web.pwa import generate_manifest, generate_service_worker

generate_manifest(
    name="Mi App",
    icons=[{"src": "icon.png", "sizes": "192x192", "type": "image/png"}],
    start_url="/",
    output_dir="web",
)
generate_service_worker(["/", "/main.css"], output_dir="web")
```

Durante el inicio de la aplicación se puede registrar con:

```python
from fletplus.web.pwa import register_pwa

def main(page):
    register_pwa(page)
```

# 🛠️ Contribuir

Las contribuciones son bienvenidas:

1. **Haz un fork**

2. **Crea tu rama**: git checkout -b feature/nueva-funcionalidad

3. **Abre un PR** explicando el cambio

# 📄 Licencia

MIT License

Copyright (c) 2025 Adolfo González

# 💬 Contacto

Desarrollado por Adolfo González Hernández. 

**email**: adolfogonzal@gmail.com
