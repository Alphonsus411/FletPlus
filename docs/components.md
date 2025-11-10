# Catálogo de componentes de FletPlus

Este resumen agrupa los controles expuestos por `fletplus.components`
según su propósito principal. Utiliza las categorías empleadas en la
documentación para ubicar rápidamente el componente que necesitas y
ver cómo se relaciona con el ecosistema de FletPlus.

## Navegación adaptable

- **AdaptiveNavigationLayout** y **AdaptiveDestination**: shell de navegación
  que alterna entre barra inferior, riel o columna según la plataforma.
- **UniversalAdaptiveScaffold** y **AdaptiveNavigationItem**: armazón que
  combina navegación adaptable con panel secundario, acciones rápidas y
  accesibilidad integrada.
- **SidebarAdmin**: menú lateral configurable con secciones anidadas y
  estado persistente.
- **CommandPalette**: paleta universal para lanzar acciones desde el
  teclado con búsqueda incremental.

## Cabeceras y overlays

- **AdaptiveAppHeader**: cabecera contextual que muestra acciones y
  navegación secundaria según el ancho disponible.
- **MetadataBadge**: distintivo auxiliar para cabeceras que destaca el
  estado actual (beta, prerelease, etc.).
- **CaptionOverlay**: capa superpuesta para enriquecer imágenes o
  vídeos con títulos y descripciones.

## Accesibilidad

- **AccessibilityPanel**: panel flotante que reúne accesos directos a
  preferencias de accesibilidad y tamaño de fuente.

## Datos

- **SmartTable**: tabla virtualizada con filtros, ordenamiento
  multi-columna y edición en línea.
- **LineChart**: gráfico de líneas interactivo basado en canvas con
  soporte para temas claros y oscuros.

## Layouts

- **ResponsiveContainer**: contenedor que aplica estilos basados en
  breakpoints de ancho y alto.
- **ResponsiveGrid** y **ResponsiveGridItem**: sistema de grilla que
  reparte columnas dinámicamente según el tamaño del viewport.
- **FlexRow** y **FlexColumn**: implementaciones flexibles de filas y
  columnas con alineación granular.
- **Grid** y **GridItem**: grilla densa para paneles modulares.
- **Wrap**: distribución fluida de chips o tarjetas que se ajusta en
  varias filas/columnas.
- **Stack** y **StackItem**: composición en capas para overlays y
  elementos posicionados.
- **Spacer**: control auxiliar para reservar espacio flexible dentro de
  filas o columnas.

## Botones tematizados

Aunque no forman parte de las categorías anteriores, FletPlus expone
una familia de botones listos para usarse con el sistema de temas del
paquete:

- **PrimaryButton**, **SecondaryButton**, **SuccessButton**,
  **WarningButton**, **DangerButton**, **InfoButton**, **OutlinedButton**,
  **TextButton**, **IconButton** y **FloatingActionButton**.

## Estilos responsivos con `ResponsiveManager`

Puedes combinar los componentes anteriores con el gestor de estilos
responsivos para adaptar márgenes, tamaños o alineaciones en tiempo
real. El flujo básico es registrar estilos con
:class:`~fletplus.utils.responsive_manager.ResponsiveManager` utilizando
instancias de :class:`~fletplus.utils.responsive_style.ResponsiveStyle`:

> ℹ️ Consulta también la [guía de perfiles de dispositivo y
> breakpoints](responsive.md) para aprender a calcular columnas según el
> ancho disponible o detectar la plataforma activa.

```python
import flet as ft
from fletplus.components import ResponsiveContainer
from fletplus.styles import Style
from fletplus.utils import ResponsiveManager, ResponsiveStyle


def main(page: ft.Page):
    manager = ResponsiveManager(page)

    card = ResponsiveContainer(
        content=ft.Text("Panel adaptable", size=16, weight=ft.FontWeight.BOLD)
    )

    manager.register_styles(
        card,
        ResponsiveStyle(
            width={
                0: Style(padding=20, bgcolor=ft.colors.BLUE_50),
                600: Style(padding=30, bgcolor=ft.colors.BLUE_100),
                1024: Style(padding=40, bgcolor=ft.colors.BLUE_200),
            }
        ),
    )

    page.add(card)


ft.app(target=main)
```

En este ejemplo, `ResponsiveManager` escucha los cambios de tamaño de la
página y reaplica los estilos definidos para cada breakpoint de ancho.
Los valores no especificados conservan el estilo base del control,
permitiendo personalizar únicamente los atributos que necesitas.
