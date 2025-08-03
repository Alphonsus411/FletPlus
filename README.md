# 🚀 FletPlus

**FletPlus** es una librería de componentes visuales y utilidades para acelerar el desarrollo de interfaces modernas en Python usando [Flet](https://flet.dev).  
Proporciona un conjunto de controles personalizables como tablas inteligentes, grillas responsivas, barras laterales, gestores de tema y estructura modular de apps.

---

## 📦 Instalación

```bash
pip install fletplus
```
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

# 🧪 Ejemplo rápido

```python
import flet as ft
from fletplus.components.smart_table import SmartTable

def main(page: ft.Page):
    rows = [
        ft.DataRow(cells=[ft.DataCell(ft.Text("1")), ft.DataCell(ft.Text("Alice"))]),
        ft.DataRow(cells=[ft.DataCell(ft.Text("2")), ft.DataCell(ft.Text("Bob"))]),
    ]
    table = SmartTable(["ID", "Nombre"], rows)
    page.add(table.build())

ft.app(target=main)
```

## 📈 Ejemplo de LineChart

```python
import flet as ft
from fletplus.components.charts import LineChart

def main(page: ft.Page):
    datos = [(0, 0), (1, 3), (2, 1), (3, 4)]
    grafico = LineChart(datos)
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

Todos los componentes están cubiertos por tests unitarios (ver carpeta tests/).

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
