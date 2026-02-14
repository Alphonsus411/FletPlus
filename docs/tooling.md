# Herramientas de desarrollo y publicación

Esta guía reúne los apoyos disponibles durante el ciclo de vida de una app FletPlus: desde las utilidades de depuración, pasando por la recarga en caliente de la CLI y los gestores de escritorio, hasta la automatización de despliegue de la documentación.

## QA y políticas de seguridad en CI

La definición base de QA está centralizada en `.github/workflows/reusable-quality.yml` (workflow reusable con `workflow_call`).

- `.github/workflows/qa.yml` es el **wrapper** para eventos `pull_request`.
- `.github/workflows/quality.yml` es el **wrapper** para eventos `push`.

Ambos wrappers delegan en el reusable para evitar duplicación y mantener en un solo lugar la matriz de Python (`3.9`, `3.10`, `3.11`) y todos los comandos de validación.

El preflight soporta selección explícita por suite con `--suite`:

- `--suite default`: validación mínima (sin dependencias opcionales).
- `--suite cli`: valida dependencias de CLI (incluye `watchdog`).
- `--suite websocket`: valida dependencias de WebSocket (incluye `websockets`).
- `--suite perf`: validación específica para benchmarks de rendimiento.

Se pueden combinar suites repitiendo la bandera (por ejemplo, `--suite unit --suite cli --suite websocket`).

Orden real de QA (idéntico en shell, reusable workflow y nox):

1. `python tools/check_test_dependencies.py --suite unit --suite cli --suite websocket`
2. `python -m pytest`
3. `python -m ruff check .`
4. `python -m black --check .`
5. `python -m mypy fletplus`
6. `python tools/check_bandit_command_sync.py`
7. `python -m bandit -c pyproject.toml -r fletplus`
8. `python -m pip_audit -r requirements.txt -r requirements-dev.txt --policy pip-audit.policy.json`
9. `python -m safety check -r requirements.txt -r requirements-dev.txt --policy-file safety-policy.yml`

Si se necesita exceptuar una vulnerabilidad de forma temporal, debe documentarse en los archivos de política correspondientes (`pip-audit.policy.json` y `safety-policy.yml`) con justificación y fecha de expiración.

> ⚠️ **Mantenimiento CI**: cualquier cambio de pasos, versiones de Python o herramientas de QA debe hacerse en `.github/workflows/reusable-quality.yml`. Los workflows `qa.yml` y `quality.yml` deben mantenerse como wrappers mínimos sin lógica duplicada.

## Estrategia de tests: suite rápida vs benchmarks

La configuración base de `pytest` en este repositorio define `addopts = -m "not perf"`, por lo que la ejecución estándar excluye benchmarks y prioriza feedback rápido en desarrollo y CI principal:

```bash
python -m pytest
```

Los benchmarks viven bajo `tests/perf/` y se ejecutan de forma explícita con el marker `perf`:

```bash
python -m pytest -m perf
```

Para automatización, el workflow dedicado `.github/workflows/perf.yml` separa estas mediciones del flujo de QA/Quality y permite lanzarlas en horario nocturno o manualmente cuando se requiera comparar rendimiento entre cambios.

## Política de stubs en tests

Para evitar falsos positivos en imports, los dobles globales ya no se aplican de forma automática en toda la suite.

- Usa fixtures **opt-in** cuando el objetivo sea un test unitario aislado:
  - `use_state_stub`
  - `use_responsive_manager_stub`
- Aplica esos stubs solo en el test (o módulo) que realmente necesite desacoplarse de implementaciones reales.
- Para pruebas de contrato de import público o fallbacks de backend, **no uses stubs**: valida el import real y, si aplica, fuerza fallos controlados con `monkeypatch`.

Archivos de referencia en esta política:

- `tests/test_unit_stub_fixtures.py`: ejemplos de uso explícito de stubs.
- `tests/test_optional_backend_import_fallbacks.py`: integración de imports reales + fallback controlado.
- `tests/test_public_api_entrypoints.py`: contrato de entrypoints públicos con módulos reales.

## DevTools integrados

`DevToolsServer` expone un servidor WebSocket ligero que reenvía mensajes entre clientes conectados. Cada vez que un cliente envía un *frame*, el servidor lo redistribuye al resto y guarda instantáneas iniciales (payloads con tipo `snapshot`) para nuevos suscriptores. De esta manera puedes abrir la vista de DevTools en múltiples navegadores y mantenerlos sincronizados mientras inspeccionas el estado de la app (implementación en `fletplus/devtools/server.py`).

Para integrarlo en tu proyecto, arranca `DevToolsServer().listen()` dentro de un `asyncio.Task` y comparte la URL en tus herramientas de depuración o paneles administrativos.

Si necesitas restringir el acceso, puedes configurar `auth_token` y/o `allowed_origins`. Con `auth_token`, el cliente debe enviar el secreto en un header dedicado (`Authorization: Bearer <token>` o `X-DevTools-Token: <token>`). La query string `?token=...` sigue disponible solo como fallback temporal deprecado y emite un warning en logs. Además, el header `Origin` debe coincidir con alguno de los orígenes permitidos cuando se configure `allowed_origins`. Las conexiones que no cumplan estos requisitos se rechazan con un cierre de política.

## Recarga en caliente desde la CLI

El comando `fletplus run` monitoriza el árbol del proyecto (ignorando carpetas temporales como `.git`, `__pycache__` o `build`) mediante `watchdog`. Cuando detecta cambios en archivos Python, JSON o YAML, detiene el proceso actual de `flet run` y lo reinicia, conservando las opciones de puerto y activando los DevTools salvo que se haya pasado `--no-devtools`. También admite seleccionar el archivo principal con `--app` y la carpeta a vigilar con `--watch`.

## Perfilado previo a releases

Para decidir qué módulos compilar con Cython antes de publicar una nueva versión:

> Requisito previo: instala el extra de build (`pip install .[build]`), que aporta `python -m build` y `cython` en el entorno local.

1. Genera el perfil con cProfile y guarda el resultado en `build/profile.txt`:

   ```bash
   fletplus profile --output build/profile.txt --sort cumtime --limit 30
   ```

   Si tu entorno no tiene registrado el alias, ejecuta `make profile`, que usa cProfile sobre el árbol `fletplus` y deja el archivo en la misma ruta.

2. Actualiza la lista de módulos a compilar con Cython leyendo el perfil anterior:

   ```bash
   python tools/select_cython_modules.py --profile build/profile.txt --config build_config.yaml --limit 4
   ```

   El script ordena los archivos del repositorio por tiempo acumulado en el perfil y rellena `build_config.yaml` con los módulos más costosos. Si el perfil no contiene datos del proyecto, recurre al listado por defecto definido en `tools/select_cython_modules.py`.

3. Construye las extensiones C justo después de actualizar la configuración. El `Makefile` ya encadena este flujo al objetivo `build`:

   ```bash
   make build
   ```

   Este objetivo regenera `build_config.yaml` y luego compila extensiones en local, de modo que la selección de módulos queda alineada con el último perfil.

> ✅ Ejecuta los pasos 1 y 2 antes de cortar cada release. Así nos aseguramos de que los módulos más calientes queden reflejados en `build_config.yaml` y entren en el flujo de compilación local con Cython cuando corresponda.

## Gestores de escritorio

### Ventanas adicionales

`WindowManager` mantiene un registro de páginas abiertas y permite alternar el foco entre ellas. La instancia principal se guarda bajo la clave `"main"`; al crear una nueva ventana basta con llamar a `open_window` con un nombre identificador. Si la página expone `window_to_front`, el gestor la llama automáticamente al recuperar el foco con `focus_window` para asegurar que quede visible.

### Bandeja del sistema

`SystemTray` ofrece una envoltura mínima sobre el icono de bandeja, manteniendo su visibilidad y un manejador de clic configurable a través de `on_click`. Puedes mostrar u ocultar el icono con `show()`/`hide()` y simular eventos durante pruebas con `_emit_click`. Es útil para exponer accesos rápidos a estados de la app cuando se minimiza a la bandeja.

### Notificaciones

`fletplus.desktop.show_notification` ya incluye backends nativos:

- **Windows** (`_notify_windows`): intenta `win10toast` si está instalado; si no, lanza un script de PowerShell usando `powershell`/`pwsh` para publicar el toast.
- **macOS** (`_notify_macos`): prefiere `pync` y, en su ausencia, recurre a `osascript` con el comando `display notification`.
- **Linux** (`_notify_linux`): usa `gi.repository.Notify` (requiere PyGObject). Si no está disponible, busca el binario `notify-send` y lo ejecuta.

Cuando ningún backend confirma la entrega o hay una excepción, el helper usa `_notify_in_page` como *fallback* y escribe `"Notificación: <titulo> - <cuerpo>"` en la salida estándar. Si quieres mostrar un `SnackBar` o un `Banner` en la propia app, sobrescribe `_notify_in_page` antes de llamar a `show_notification` o envuelve el helper con tu propio control para desactivar el fallback.

## Gestor de drop de archivos

`FileDropZone` encapsula las comprobaciones necesarias para aceptar archivos arrastrados desde el sistema operativo. Cada entrada se normaliza con `Path.resolve(strict=True)` y se descarta cualquier ruta que no exista, apunte a directorios o atraviese enlaces simbólicos en su camino.

- **Sanitización de rutas**: al establecer `base_directory`, la ruta resultante debe pertenecer a dicho directorio (se usa `Path.relative_to`). Esto evita que un usuario entregue ficheros fuera del sandbox configurado, incluso si intenta usar `..` o enlaces simbólicos.
- **Filtros por extensión y tamaño**: `allowed_extensions` acepta colecciones con o sin punto (`{"jpg", ".png"}`) y se evalúan en minúsculas. `max_size` recibe un entero en bytes y se contrasta usando `os.path.getsize`; si falla la lectura o el archivo excede el límite, el elemento se ignora.
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

`PreferenceStorage` determina el backend disponible en tiempo de ejecución: si la página cuenta con `client_storage` (p. ej. aplicaciones empaquetadas con Flet), se guarda bajo una clave JSON; de lo contrario utiliza un archivo local configurable vía `FLETPLUS_PREFS_FILE`. Los métodos `load()` y `save()` devuelven/reciben diccionarios con los valores a persistir.

`FletPlusApp` crea automáticamente una instancia de `PreferenceStorage` y observa los cambios de `ThemeManager`. Al iniciar la app se restauran el modo claro/oscuro y los *tokens* guardados; cada vez que el usuario cambia el tema, los nuevos valores se escriben otra vez en el almacenamiento elegido. Así garantizas que la preferencia visual permanece entre sesiones sin código adicional (Core legacy en `fletplus/core_legacy.py`).

> 🧭 Si también deseas persistir preferencias de accesibilidad (escala de texto, contraste, movimiento), consulta cómo reutilizar `AccessibilityPreferences` junto al `ThemeManager` en [la guía de componentes](components.md#preferencias-accesibilidad).

## Soporte PWA

El módulo `fletplus.web.pwa` incluye tres utilidades clave:

- `generate_service_worker(static_files, output_dir)` crea un `service_worker.js` con una caché estática (`STATIC_ASSETS`) e instala controladores `install` y `fetch` para responder con recursos cacheados cuando sea posible.
- `generate_manifest(name, icons, start_url, output_dir)` genera un `manifest.json` con nombre, URL inicial y lista de iconos.
- `register_pwa(page, manifest_url, service_worker_url)` añade la etiqueta `<link rel="manifest">` al `<head>` de la página y registra el *service worker* asegurándose de que las rutas sean del mismo origen.

Una vez generados ambos archivos, sirve el directorio que los contiene y llama a `register_pwa(page)` durante la inicialización de tu app web para activar la experiencia instalable.

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

> ✅ Recuerda habilitar GitHub Pages la primera vez desde **Settings → Pages** seleccionando “GitHub Actions” como fuente. Después de ese paso manual, cada `push` sobre `main` publicará la nueva versión de la documentación sin intervención adicional.

Para mantener la compatibilidad de enlaces entre el `README.md` en GitHub y el `index.md` de MkDocs (que incluye ese README), sigue también la guía breve de [estilo de enlaces](link-style.md).
