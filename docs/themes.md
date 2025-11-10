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
  variantes `light`/`dark`. Si `follow_platform_theme=True` (valor por
  defecto), la variante activa seguirá al sistema.
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
- `ThemeManager.list_available_palettes()` reutiliza internamente
  `list_palettes()` para integrar el listado desde la propia instancia.

Puedes pasar el resultado a `ThemeManager.apply_palette()` o fusionarlo en
los tokens manualmente.

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
