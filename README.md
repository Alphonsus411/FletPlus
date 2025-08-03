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
| `LineChart`   | Gráfico de líneas interactivo basado en Canvas   |
| `ThemeManager` | Gestión centralizada de modo claro/oscuro        |
| `FletPlusApp`  | Estructura base para apps con navegación y tema  |
| `SystemTray`   | Icono de bandeja del sistema con eventos         |
| `PrimaryButton` / `SecondaryButton` / `IconButton` | Conjunto de botones tematizados y personalizables |
| `ResponsiveVisibility` | Oculta o muestra controles según tamaño u orientación |

# 🎨 Sistema de estilos

El dataclass `Style` permite envolver cualquier control de Flet dentro de un
`Container` aplicando márgenes, padding, colores y bordes de forma declarativa.

```python
import flet as ft
from fletplus.styles import Style

def main(page: ft.Page):
    estilo = Style(padding=20, bgcolor=ft.colors.AMBER_100, border_radius=10)
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
        PrimaryButton("Guardar", icon=ft.icons.SAVE, theme=theme),
        SecondaryButton("Cancelar", theme=theme),
        IconButton(ft.icons.DELETE, label="Eliminar", theme=theme),
    )

ft.app(target=main)
```

# 🌓 Gestor de temas

`ThemeManager` permite centralizar los tokens de estilo y alternar entre modo claro y oscuro.

## 📁 Cargar tokens/paletas desde JSON o YAML

Las paletas pueden definirse en un archivo **JSON** o **YAML** con las claves `light` y `dark`.
Además de `primary`, FletPlus reconoce grupos semánticos como `info`,
`success`, `warning` y `error` con tonos `_100` ... `_900`.

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
        ft.icons.DARK_MODE,
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
    table = SmartTable(["ID", "Nombre"], rows, style=Style(bgcolor=ft.colors.AMBER_50))
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
