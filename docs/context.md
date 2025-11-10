# Contextos y proveedores en FletPlus

Esta guía repasa el sistema `fletplus.context`, cómo utilizar `Context` y `ContextProvider` para compartir estado y de qué manera integrarlos con las señales reactivas del paquete.

## Conceptos fundamentales

1. **Context**: representa un canal nombrado. Su valor depende del proveedor activo más cercano en la jerarquía de ejecución.
2. **ContextProvider**: gestiona el valor concreto dentro de un bloque (`with`) o durante la vida útil de un componente.
3. **contextvars**: la implementación interna que evita interferencias entre hilos o *coroutines* y mantiene el aislamiento por petición.

Cuando creas un `Context`, puedes establecer un valor por defecto y una función comparadora opcional para controlar cuándo deben propagarse cambios.

```python
from fletplus.context import Context

# Se reutiliza la misma instancia si se vuelve a declarar con el mismo nombre
locale_context = Context("locale", default="es-ES")
```

## Flujo básico paso a paso

1. **Declarar el contexto** (`Context("nombre")`).
2. **Abrir un proveedor** ya sea con `with Context("nombre") as provider:` o llamando a `context.provide(...)` para crear un `ContextProvider` explícito.
3. **Leer el valor** desde cualquier punto anidado con `context.get()`.
4. **Actualizar el valor** usando `context.set(nuevo_valor)` o `provider.set(...)`.
5. **Cerrar el proveedor** automáticamente al salir del bloque `with` o manualmente invocando `provider.close()`.

```python
from fletplus.context import Context

request_context = Context("request_id", default=None)

with request_context as provider:
    provider.set("abc-123")
    assert request_context.get() == "abc-123"

assert request_context.get() is None  # vuelve al valor por defecto
```

> ℹ️ Si llamas a `Context("request_id")` varias veces, siempre recibirás la misma instancia registrada originalmente.

## Control preciso con `ContextProvider`

En lugar de usar el gestor automático (`with context:`), puedes crear un proveedor explícito para inyectar un valor inicial, decidir si hereda del padre o integrarlo con el ciclo de vida de un control.

```python
from fletplus.context import Context

permissions_context = Context("permissions", default=set())

def build_view():
    provider = permissions_context.provide({"dashboard.view"})
    provider.__enter__()
    try:
        render_dashboard()
    finally:
        provider.close()
```

Parámetros clave:

- `value`: valor inicial del proveedor. Si no se indica y existe un proveedor padre, se hereda automáticamente (`inherit=True`).
- `inherit`: desactívalo para iniciar siempre con el valor por defecto del contexto.

## Encadenar proveedores personalizados

Puedes encapsular la lógica de apertura y cierre en funciones auxiliares o decoradores. Esto resulta útil para registrar contextos específicos de una vista, una petición HTTP o un flujo de autenticación.

```python
from contextlib import contextmanager
from fletplus.context import Context

user_context = Context("user", default=None)

@contextmanager
def provide_user(user):
    provider = user_context.provide(user)
    provider.__enter__()
    try:
        yield provider
    finally:
        provider.close()
```

El uso queda reducido a:

```python
with provide_user({"id": 1, "name": "Ada"}):
    load_personalized_dashboard()
```

## Integración con señales reactivas

Internamente, cada `ContextProvider` crea una `Signal` que notifica cambios a los suscriptores. Puedes aprovecharlo directamente de varias maneras:

- **Suscribirse a cambios**:

  ```python
  def on_locale_change(new_locale):
      print("Nuevo locale", new_locale)

  unsubscribe = locale_context.subscribe(on_locale_change, immediate=True)
  # Llama a on_locale_change con el valor actual y cada vez que cambie
  ```

- **Vincular controles de Flet** mediante `bind_control`, ideal para reflejar cambios en tiempo real en etiquetas, *switches* o campos de entrada.

  ```python
  from fletplus.context import theme_context
  import flet as ft

  theme_label = ft.Text()
  theme_context.bind_control(theme_label, attr="value", transform=lambda mode: f"Tema activo: {mode}")
  ```

- **Sincronizar con otras señales**: si necesitas integrar el contexto con utilidades como `use_signal`, crea una `Signal` puente que se actualice cada vez que cambie el contexto.

  ```python
  from fletplus.context import Context
  from fletplus.state import Signal

  session_context = Context("session", default=None)

  bridge = Signal(session_context.get())

  unsubscribe = session_context.subscribe(bridge.set, immediate=True)
  # Ahora puedes pasar `bridge` a `use_signal` o combinarla con otras señales
  ```

> ✅ Consejo: cuando trabajes con vistas decoradas con `@reactive`, crea la señal puente dentro de `__init__` o en un módulo compartido y suscríbete en `did_mount` para mantener el render sincronizado.

## Contextos automáticos de `FletPlusApp`

`FletPlusApp` activa proveedores para `theme_context`, `user_context`, `locale_context` y `animation_controller_context`. Esto significa que dentro de cualquier vista renderizada por la aplicación puedes acceder directamente al estado global:

```python
from fletplus.context import theme_context

current_tokens = theme_context.get()
```

Si necesitas añadir tus propios contextos globales, sobrescribe `_activate_contexts()` o monta tus proveedores antes de llamar a `app.build()`:

```python
from fletplus.context import Context

session_context = Context("session", default=None)

class MyApp(FletPlusApp):
    def _activate_contexts(self):
        super()._activate_contexts()
        session_context.provide({"token": "abc"}).__enter__()
```

Recuerda cerrar cualquier proveedor manual que abras para evitar fugas entre sesiones.

## Buenas prácticas y patrones comunes

- Crea los contextos en módulos de configuración o en la capa de dominio para reutilizarlos en todo el proyecto.
- Evita almacenar objetos no serializables si planeas depurar o registrar el estado; considera usar identificadores simples.
- Anida proveedores cuando necesites scopes temporales (por ejemplo, durante una petición API) y libera el valor en un bloque `finally`.
- Usa `subscribe` con `immediate=True` para inicializar controles con el valor actual sin esperar el primer cambio.
- Documenta los contextos globales disponibles en tu proyecto para que los equipos sepan qué valores pueden consumir.
