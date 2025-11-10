# Proveedores de almacenamiento reactivo

Esta guía explica cómo funciona la interfaz `StorageProvider` de FletPlus y cómo aprovechar
sus señales para sincronizar datos persistentes con los controles de Flet. También se
incluyen detalles de las implementaciones listas para usar y recomendaciones de uso
según el tipo de persistencia que necesites.

## Interfaz `StorageProvider`

`StorageProvider` ofrece una capa unificada sobre diferentes backends de almacenamiento
(almacenamiento local, almacenamiento de sesión o archivos JSON) y expone una API
enfocada en mantener la UI sincronizada. Todos los proveedores comparten estas
capacidades:

- Serialización configurable mediante los argumentos `serializer` y `deserializer` del
  constructor.
- Emisión de señales de `fletplus.state.Signal` cada vez que cambia una clave o el
  snapshot global del almacenamiento.
- Operaciones básicas para manipular claves (`set`, `get`, `remove`, `clear`) y
  utilidades de suscripción o enlace con controles de Flet (`bind_control`).

### Señales reactivas

Los proveedores generan dos tipos de señales para observar cambios en los datos:

- `signal(key, default=MISSING)`: crea (o reutiliza) una señal asociada a una clave.
  Puedes suscribirte manualmente con `subscribe()` o invocar `bind_control()` para que
  un control actualice automáticamente un atributo cuando el valor cambie. El argumento
  `default` permite establecer un valor inicial cuando la clave aún no existe.
- `snapshot_signal()`: devuelve una señal que expone una vista inmutable (`Mapping`) con
  todas las claves conocidas. Es útil cuando necesitas reaccionar ante cualquier cambio
  del almacenamiento completo y no solo de una clave concreta.

Internamente, cada operación que modifica el backend invoca `_refresh_snapshot()` para
que la señal global emita un nuevo snapshot.

### Métodos fundamentales

Todos los proveedores comparten la misma semántica para los métodos principales:

| Método | Descripción |
| --- | --- |
| `get(key, default=None)` | Recupera el valor de una clave aplicando `deserializer`. Si la clave no existe retorna `default`. |
| `set(key, value)` | Persiste el valor (tras pasar por `serializer`) y emite la señal asociada a `key`, además de refrescar el snapshot global. |
| `remove(key)` | Elimina la clave; si había una señal asociada, la restablece a su valor por defecto y actualiza el snapshot. |
| `clear()` | Limpia todas las claves disponibles, emitiendo actualizaciones para cada señal registrada y regenerando el snapshot. |

Además, dispones de helpers como `subscribe(key, callback)` para recibir notificaciones
imperativas y `bind_control(key, control, attr="value")` para conectar una clave con un
atributo de un control Flet.

## Implementaciones incluidas

### `LocalStorageProvider`

- **Requisitos**: instancia de `flet.Page` o de `flet.core.client_storage.ClientStorage`.
- **Uso recomendado**: persistir datos en el almacenamiento local del navegador
  (sobrevive a recargas y cierres de pestaña mientras no se limpien los datos del sitio).
- **Inicialización rápida**:

  ```python
  import flet as ft
  from fletplus.storage.local import LocalStorageProvider

  def main(page: ft.Page):
      storage = LocalStorageProvider.from_page(page)
      counter = storage.signal("counter", default=0)

      label = ft.Text()
      counter.bind_control(label, attr="value", transform=lambda v: f"Clicks: {v}")

      def increment(_):
          storage.set("counter", counter.get() + 1)

      page.add(label, ft.ElevatedButton("Sumar", on_click=increment))

  ft.app(target=main)
  ```

  Con este patrón, el valor se conserva entre sesiones del navegador y el texto se
  actualiza automáticamente.

### `SessionStorageProvider`

- **Requisitos**: instancia de `flet.Page` o de `flet.core.session_storage.SessionStorage`.
- **Uso recomendado**: almacenar información temporal por sesión de navegador. El
  contenido se descarta cuando la pestaña o ventana se cierra.
- **Ejemplo de uso**:

  ```python
  import flet as ft
  from fletplus.storage.session import SessionStorageProvider

  def main(page: ft.Page):
      storage = SessionStorageProvider.from_page(page)
      theme_pref = storage.signal("theme", default="light")

      dropdown = ft.Dropdown(
          options=[ft.dropdown.Option("light"), ft.dropdown.Option("dark")],
          on_change=lambda e: storage.set("theme", e.control.value),
      )
      theme_pref.bind_control(dropdown, attr="value")

      page.add(ft.Text("Tema preferido (solo sesión actual):"), dropdown)

  ft.app(target=main)
  ```

  Este proveedor resulta práctico para mantener selecciones temporales mientras el
  usuario navega por la misma sesión.

### `FileStorageProvider`

- **Requisitos**: ruta accesible en disco (como `Path` o `str`). Se crea el directorio
  automáticamente si no existe. Utiliza JSON por defecto (`json.dumps/json.loads`).
- **Uso recomendado**: persistencia en escritorio o backend cuando necesitas compartir
  datos entre ejecuciones de la app.
- **Ejemplo integrando controles**:

  ```python
  from pathlib import Path

  import flet as ft
  from fletplus.storage.files import FileStorageProvider

  def main(page: ft.Page):
      storage = FileStorageProvider(Path.home() / ".my_app" / "settings.json")
      username = storage.signal("username", default="")

      textfield = ft.TextField(label="Nombre de usuario")
      username.bind_control(textfield, attr="value")

      def save(_):
          storage.set("username", textfield.value)

      page.add(textfield, ft.ElevatedButton("Guardar", on_click=save))

  ft.app(target=main)
  ```

  Cada vez que se pulsa el botón, el archivo JSON se sincroniza y los controles
  reciben los nuevos valores.

## Comparativa de escenarios

| Proveedor | Persistencia | Contexto ideal | Consideraciones |
| --- | --- | --- | --- |
| `LocalStorageProvider` | Almacenamiento local del navegador (permanente hasta limpiar datos) | Preferencias de usuario, contadores o flags que deben sobrevivir a recargas | Disponible solo cuando la app corre en un navegador con `client_storage` habilitado. |
| `SessionStorageProvider` | Almacenamiento de sesión del navegador | Estados temporales, wizards o filtros que deben resetearse al cerrar la pestaña | Los datos desaparecen al cerrar la pestaña o expirar la sesión. |
| `FileStorageProvider` | Archivo JSON en disco | Aplicaciones de escritorio o backend que requieren persistencia estable entre ejecuciones | Asegúrate de gestionar rutas accesibles y permisos de escritura/lectura. |

## Recursos relacionados

- Consulta la sección "Gestión de estado reactivo" en la portada para combinar
  las señales de almacenamiento con `Store` y `Signal`.
- Explora los ejemplos de `fletplus.state` en la demo para ver cómo los controles se
  enlazan mediante `Signal.bind_control`.
- Si tu app se construye con `FletPlusApp`, revisa [Arquitectura de FletPlusApp](app.md#hooks-reactivos) para integrar las señales con hooks reactivos y contextos compartidos.

