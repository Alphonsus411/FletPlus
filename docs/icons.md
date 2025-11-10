# Iconos en FletPlus

FletPlus incluye un módulo `fletplus.icons` que centraliza el uso de iconos en
las aplicaciones. De forma predeterminada se cargan dos catálogos integrados:

- **Material** (`material`): usa los nombres estándar de Flet como `home`,
  `settings` o `help`.
- **Lucide** (`lucide`): expone los identificadores `lucide:` utilizados por el
  set Lucide, por ejemplo `lucide:alert-triangle`.

## Uso básico

```python
from fletplus.icons import icon

home_icon = icon("home")
lucide_info = icon("info", icon_set="lucide")
```

La función `icon()` valida que el icono exista y, si no se encuentra, puede
utilizar un fallback configurable:

```python
# Usa "settings" si "preferences" no existe en el catálogo solicitado
preferences = icon("preferences", fallback="settings")
```

Si se desea trabajar de forma orientada a objetos también está disponible la
clase `Icon`, que construye instancias de `ft.Icon` con los mismos parámetros.

## Registro de iconos personalizados

Puedes extender los catálogos en tiempo de ejecución sin necesidad de modificar
la librería.

```python
from fletplus.icons import register_icon, register_icon_set

# Añade un icono al catálogo Lucide
register_icon("brand", "lucide:brand", icon_set="lucide")

# Crea un set completamente nuevo
register_icon_set("custom", {
    "logo": "custom:logo",
    "alt_logo": "custom:alt-logo",
})
```

Tras registrar un icono o set personalizado, `icon()` y `resolve_icon_name()`
pueden utilizarlo inmediatamente. Los catálogos personalizados también aparecen
en `available_icon_sets()` y `list_icons()`.
