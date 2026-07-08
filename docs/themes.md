# Gestor de temas y presets

`ThemeManager` centraliza los *tokens* de diseño de una página de Flet y
permite aplicar paletas, presets y overrides según el dispositivo,
orientación o breakpoint activo. Esta guía resume la API disponible en
`fletplus.themes.theme_manager`, describe cómo leer archivos externos de
paletas/temas y cómo integrarla con señales reactivas y persistencia de
preferencias.

## Inicialización de `ThemeManager`

```python
import flet as ft
from fletplus.themes import ThemeManager


def main(page: ft.Page):
    theme = ThemeManager(
        page,
        tokens={
            "spacing": {"md": 16},
            "colors": {"background": "#101418"},
        },
        palette="aurora",
        device_tokens={
            "desktop": {"spacing": {"section": 32}},
        },
        orientation_tokens={
            "portrait": {"spacing": {"page": 16}},
        },
        breakpoint_tokens={
            1024: {"spacing": {"grid_gap": 24}},
        },
    )
    theme.apply_theme(device="desktop", orientation="portrait", width=1280)
```

Al crear la instancia puedes proporcionar:

- `tokens`: grupos de tokens base (`colors`, `typography`, `spacing`,
  `radii`, `borders`, `shadows`, `gradients`).
- `palette`: nombre de una paleta registrada o un mapeo personalizado con
  tokens comunes (`tokens` o `common`), variantes `light`/`dark` y overrides
  opcionales `web`/`desktop`/`mobile`. Si `follow_platform_theme=True` (valor
  por defecto), la variante activa seguirá al sistema.
- Overrides adaptativos (`device_tokens`, `orientation_tokens`,
  `breakpoint_tokens`). Cada estructura replica el esquema de grupos de
  tokens y se fusiona automáticamente cuando se invoca `apply_theme`.
- `palette_mode`: fuerza la variante inicial (`"light"` o `"dark"`) cuando
  se desactiva la sincronización automática.
- `follow_platform_theme`: controla si el modo se sincroniza con los eventos
  de `page.on_platform_brightness_change` o `page.on_platform_theme_change`.
  Cuando la preferencia del sistema cambia, el gestor emite una nueva señal y
  vuelve a aplicar la paleta activa.

El método `apply_theme()` refresca el `ft.Page` asignando colores, tipografías
personalizadas y cualquier token adicional almacenado bajo `theme.tokens`.

## Presets disponibles

`ThemeManager` puede arrancar desde un preset registrado. Utiliza las
funciones auxiliares de `fletplus.themes.presets` para descubrir las opciones
disponibles:

```python
from fletplus.themes.presets import list_presets, get_preset_definition

for name, description in list_presets():
    print(name, "→", description)

material = get_preset_definition("material3")
```

- `list_presets()` devuelve pares `(nombre, descripción)` listos para
  poblar un selector.
- `get_preset_definition(nombre)` regresa un diccionario con grupos de
  tokens por variante (`light`/`dark`). Puedes pasarlo directamente a
  `ThemeManager._apply_preset_definition()` si necesitas fusionarlo con
  otros datos antes de instanciar el gestor o con `ThemeManager.apply_palette`
  para combinarlo con overrides ya cargados.

Para cargar un preset durante la ejecución existe `ThemeManager.apply_palette()`
y los atajos `apply_material3()`, `apply_fluent()` y `apply_cupertino()`. Si
llamas a estos métodos con `mode="dark"`, el gestor desactiva la sincronización
automática y aplica la variante solicitada antes de refrescar la página.

## Paletas y archivos externos

Las paletas agrupan colores, gradientes y otros tokens. Puedes explorarlas y
cargar una definición personalizada:

```python
from fletplus.themes.palettes import list_palettes
from fletplus.themes.theme_manager import load_palette_from_file

for slug, description in list_palettes():
    print(slug, description)

palette = load_palette_from_file("paletas/digital_ocean.json", mode="dark")
```

- `list_palettes()` expone los nombres y descripciones de las paletas
  incluidas en FletPlus.
- `load_palette_from_file(ruta, mode="light")` lee un archivo JSON con
  claves `light` y/o `dark`, aplana los grupos de colores (por ejemplo
  `info -> 100` se convierte en `info_100`) y devuelve un diccionario de
  tokens listo para combinarse con `ThemeManager.tokens`.
- Las paletas registradas incluyen roles semánticos estándar en
  `colors`: `success`, `warning`, `error`, `info`, `surface_soft`,
  `surface_elevated`, `focus_ring`, `disabled` y `on_disabled`.
- Cuando pases una paleta completa a `ThemeManager`, el gestor fusiona primero
  tokens comunes, luego la variante `light`/`dark` activa y finalmente la
  variante de plataforma (`web`, `desktop` o `mobile`) que coincida con
  `apply_theme(device=...)`.
- `ThemeManager.list_available_palettes()` reutiliza internamente
  `list_palettes()` para integrar el listado desde la propia instancia.

Puedes pasar el resultado a `ThemeManager.apply_palette()` o fusionarlo en
los tokens manualmente.

## Estructura recomendada de paletas personalizadas

Para nuevas paletas, usa un objeto JSON con cuatro capas declarativas:

1. `tokens` (o `common`): tokens compartidos por todos los modos y plataformas.
2. `light` / `dark`: tokens específicos del modo visual.
3. `web` / `desktop` / `mobile`: overrides opcionales por plataforma.
4. Overrides de ejecución (`device_tokens`, orientación, breakpoint y
   `set_token`) que siguen teniendo prioridad desde Python.

El orden efectivo de fusión en `ThemeManager` es:

```text
tokens base → paleta común → light/dark → web/desktop/mobile →
device_tokens → orientation_tokens → breakpoint_tokens → set_token/load_token_overrides
```

Los tokens críticos recomendados dentro de `colors` son:

```text
primary, background, surface, on_surface, success, warning, error, info,
surface_soft, surface_elevated, focus_ring, disabled, on_disabled
```

Si falta alguno de estos tokens, el gestor no bloquea la aplicación, pero
emite una advertencia en el logger para ayudarte a detectar paletas
incompletas durante desarrollo.

Ejemplo mínimo con variantes por plataforma:

```json
{
  "tokens": {
    "spacing": {"page": 20, "section": 16},
    "radii": {"card": 18}
  },
  "light": {
    "colors": {
      "primary": "#2563EB",
      "background": "#F8FAFC",
      "surface": "#FFFFFF",
      "on_surface": "#111827",
      "success": "#15803D",
      "warning": "#B45309",
      "error": "#B91C1C",
      "info": "#0369A1",
      "surface_soft": "#F1F5F9",
      "surface_elevated": "#FFFFFF",
      "focus_ring": "#2563EB",
      "disabled": "#CBD5E1",
      "on_disabled": "#64748B"
    }
  },
  "dark": {
    "colors": {
      "primary": "#93C5FD",
      "background": "#020617",
      "surface": "#0F172A",
      "on_surface": "#E2E8F0",
      "success": "#86EFAC",
      "warning": "#FCD34D",
      "error": "#FCA5A5",
      "info": "#7DD3FC",
      "surface_soft": "#111827",
      "surface_elevated": "#1E293B",
      "focus_ring": "#93C5FD",
      "disabled": "#334155",
      "on_disabled": "#94A3B8"
    }
  },
  "web": {"spacing": {"page": 24}},
  "desktop": {"spacing": {"page": 28}},
  "mobile": {"spacing": {"page": 16}, "radii": {"card": 24}}
}
```

Hay un ejemplo más completo en `examples/custom_palette_platforms.json`.

## Overrides por dispositivo, orientación y breakpoint

`ThemeManager` mantiene tres mapas de overrides:

- `set_device_tokens("mobile", {...})` aplica tokens extra cuando
  `apply_theme(device="mobile")` está activo.
- `set_orientation_tokens("landscape", {...})` responde a `apply_theme`
  con `orientation="landscape"`.
- `set_breakpoint_tokens(1024, {...})` se activa cuando el ancho actual es
  mayor o igual al breakpoint indicado. Si defines múltiples breakpoints,
  la variante activa queda expuesta mediante `ThemeManager.active_breakpoint`.

Los overrides se fusionan en este orden: dispositivo → orientación → breakpoint
→ overrides persistentes (`set_token`). Esto significa que las llamadas a
`set_token("colors.primary", "#FF7043")` siempre prevalecen y se almacenan en
`overrides_signal` (ver siguiente sección).

## JSON completo para `load_theme_from_json`

`ThemeManager.load_theme_from_json("ruta.json")` utiliza
`fletplus.themes.theme_manager._parse_theme_json` para normalizar la entrada.
El archivo puede verse así:

```json
{
  "preset": "material3",
  "mode": null,
  "tokens": {
    "spacing": {
      "md": 20,
      "xl": 32
    },
    "radii": {
      "card": 18
    }
  },
  "light": {
    "colors": {
      "primary": "#6750A4",
      "background": "#FFFBFE"
    },
    "gradients": {
      "hero": {
        "colors": ["#6750A4", "#B583F5"],
        "begin": [0.0, -1.0],
        "end": [0.0, 1.0]
      }
    }
  },
  "dark": {
    "colors": {
      "primary": "#D0BCFF",
      "background": "#1C1B1F"
    }
  }
}
```

- `preset` es opcional; si está presente se fusiona antes de aplicar los
  overrides.
- `tokens` define ajustes comunes a las variantes `light` y `dark`.
- Cada variante puede agregar o reemplazar grupos específicos.
- `web`, `desktop` y `mobile` son opcionales y se fusionan cuando el
  dispositivo activo coincide con `apply_theme(device="...")`.
- `mode` admite `"light"` o `"dark"`. Si lo dejas en `null` (o lo omites)
  y `follow_platform_theme=True`, el gestor seguirá la preferencia del
  sistema (modo automático). Cuando se detecte un cambio en la plataforma,
  se actualizará `mode_signal` y se re-renderizará la página.

Si solo necesitas validar el archivo sin aplicarlo, usa la función de módulo
`load_theme_from_json(ruta)` que devuelve el diccionario normalizado.

## Reaccionar a las señales del tema

`ThemeManager` expone tres señales reactivas (`fletplus.state.Signal`):

- `mode_signal`: emite `True` cuando el modo oscuro está activo. Úsala para
  actualizar botones o iconos que cambian según la variante.
- `tokens_signal`: emite un *snapshot* completo de los tokens efectivos tras
  cada `apply_theme`. El comparador siempre devuelve `False`, por lo que
  todos los cambios disparan listeners.
- `overrides_signal`: refleja los tokens personalizados registrados mediante
  `set_token` o `load_token_overrides`.

Ejemplo de integración con la librería de estado:

```python
from fletplus.state import watch

watch(theme.mode_signal, lambda is_dark: toggle_button.set_icon(
    "dark_mode" if is_dark else "light_mode"
))

watch(theme.tokens_signal, lambda tokens: update_preview(tokens["colors"]))

watch(theme.overrides_signal, lambda overrides: persist(overrides))
```

Para persistir las decisiones del usuario (por ejemplo, colores ajustados en
un editor), combina `overrides_signal` con los proveedores descritos en la
[guía de almacenamiento reactivo](storage.md). Cuando cargues la app, inyecta
las preferencias previas mediante `ThemeManager.load_token_overrides()` antes
de invocar `apply_theme()`. Si además guardas el modo claro/oscuro elegido,
puedes restaurarlo ajustando `theme.set_dark_mode(valor, refresh=False)` antes
de aplicar los tokens para evitar parpadeos.

---

Con estos bloques puedes construir selectores de tema avanzados, sincronizar
la UI con la configuración del sistema y ofrecer personalización persistente
sin duplicar lógica.


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

## Tipografía como tokens del tema

La configuración de frontend publica la escala tipográfica dentro del grupo de
tokens `typography` al ejecutar `FrontEndConfig.apply_to_page(page)` o al usar
`ResponsiveTypography` con un `ThemeManager`. Esto permite que un tema comparta
los mismos roles visuales que la capa responsiva:

```python
from fletplus import FrontEndConfig

config = FrontEndConfig(
    typography_tokens={
        "display": {
            "mobile": {"size": 40, "weight": "w700", "line_height": 1.1},
            "desktop": {"size": 56, "weight": "w700", "line_height": 1.05},
        },
        "body": {
            "mobile": {"size": 14, "weight": "w400", "line_height": 1.55},
            "desktop": {"size": 18, "weight": "w400", "line_height": 1.5},
        },
    }
)

theme = config.apply_to_page(page)
print(theme.tokens["typography"]["display"]["desktop"])
```

Las plantillas de la CLI exponen `TYPOGRAPHY_TOKENS` en
`src/frontend/config.py` y los fusionan en `create_frontend_config()`, de modo
que puedes ajustar tipografías sin tocar la lógica de arranque.
