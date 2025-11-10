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

### Preferencias de accesibilidad {#preferencias-accesibilidad}

`fletplus.utils.accessibility.AccessibilityPreferences` encapsula los
ajustes más frecuentes que una persona puede necesitar para navegar una
aplicación con comodidad. Es una `dataclass` pensada para sincronizar el
estado de accesibilidad entre la página (`ft.Page`), los controles
visualizados y el `ThemeManager` activo.

- **Escala de texto (`text_scale`)**: multiplica el tamaño base de las
  tipografías y tooltips. El método `apply()` recalcula un `TextTheme`
  completo garantizando tamaños mínimos de 12 px para evitar texto
  ilegible.
- **Alto contraste (`high_contrast`)**: activa una paleta accesible
  (blanco sobre negro) y resalta los estados de foco con ámbar.
- **Reducción de movimiento (`reduce_motion`)**: deshabilita las
  transiciones de página en todas las plataformas soportadas.
- **Captions (`enable_captions`, `caption_mode`, `caption_duration_ms`)**:
  habilitan subtítulos descriptivos en componentes como
  `CaptionOverlay`. También ajustan la duración visible de tooltips y
  captions.
- **Otros campos**: `tooltip_wait_ms` controla la latencia antes de
  mostrar un tooltip y `locale` permite aplicar una localización
  específica a la página antes de actualizar el tema.

Para aplicar las preferencias llama a
`AccessibilityPreferences.apply(page, theme_manager)`. El método acepta
un `ThemeManager` opcional: cuando se proporciona actualiza los tokens
`typography` y `accessibility`, y finalmente invoca
`theme_manager.apply_theme()` para propagar los cambios a la interfaz.
Si no trabajas con `ThemeManager`, basta con pasar únicamente la página:

```python
prefs = AccessibilityPreferences(text_scale=1.2, high_contrast=True)
prefs.apply(page)  # Modifica page.theme y llama a page.update()
```

### Ejemplo combinado con panel accesible

El siguiente fragmento muestra cómo inicializar un `ThemeManager`,
sincronizar las preferencias y reutilizarlas tanto en un
`AccessibilityPanel` como en un `UniversalAdaptiveScaffold`:

```python
import flet as ft
from fletplus.components import (
    AccessibilityPanel,
    AdaptiveNavigationItem,
    UniversalAdaptiveScaffold,
)
from fletplus.themes import ThemeManager
from fletplus.utils.accessibility import AccessibilityPreferences


def main(page: ft.Page) -> None:
    theme = ThemeManager(page)
    prefs = AccessibilityPreferences(
        text_scale=1.3,
        high_contrast=page.platform == "windows",
        reduce_motion=True,
        enable_captions=True,
        caption_mode="overlay",
    )

    # Aplica la configuración inicial sobre la página y el tema activo.
    prefs.apply(page, theme)

    scaffold = UniversalAdaptiveScaffold(
        navigation_items=[
            AdaptiveNavigationItem("home", "Inicio", ft.Icons.HOME_OUTLINED),
            AdaptiveNavigationItem("reports", "Reportes", ft.Icons.INSIGHTS_OUTLINED),
            AdaptiveNavigationItem("settings", "Ajustes", ft.Icons.SETTINGS_OUTLINED),
        ],
        content_builder=lambda item, _: ft.Text(f"Vista: {item.label}"),
        theme=theme,
        accessibility=prefs,
        accessibility_panel=AccessibilityPanel(
            preferences=prefs,
            theme=theme,
        ),
        page_title="Panel adaptable e inclusivo",
    )

    page.add(scaffold.build(page))


ft.app(target=main)
```

Gracias a que `AccessibilityPreferences` comparte instancia con el
panel, cualquier ajuste del usuario (por ejemplo aumentar la escala de
texto) se refleja automáticamente en la página y en el tema.

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
