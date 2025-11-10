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
        controls=[
            ResponsiveGridItem(
                content=ft.Container(
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
