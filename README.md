# 🚀 FletPlus

**FletPlus** es una librería de componentes avanzados y utilidades para [Flet](https://flet.dev), diseñada para construir aplicaciones modernas, responsivas y escalables 100% en Python.

> 🎯 Ideal para CRMs, dashboards administrativos, herramientas internas o cualquier interfaz rica en datos.

---

## ✨ Características principales

- ✅ `SmartTable` — Tabla dinámica con paginación y ordenamiento.
- ✅ `SidebarAdmin` — Menú lateral adaptable para paneles.
- ✅ `ResponsiveGrid` — Distribución de elementos adaptable a diferentes tamaños de pantalla.
- ✅ `ThemeManager` — Control centralizado de tema claro/oscuro y colores principales.
- 🛠️ Listo para integrarse con tus proyectos Flet actuales.

---

## 🧱 Estructura del proyecto

````yaml
fletplus/ ├── components/ │ ├── smart_table.py │ ├── sidebar_admin.py │ └── responsive_grid.py ├── themes/ │ └── theme_manager.py ├── utils/ │ └── responsive_manager.py ├── core.py
````


---

## 📦 Instalación

> 🔧 Requisitos: Python 3.8+ y `flet`

```bash
pip install flet
````
Y luego clona este repositorio o instálalo como paquete

## 🚀 Uso rápido

````python
from fletplus.core import FletPlusApp
import flet as ft

def home():
    return ft.Text("Inicio")

def usuarios():
    return ft.Text("Gestión de usuarios")

routes = {
    "Inicio": home,
    "Usuarios": usuarios,
}

sidebar_items = [
    {"title": "Inicio", "icon": ft.icons.HOME},
    {"title": "Usuarios", "icon": ft.icons.PEOPLE},
]

FletPlusApp.start(routes=routes, sidebar_items=sidebar_items, title="Mi CRM")

````
## 📂 Ejemplos

Explora la carpeta examples/ para ver una demo completa con tabla, sidebar y temas.

## 🛠️ En desarrollo

 -  **CrudGenerator** para construir formularios automáticos

 - **Soporte** de plugins

 - **Guardado** de preferencias del usuario

 - **Internacionalización** (i18n)

## 🤝 Contribuciones

¿Quieres ayudar a mejorar FletPlus? ¡Eres bienvenido!

- Clona el repo.

- Crea tus propios componentes.

- Haz pull requests.

## 📝 Licencia

MIT © 2025 Adolfo González



