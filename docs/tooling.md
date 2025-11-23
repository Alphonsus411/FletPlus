# Herramientas de desarrollo y publicación

Esta guía reúne los apoyos disponibles durante el ciclo de vida de una app FletPlus: desde las utilidades de depuración, pasando por la recarga en caliente de la CLI y los gestores de escritorio, hasta la automatización de despliegue de la documentación.

## DevTools integrados

`DevToolsServer` expone un servidor WebSocket ligero que reenvía mensajes entre clientes conectados. Cada vez que un cliente envía un *frame*, el servidor lo redistribuye al resto y guarda instantáneas iniciales (payloads con tipo `snapshot`) para nuevos suscriptores. De esta manera puedes abrir la vista de DevTools en múltiples navegadores y mantenerlos sincronizados mientras inspeccionas el estado de la app.【F:fletplus/devtools/server.py†L15-L86】

Para integrarlo en tu proyecto, arranca `DevToolsServer().listen()` dentro de un `asyncio.Task` y comparte la URL en tus herramientas de depuración o paneles administrativos.

## Recarga en caliente desde la CLI

El comando `fletplus run` monitoriza el árbol del proyecto (ignorando carpetas temporales como `.git`, `__pycache__` o `build`) mediante `watchdog`. Cuando detecta cambios en archivos Python, JSON o YAML, detiene el proceso actual de `flet run` y lo reinicia, conservando las opciones de puerto y activando los DevTools salvo que se haya pasado `--no-devtools`. También admite seleccionar el archivo principal con `--app` y la carpeta a vigilar con `--watch`.【F:fletplus/cli/main.py†L83-L171】

## Perfilado previo a releases

Para decidir qué módulos compilar con Cython antes de publicar una nueva versión:

1. Genera el perfil con cProfile y guarda el resultado en `build/profile.txt`:

   ```bash
   fletplus profile --output build/profile.txt --sort cumtime --limit 30
   ```

   Si tu entorno no tiene registrado el alias, ejecuta `make profile`, que usa cProfile sobre el árbol `fletplus` y deja el archivo en la misma ruta.【F:Makefile†L5-L15】

2. Actualiza la lista de módulos a compilar con Cython leyendo el perfil anterior:

   ```bash
   python tools/select_cython_modules.py --profile build/profile.txt --config build_config.yaml --limit 4
   ```

   El script ordena los archivos del repositorio por tiempo acumulado en el perfil y rellena `build_config.yaml` con los módulos más costosos. Si el perfil no contiene datos del proyecto, recurre al listado por defecto usado en `setup.py`.【F:tools/select_cython_modules.py†L1-L95】

3. Construye las extensiones C justo después de actualizar la configuración. El `Makefile` ya encadena este flujo al objetivo `build`:

   ```bash
   make build
   ```

   Este objetivo regenera `build_config.yaml` antes de invocar `setup.py`, de modo que la configuración que lee `_load_module_config` siempre está alineada con el último perfil.【F:Makefile†L1-L17】【F:setup.py†L7-L57】

> ✅ Ejecuta los pasos 1 y 2 antes de cortar cada release. Así nos aseguramos de que los módulos más calientes se compilan con Cython y `setup.py` los detecta automáticamente al construir paquetes o instalar en editable.

## Gestores de escritorio

### Ventanas adicionales

`WindowManager` mantiene un registro de páginas abiertas y permite alternar el foco entre ellas. La instancia principal se guarda bajo la clave `"main"`; al crear una nueva ventana basta con llamar a `open_window` con un nombre identificador. Si la página expone `window_to_front`, el gestor la llama automáticamente al recuperar el foco con `focus_window` para asegurar que quede visible.【F:fletplus/desktop/window_manager.py†L1-L38】

### Bandeja del sistema

`SystemTray` ofrece una envoltura mínima sobre el icono de bandeja, manteniendo su visibilidad y un manejador de clic configurable a través de `on_click`. Puedes mostrar u ocultar el icono con `show()`/`hide()` y simular eventos durante pruebas con `_emit_click`. Es útil para exponer accesos rápidos a estados de la app cuando se minimiza a la bandeja.【F:fletplus/desktop/system_tray.py†L1-L25】

### Notificaciones

`fletplus.desktop.show_notification` intenta llamar a un backend nativo según la plataforma (`_notify_windows`, `_notify_macos`, `_notify_linux`). Actualmente estas funciones lanzan `NotImplementedError`, por lo que el soporte real en Windows, macOS y Linux está pendiente de integración.

Mientras llegan esas implementaciones, la función captura los errores y recurre a `_notify_in_page`, un *fallback* que imprime el mensaje en la salida estándar de la sesión de la app. Puedes reemplazarlo por una notificación visual propia (por ejemplo, un `SnackBar` o `Banner`) asignándola cuando detectes que la plataforma aún no dispone de backend.

> 🔧 **Seguimiento**: TODO — Implementar las integraciones nativas de notificaciones para Windows, macOS y Linux en cuanto se asigne el issue correspondiente.

## Gestor de drop de archivos

`FileDropZone` encapsula las comprobaciones necesarias para aceptar archivos arrastrados desde el sistema operativo. Cada entrada se normaliza con `Path.resolve(strict=True)` y se descarta cualquier ruta que no exista, apunte a directorios o atraviese enlaces simbólicos en su camino.【F:fletplus/utils/dragdrop.py†L9-L58】

- **Sanitización de rutas**: al establecer `base_directory`, la ruta resultante debe pertenecer a dicho directorio (se usa `Path.relative_to`). Esto evita que un usuario entregue ficheros fuera del sandbox configurado, incluso si intenta usar `..` o enlaces simbólicos.【F:fletplus/utils/dragdrop.py†L32-L44】
- **Filtros por extensión y tamaño**: `allowed_extensions` acepta colecciones con o sin punto (`{"jpg", ".png"}`) y se evalúan en minúsculas. `max_size` recibe un entero en bytes y se contrasta usando `os.path.getsize`; si falla la lectura o el archivo excede el límite, el elemento se ignora.【F:fletplus/utils/dragdrop.py†L18-L53】
- **Callbacks y señales**: `on_files` se ejecuta cuando al menos un archivo pasa los filtros y recibe la lista final. Puedes enlazarlo con una señal reactiva (`Signal`) para actualizar controles sin lógica adicional o disparar subidas asíncronas.

Ejemplo combinando la señalización de FletPlus y un `ListView` de Flet:

```python
import flet as ft
from fletplus.state import Signal
from fletplus.utils.dragdrop import FileDropZone


def main(page: ft.Page) -> None:
    accepted_files = Signal([])

    drop_zone = FileDropZone(
        allowed_extensions={".png", "jpg"},
        max_size=5 * 1024 * 1024,
        base_directory="/home/usuario/Downloads",
        on_files=accepted_files.set,
    )

    file_list = ft.ListView(expand=True)
    accepted_files.bind_control(
        file_list,
        attr="controls",
        transform=lambda files: [ft.Text(path) for path in files],
    )

    def handle_drop(event: ft.DragTargetEvent) -> None:
        drop_zone.drop(file.path for file in event.files)
        page.update()

    page.on_drop = handle_drop
    page.add(ft.Text("Arrastra tus imágenes"), file_list)


ft.app(target=main)
```

## Preferencias persistentes y temas

`PreferenceStorage` determina el backend disponible en tiempo de ejecución: si la página cuenta con `client_storage` (p. ej. aplicaciones empaquetadas con Flet), se guarda bajo una clave JSON; de lo contrario utiliza un archivo local configurable vía `FLETPLUS_PREFS_FILE`. Los métodos `load()` y `save()` devuelven/reciben diccionarios con los valores a persistir.【F:fletplus/utils/preferences.py†L19-L107】

`FletPlusApp` crea automáticamente una instancia de `PreferenceStorage` y observa los cambios de `ThemeManager`. Al iniciar la app se restauran el modo claro/oscuro y los *tokens* guardados; cada vez que el usuario cambia el tema, los nuevos valores se escriben otra vez en el almacenamiento elegido. Así garantizas que la preferencia visual permanece entre sesiones sin código adicional.【F:fletplus/core.py†L120-L175】

> 🧭 Si también deseas persistir preferencias de accesibilidad (escala de texto, contraste, movimiento), consulta cómo reutilizar `AccessibilityPreferences` junto al `ThemeManager` en [la guía de componentes](components.md#preferencias-accesibilidad).

## Soporte PWA

El módulo `fletplus.web.pwa` incluye tres utilidades clave:

- `generate_service_worker(static_files, output_dir)` crea un `service_worker.js` con una caché estática (`STATIC_ASSETS`) e instala controladores `install` y `fetch` para responder con recursos cacheados cuando sea posible.
- `generate_manifest(name, icons, start_url, output_dir)` genera un `manifest.json` con nombre, URL inicial y lista de iconos.
- `register_pwa(page, manifest_url, service_worker_url)` añade la etiqueta `<link rel="manifest">` al `<head>` de la página y registra el *service worker* asegurándose de que las rutas sean del mismo origen.

Una vez generados ambos archivos, sirve el directorio que los contiene y llama a `register_pwa(page)` durante la inicialización de tu app web para activar la experiencia instalable.【F:fletplus/web/pwa.py†L1-L83】

## Workflow de documentación

El repositorio incluye el workflow `.github/workflows/docs.yml` que publica automáticamente la documentación en GitHub Pages. El job `build` instala Python 3.11, las dependencias de `requirements-docs.txt` y construye el sitio de MkDocs antes de subirlo como artefacto:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements-docs.txt
      - uses: actions/configure-pages@v4
      - run: mkdocs build --strict --site-dir site
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
```

El job `deploy` depende del artefacto previo y ejecuta `actions/deploy-pages@v4`, exponiendo la URL final a través de la salida `page_url`:

```yaml
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - id: deploy
        uses: actions/deploy-pages@v4
```

> ✅ Recuerda habilitar GitHub Pages la primera vez desde **Settings → Pages** seleccionando “GitHub Actions” como fuente. Después de ese paso manual, cada `push` sobre `main` publicará la nueva versión de la documentación sin intervención adicional.【F:.github/workflows/docs.yml†L1-L43】
