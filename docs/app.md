# FletPlusApp en detalle

`FletPlusApp` centraliza la navegación, la gestión de temas, los atajos de teclado y la paleta de comandos sobre una página de Flet. Esta guía repasa el flujo interno tomando como referencia la Core legacy (`fletplus/core_legacy.py`) y muestra cómo sacarle partido en proyectos reales.

> ℹ️ La nueva Core desacoplada vive en el paquete `fletplus/core/`. Para nuevas integraciones, utiliza `fletplus.core`.

## Inicialización básica

```python
import flet as ft
from fletplus.core_legacy import FletPlusApp
from fletplus.router import Route


def main(page: ft.Page):
    app = FletPlusApp(
        page,
        routes=[
            Route(path="/", name="home", view=lambda match: ft.Text("Inicio")),
            Route(path="/settings", name="settings", view=lambda match: ft.Text("Ajustes")),
        ],
        sidebar_items=[{"title": "Inicio", "icon": ft.Icons.HOME}],
        title="Panel FletPlus",
        commands={"Abrir ajustes": lambda: app.router.go("/settings")},
    )

    app.build()


ft.app(target=main)
```

Durante la construcción, la clase:

- Normaliza la lista de rutas y la transforma en un `Router` interno (`_build_router`).
- Genera entradas para la barra lateral a partir de `sidebar_items` o de los metadatos de las rutas (`name`, `path`).
- Detecta la plataforma (móvil, web o escritorio) para aplicar tokens de tema específicos.
- Registra atajos (`Ctrl/Cmd + K`) para abrir la paleta de comandos y prepara gestores auxiliares (animaciones, preferencias, ventanas, etc.).

> ℹ️ Cuando proporcionas un `Store` personalizado (`state=`) la instancia se asigna a `page.state` y queda disponible desde cualquier control.

## Router integrado y observadores

`FletPlusApp` delega la navegación en `fletplus.router.Router`. Tras crear el router, se suscribe a `Router.observe` para reaccionar a cada coincidencia y renderizar la vista activa dentro de `content_container`.

```python
self._router_unsubscribe = self.router.observe(self._handle_route_change)
```

El método `_handle_route_change` recibe el `RouteMatch` final y el control raíz generado por el router. Desde ahí se actualiza el contenedor principal y se sincroniza la navegación seleccionada en la barra lateral o la navegación inferior.

Consulta la [guía del router](router.md) para conocer cómo definir rutas hijas, parámetros dinámicos y layouts persistentes que `FletPlusApp` respetará automáticamente.

## Navegación adaptable

El atributo `responsive_navigation` acepta una instancia de `ResponsiveNavigationConfig` (o usa los valores por defecto). Esta configuración decide qué variante de menú mostrar según el ancho de la ventana:

- **Mobile (`<720px`)**: se activa `NavigationBar` inferior o el menú flotante cuando `floating_breakpoint` lo permite.
- **Tablet (`<1100px`)**: se utiliza un `NavigationRail` o un panel compacto.
- **Desktop**: la barra lateral completa (`SidebarAdmin`) permanece anclada a la izquierda.

Internamente, `ResponsiveManager` observa los cambios de tamaño y pide a `_layout_for_mode` reconstruir los contenedores pertinentes. Los íconos y títulos provienen de `_nav_routes`, generada durante la inicialización.

Para conocer los rangos exactos de `DEFAULT_DEVICE_PROFILES`, extenderlos con `EXTENDED_DEVICE_PROFILES` o detectar la plataforma mediante `is_mobile`/`is_desktop`, revisa la [guía de perfiles de dispositivo y breakpoints](responsive.md).

## Gestor de temas y preferencias

`FletPlusApp` crea un `ThemeManager` con la configuración proporcionada (`theme_config`). Al detectar la plataforma activa fusiona tokens específicos (por ejemplo `mobile_tokens`) en el diccionario base y expone las señales:

- `theme_mode_signal`
- `theme_tokens_signal`
- `theme_overrides_signal`

Además, se registran observadores sobre `PreferenceStorage` para restaurar el modo (claro/oscuro) y persistir cambios. Si tu aplicación añade un selector de tema personalizado, puedes escribir directamente sobre `self.theme_mode_signal.set(...)` o utilizar el contexto `theme_context` documentado más abajo.

> 💡 Para combinar el gestor de temas con escalado de texto, alto contraste o reducción de movimiento revisa la sección de [Preferencias de accesibilidad](components.md#preferencias-accesibilidad). Allí encontrarás cómo sincronizar `AccessibilityPreferences` con `ThemeManager` y `ft.Page`.

## Paleta de comandos y atajos

La paleta (`CommandPalette`) recibe un mapeo sencillo `dict[str, Callable]` al inicializar `FletPlusApp`. Cada clave del diccionario se muestra como etiqueta en la lista y su valor debe ser una función sin argumentos que se ejecutará cuando la persona usuaria seleccione el comando. No se admiten objetos con atributos extra; basta con la pareja `texto -> callable`.

```python
import flet as ft
from fletplus.core_legacy import FletPlusApp
from fletplus.router import Route


def main(page: ft.Page):
    commands = {
        "Abrir ajustes": lambda: page.go("/settings"),
        "Refrescar datos": lambda: page.pubsub.send_all("reload"),
    }

    app = FletPlusApp(
        page,
        routes=[Route(path="/", name="home", view=lambda match: ft.Text("Inicio"))],
        commands=commands,
    )

    app.build()


ft.app(target=main)
```

La clase registra el atajo `Ctrl/Cmd + K` mediante `ShortcutManager`:

```python
self.shortcuts.register("k", lambda: self.command_palette.open(self.page), ctrl=True)
```

Si necesitas otros atajos debes gestionarlos manualmente con `ShortcutManager`. Puedes reutilizar las mismas funciones definidas en `commands`. Por ejemplo, dentro de `main` tras construir la aplicación:

```python
    app.shortcuts.register(
        "r",
        commands["Refrescar datos"],
        ctrl=True,
    )
```

La paleta también se integra con la navegación: cualquier comando puede llamar a `app.router.go(...)` para cambiar de vista.

## Integración con animaciones y layouts reactivos

`FletPlusApp` crea un `AnimationController` compartido (`self.animation_controller`) y lo expone a través de un contexto llamado `animation`. Esto permite coordinar transiciones o efectos desde diferentes componentes sin pasar la referencia explícitamente.

Cuando utilizas decoradores como `@reactive` (sección de hooks), puedes recuperar esta instancia con `animation_controller_context.get()` siempre que la vista actual se haya montado dentro de `FletPlusApp`.
Revisa la guía [Animaciones coordinadas](animation.md) para ver ejemplos completos de los envoltorios disponibles y cómo disparar eventos personalizados.

## Contexto global y proveedores {#contexto-global}

El paquete `fletplus.context` define un sistema jerárquico de contextos basado en `contextvars`. `FletPlusApp` registra automáticamente proveedores para los contextos principales (consulta la [guía completa de contextos](context.md) para un repaso paso a paso):

- `theme_context`
- `user_context`
- `locale_context`
- `animation_controller_context`

Cada proveedor se activa en `_activate_contexts()`, de manera que cualquier control renderizado dentro de la aplicación puede hacer:

```python
from fletplus.context import theme_context

current_theme = theme_context.get()
```

### Creación manual de proveedores

`Context` funciona como *singleton* por nombre. Puedes declarar nuevos contextos o sustituir el valor temporalmente:

```python
from fletplus.context import Context

request_context = Context("request_id", default=None)


with request_context.provide("abc-123"):
    # Dentro del bloque, request_context.get() devuelve "abc-123"
    ...
```

Los proveedores actúan como gestores de contexto y exponen métodos para leer/escribir el valor actual (`provider.value`). También puedes suscribirte a cambios (`provider.subscribe(callback)`) o enlazarlos con controles Flet (`provider.bind_control(control, attr="value")`).

Para ver ejemplos completos de cómo `FletPlusApp` configura estos proveedores, revisa `_activate_contexts()` en `fletplus/core_legacy.py`.

## Hooks reactivos en vistas {#hooks-reactivos}

El módulo `fletplus.state.hooks` ofrece utilidades estilo React que se integran con el ciclo de vida de `FletPlusApp`:

- `@reactive`: decora un método `build` (o cualquier función de render). Mantiene señales memorables por instancia y vuelve a invocar `update()` cuando cambian.
- `use_state(initial)`: crea una `Signal` local asociada a la posición del hook.
- `use_signal(signal)`: registra señales externas como dependencias.
- `watch(signals, callback, immediate=True)`: ejecuta un callback cuando una o varias señales emiten nuevos valores.

```python
import flet as ft
from fletplus.state import reactive, use_state, use_signal, watch


class DashboardCard(ft.UserControl):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.total = ft.Text()

    @reactive
    def build(self):
        local = use_state(0)
        global_counter = use_signal(self.store.bind("count"))

        local.bind_control(self.total, attr="value", transform=lambda v: f"Total local: {v}")

        if not hasattr(self, "_subscriptions"):
            self._subscriptions = True
            watch(global_counter, lambda value: self.page.snack_bar.open = True)
            watch((local, global_counter), lambda local_value, global_value: print(local_value + global_value))

        return ft.Column(
            controls=[
                ft.TextButton("Sumar", on_click=lambda _: local.set(local.get() + 1)),
                ft.TextButton("Incrementar global", on_click=lambda _: self.store.update("count", lambda v: v + 1)),
            ]
        )
```

> 💡 Los hooks solo pueden llamarse dentro de un render decorado con `@reactive`. Si lo olvidas, `_current_context(required=True)` lanzará un error explicativo.

La instancia de `FletPlusApp` mantiene un registro de los renders reactivos (`self._register_reactive_render`) para limpiar suscripciones cuando la vista cambia. Así evitas fugas de memoria y callbacks huérfanos.

## Recursos adicionales

- [Router declarativo y layouts persistentes](router.md)
- [Proveedores de almacenamiento reactivo](storage.md)
- [Guía de hooks y estado](index.md#gestion-de-estado-reactivo)

Si buscas cómo combinar contextos y hooks con almacenamiento persistente, revisa la sección correspondiente en [Almacenamiento reactivo](storage.md#recursos-relacionados).
