# Perfiles de dispositivo y breakpoints

Esta guía amplía los helpers disponibles en `fletplus.utils.device_profiles`
y `fletplus.utils.device` para ayudarte a construir interfaces
verdaderamente adaptables. Aquí encontrarás los perfiles predeterminados,
las opciones extendidas y varios patrones para personalizarlos en tus
apps.

## Catálogo predeterminado

`DEFAULT_DEVICE_PROFILES` define tres segmentos que cubren desde móviles
compactos hasta escritorios de gran tamaño. Cada entrada incluye el
rango de anchura (en píxeles), la cantidad sugerida de columnas para
grilas responsivas y una descripción orientativa.

| Nombre | Rango de ancho | Columnas | Descripción |
| ------ | --------------- | -------- | ----------- |
| `mobile` | `0–599 px` | `4` | Teléfonos y pantallas muy compactas |
| `tablet` | `600–1023 px` | `8` | Tabletas, pantallas híbridas o ventanas medianas |
| `desktop` | `≥1024 px` | `12` | Escritorios, portátiles o monitores anchos |

Puedes inspeccionar estos valores programáticamente con
`iter_device_profiles()` o filtrar el perfil activo con
`get_device_profile(width)`.

```python
from fletplus.utils.device_profiles import get_device_profile

profile = get_device_profile(width=840)
print(profile.name)      # tablet
print(profile.columns)   # 8
```

## Perfilar más allá del catálogo base

`EXTENDED_DEVICE_PROFILES` añade un segmento adicional pensado para
monitores ultraanchos o paneles profesionales:

| Nombre | Rango de ancho | Columnas | Descripción |
| ------ | --------------- | -------- | ----------- |
| `large_desktop` | `≥1440 px` | `16` | Monitores ultraanchos, proyectores o estaciones profesionales |

Puedes reutilizar este catálogo extendido al invocar cualquiera de los
helpers (`device_name`, `columns_for_width`, etc.) pasando el parámetro
`profiles=EXTENDED_DEVICE_PROFILES`.

```python
from fletplus.utils.device_profiles import (
    columns_for_width,
    device_name,
    EXTENDED_DEVICE_PROFILES,
)

width = 1680
print(device_name(width, profiles=EXTENDED_DEVICE_PROFILES))  # large_desktop
print(columns_for_width(width, profiles=EXTENDED_DEVICE_PROFILES))  # 16
```

## Crear perfiles personalizados

Si necesitas breakpoints diferentes (por ejemplo, para kioscos o
ventanas emergentes dentro de la misma app), construye tu propia tupla
de `DeviceProfile` y pásala a los helpers.

```python
from fletplus.utils.device_profiles import DeviceProfile, get_device_profile

CUSTOM_PROFILES = (
    DeviceProfile("compact", 0, 479, columns=3),
    DeviceProfile("regular", 480, 1023, columns=6),
    DeviceProfile("wide", 1024, None, columns=12),
)

active = get_device_profile(width=512, profiles=CUSTOM_PROFILES)
print(active.name)  # regular
```

También puedes mezclarlos con los perfiles oficiales usando la suma de
tuplas (`DEFAULT_DEVICE_PROFILES + (DeviceProfile(...), )`) para heredar
la semántica existente.

## Integración con `ResponsiveGrid`

`ResponsiveGrid` puede recibir controles planos mediante el parámetro
`children=` o instancias enriquecidas a través de `items=`. En el ejemplo
siguiente usamos la segunda opción para envolver cada tarjeta con
`ResponsiveGridItem(control=...)`.

Cuando la extensión nativa `responsive_grid_rs` está disponible, el
backend utiliza una ruta optimizada que lee directamente los atributos de
cada `ResponsiveGridItem` (o de estructuras simples con las mismas
propiedades) para calcular los descriptores. Asegúrate de que los items
expongan `span`, `span_breakpoints`, `span_devices`, `visible_devices`,
`hidden_devices`, `min_width`, `max_width` y `responsive_style`. Si la
extensión no está presente, el comportamiento vuelve automáticamente al
fallback en Python.

El siguiente fragmento actualiza el número de columnas y muestra el
nombre del perfil activo cada vez que cambia el ancho de la ventana.

```python
import flet as ft
from fletplus.components import ResponsiveGrid, ResponsiveGridItem
from fletplus.utils.device_profiles import columns_for_width, device_name


def main(page: ft.Page) -> None:
    status = ft.Text()

    grid = ResponsiveGrid(
        columns=columns_for_width(page.window_width or 0),
        spacing=16,
        items=[
            ResponsiveGridItem(
                control=ft.Container(
                    content=ft.Text(f"Card {i}"),
                    padding=12,
                    bgcolor=ft.colors.with_opacity(0.08, ft.colors.BLUE),
                )
            )
            for i in range(1, 10)
        ],
    )

    def sync_layout(_: ft.ControlEvent | None = None) -> None:
        width = page.window_width or page.width or 0
        grid.columns = columns_for_width(width)
        status.value = f"Perfil activo: {device_name(width)}"
        page.update()

    page.on_resize = sync_layout
    page.add(status, grid)
    sync_layout()


ft.app(target=main)
```

## Controlar visibilidad con `ResponsiveVisibility`

La utilidad `fletplus.utils.responsive_visibility.ResponsiveVisibility` ofrece
un atajo para mostrar u ocultar cualquier control según el ancho, la altura o la
orientación de la ventana. Internamente delega en `ResponsiveManager`, por lo
que comparte el mismo sistema de breakpoints que otras utilidades responsivas
del paquete.

### Parámetros clave

- `width_breakpoints`: diccionario donde cada clave representa un breakpoint de
  anchura (en píxeles) y el valor indica si el control debe ser visible cuando
  la ventana supera ese ancho. `ResponsiveManager` ejecuta el callback asociado
  al breakpoint más cercano en cada cambio de tamaño, y `ResponsiveVisibility`
  utiliza ese evento para actualizar la propiedad `visible` del control.
- `height_breakpoints`: se comporta igual que la configuración de anchura, pero
  basada en la altura disponible. Puedes combinar ambos mapas para que el
  último cambio relevante (ancho o alto) determine la visibilidad.
- `orientation_visibility`: mapea orientaciones (`"portrait"` o `"landscape"`)
  a valores booleanos. `ResponsiveManager` detecta la orientación actual del
  `Page` y dispara el callback apropiado, permitiendo forzar visibilidad distinta
  según la rotación del dispositivo.

Al instanciar la clase se evalúa inmediatamente cada conjunto de breakpoints y
orientación para sincronizar el estado inicial antes de escuchar futuros
eventos de redimensionado.

### Ejemplo práctico

El siguiente fragmento crea un `Container` que solo es visible en pantallas
anchas (≥900 px), se oculta cuando la altura cae por debajo de 480 px y se
desactiva en orientación vertical. Cambia el tamaño de la ventana o rota el
dispositivo para ver cómo responde la visibilidad.

```python
import flet as ft

from fletplus.utils.responsive_visibility import ResponsiveVisibility


def main(page: ft.Page) -> None:
    banner = ft.Container(
        bgcolor=ft.colors.BLUE,
        padding=24,
        content=ft.Text("Solo en modo apaisado y con suficiente espacio"),
    )

    ResponsiveVisibility(
        page,
        banner,
        width_breakpoints={900: True, 0: False},
        height_breakpoints={0: True, 480: False},
        orientation_visibility={"landscape": True, "portrait": False},
    )

    page.add(ft.Text("Redimensiona la ventana"), banner)


ft.app(target=main)
```

`ResponsiveVisibility` combinará los eventos emitidos por `ResponsiveManager`
para aplicar la visibilidad apropiada. Por ejemplo, si la ventana mide 960×600,
la anchura activará el breakpoint `900` (visible) pero la altura activará el
breakpoint `480` (oculto), por lo que el control permanecerá oculto hasta que
ambas condiciones vuelvan a ser favorables y la orientación siga siendo
"landscape".

## Detectar plataforma con `is_mobile` y `is_desktop`

Cuando necesites condicionar secciones completas de la interfaz por la
plataforma (y no solo por el ancho disponible), apóyate en los helpers
de `fletplus.utils.device`:

```python
import flet as ft
from fletplus.utils.device import is_desktop, is_mobile


def main(page: ft.Page) -> None:
    if is_mobile(page):
        page.add(ft.Text("Bienvenido a la experiencia móvil"))
    elif is_desktop(page):
        page.add(ft.Text("Panel completo disponible en escritorio"))
    else:
        page.add(ft.Text("Interfaz optimizada para web"))


ft.app(target=main)
```

Estos helpers son ideales para alternar entre barras de navegación,
presentar diálogos específicos o activar/desactivar atajos de teclado
según la plataforma de ejecución.

## Tipografía y espaciado responsivo

`ResponsiveTypography` coordina cambios de tipografía y espaciado en función
de los breakpoints, reutilizando `ResponsiveManager` para reaccionar a cada
`resize` de la página. Internamente expone dos accesos directos —`responsive_text`
y `responsive_spacing`— que devuelven el tamaño y padding recomendados en el
momento actual, permitiendo crear estilos consistentes incluso fuera de la
instancia principal.

Cuando se vincula a un `ThemeManager`, la utilidad actualiza el token
`spacing.default` del tema activo tras cada cambio de ancho. Eso permite que
los componentes que lean el tema (por ejemplo, paddings globales o spacing de
layout) reflejen el mismo valor sin duplicar lógica.

El siguiente ejemplo se inspira en el test `test_responsive_typography_updates_text_and_spacing`
para ilustrar cómo se mantiene sincronizado el texto, el espaciado y los tokens
del tema al redimensionar la ventana:

```python
import flet as ft

from fletplus.themes.theme_manager import ThemeManager
from fletplus.utils.responsive_typography import (
    ResponsiveTypography,
    responsive_spacing,
    responsive_text,
)


def main(page: ft.Page) -> None:
    theme = ThemeManager(page)
    typography = ResponsiveTypography(page, theme)

    message = ft.Text("Hola", style=ft.TextStyle(size=responsive_text(page)))
    surface = ft.Container(padding=responsive_spacing(page), content=message)

    typography.register_text(message)
    typography.register_spacing_control(surface)

    status = ft.Text()

    def sync(_: ft.ControlEvent | None = None) -> None:
        size = responsive_text(page)
        spacing = responsive_spacing(page)
        status.value = (
            f"Texto: {size}px — Espaciado: {spacing}px — Token spacing.default: "
            f"{theme.tokens['spacing']['default']}"
        )
        page.update()

    page.on_resize = sync
    page.add(status, surface)
    sync()


ft.app(target=main)
```

Al ampliar la ventana se incrementa automáticamente `message.style.size`, se
actualiza el `padding` de `surface` y el `ThemeManager` reaplica el tema con el
nuevo valor del token de espaciado, manteniendo la coherencia de toda la UI.
