# Herramientas de desarrollo y publicación

Esta guía reúne los apoyos disponibles durante el ciclo de vida de una app FletPlus: desde las utilidades de depuración, pasando por la recarga en caliente de la CLI y los gestores de escritorio, hasta la automatización de despliegue de la documentación.

## QA y políticas de seguridad en CI

La fuente única de verdad de QA está centralizada en `tools/qa.sh`. El workflow reusable y la sesión `nox -s qa` delegan exactamente en ese script.

- `.github/workflows/qa.yml` es el **wrapper** para eventos `pull_request`.
- `.github/workflows/quality.yml` es el **wrapper** para eventos `push`.

Ambos wrappers delegan en el reusable para evitar duplicación. El reusable se divide en dos jobs contractuales: `tests-matrix` (matriz `3.9`, `3.10`, `3.11`) y `static-security` (solo `3.11`). Cada job delega en `tools/qa.sh` con `--scope` para no repetir auditorías de seguridad en toda la matriz.

Como política de mínimo privilegio, `qa.yml`, `quality.yml` y `reusable-quality.yml` deben declarar permisos explícitos de solo lectura (`permissions: { contents: read }`) a nivel workflow o job. Ninguno de estos pipelines necesita permisos de escritura adicionales para ejecutar `actions/checkout`, `actions/setup-python` y los comandos de QA.

El preflight soporta selección explícita por suite con `--suite`:

- `--suite default`: validación mínima (sin dependencias opcionales).
- `--suite cli`: valida dependencias de CLI (incluye `watchdog`).
- `--suite websocket`: valida dependencias de WebSocket (incluye `websockets`).
- `--suite perf`: validación específica para benchmarks de rendimiento.

Se pueden combinar suites repitiendo la bandera (por ejemplo, `--suite unit --suite cli --suite websocket`).

Orden real de QA (idéntico en shell, reusable workflow y nox):

1. `python tools/check_test_dependencies.py --suite unit --suite cli --suite websocket`
2. `python tools/check_package_data_files.py`
3. `python tools/check_canonical_repo_links.py`
4. `python tools/check_github_workflows.py`
5. `python -m pytest`
6. `python -m ruff check .`
7. `python -m black --check .`
8. `python -m mypy fletplus`
9. `python tools/check_bandit_command_sync.py`
10. `python -m bandit -c pyproject.toml -r fletplus`
11. `python -m pip_audit -r requirements.txt -r requirements-dev.txt --policy pip-audit.policy.json`
12. `python -m safety check -r requirements.txt -r requirements-dev.txt --policy-file safety-policy.yml`

Si se necesita exceptuar una vulnerabilidad de forma temporal, debe documentarse en los archivos de política correspondientes (`pip-audit.policy.json` y `safety-policy.yml`) con justificación y fecha de expiración.

> ⚠️ **Mantenimiento CI**: cualquier cambio de pasos de QA debe hacerse primero en `tools/qa.sh`. El workflow reusable y `nox -s qa` deben limitarse a invocar ese script para preservar la sincronía. En CI, el reusable usa `bash tools/qa.sh --scope tests-matrix` y `bash tools/qa.sh --scope static-security`; localmente puedes ejecutar `bash tools/qa.sh` (scope `all`) para correr todo. Además, `tools/check_bandit_command_sync.py` valida que `tools/qa.sh` mantenga el comando canónico de Bandit y que el reusable siga delegando en `tools/qa.sh`.

### Política formal de actualización de baseline/target de Flet

La matriz `flet-version-matrix` sigue una política de revisión **obligatoria y periódica**:

- **Cadencia mínima:** revisión mensual del target (`latest-migration-target`).
- **Cadencia extraordinaria:** actualización inmediata ante un release crítico de Flet (breaking fixes, deprecaciones relevantes o seguridad).

Definiciones contractuales:

- **baseline (`min-supported`)**: minor mínimo soportado activamente por el proyecto.
- **target (`latest-migration-target`)**: última minor estable validada para migración progresiva.

Fuente de verdad y automatización:

1. La fuente de verdad de minors de CI es `tools/flet_version_matrix_config.py` (`FLET_MATRIX_MINORS`).
2. Cualquier cambio debe realizarse con `python tools/update_flet_target.py --baseline-minor <X.Y> --target-minor <A.B>`.
3. El script actualiza de forma centralizada:
   - `.github/workflows/reusable-quality.yml`
   - `tools/flet_version_matrix_config.py`
   - `docs/migration-flet-latest.md`
4. El contrato CI (`python tools/check_ci_workflow_contract.py`) falla si workflow/config/docs no coinciden en baseline/target.
5. Todo salto de target debe registrarse en `CHANGELOG.md` con fecha y motivo (breaking fixes/deprecaciones/seguridad).


### Validación local de workflows (GitHub Actions)

`tools/qa.sh` ejecuta `python tools/check_github_workflows.py`, que valida:

- Sintaxis YAML de cada archivo en `.github/workflows/*.yml` y `.github/workflows/*.yaml`.
- Reglas base de GitHub Actions (presencia de `on`, `jobs`, estructura de `steps`, y consistencia `uses`/`runs-on`).

Instalación necesaria para este check:

```bash
pip install -r requirements-dev.txt
```

El script depende de `PyYAML` (incluido en `requirements-dev.txt`).

### Depuración de errores de workflows en local

Si falla la validación de workflows:

1. Ejecuta solo el check para aislar el error:

   ```bash
   python tools/check_github_workflows.py
   ```
2. Revisa el archivo y job/step indicado en el mensaje de error.
3. Verifica YAML con parser local:

   ```bash
   python - <<'PY'
from pathlib import Path
import yaml
path = Path('.github/workflows/reusable-quality.yml')
yaml.safe_load(path.read_text(encoding='utf-8'))
print('YAML OK')
PY
   ```
4. Reejecuta QA según necesidad:

   ```bash
   bash tools/qa.sh --scope tests-matrix
   bash tools/qa.sh --scope static-security
   # o todo junto:
   bash tools/qa.sh
   ```

## Estrategia de tests: suite rápida vs benchmarks

La configuración base de `pytest` en este repositorio define `addopts = -m "not perf"`, por lo que la ejecución estándar excluye benchmarks y prioriza feedback rápido en desarrollo y CI principal:

```bash
python -m pytest
```

Los benchmarks viven bajo `tests/perf/` y se ejecutan de forma explícita con el marker `perf`:

```bash
python -m pytest -m perf -o addopts=
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

Si necesitas restringir el acceso, puedes configurar `auth_token` y opcionalmente `allowed_origins`. Con `auth_token`, el cliente debe enviar el secreto en un header dedicado (`Authorization: Bearer <token>` o `X-DevTools-Token: <token>`). Además, el header `Origin` debe coincidir con alguno de los orígenes permitidos cuando se configure `allowed_origins`. Las conexiones que no cumplan estos requisitos se rechazan con un cierre de política.

Cuando el servidor se expone fuera de loopback (`0.0.0.0`, `::` o IP no local), `auth_token` pasa a ser obligatorio. En ese escenario, `allowed_origins` por sí solo no basta para habilitar la exposición remota.

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

En backend de archivo (`_FileBackend.save`) FletPlus aplica **modo seguro por defecto**: la ruta final (canonizada con `resolve(strict=False)`) debe permanecer dentro de un directorio confiable. Ese root es `~/.fletplus` por defecto o el valor de `FLETPLUS_PREFS_TRUSTED_ROOT` si se define. Si `FLETPLUS_PREFS_FILE` apunta fuera de ese root, el guardado se rechaza con `logger.error`.

Para compatibilidad con despliegues existentes puedes habilitar un modo opt-in con `FLETPLUS_PREFS_ALLOW_ARBITRARY_PATH=1`; en ese caso se permite la ruta arbitraria y se registra `logger.warning` explícito para facilitar migración controlada. Además, se rechaza cualquier ruta con componentes symlink (archivo/directorio) y se repite la validación antes de `os.replace`, junto con archivo temporal protegido (`O_EXCL`, `O_NOFOLLOW`, `O_CLOEXEC` cuando están disponibles).

`FletPlusApp` crea automáticamente una instancia de `PreferenceStorage` y observa los cambios de `ThemeManager`. Al iniciar la app se restauran el modo claro/oscuro y los *tokens* guardados; cada vez que el usuario cambia el tema, los nuevos valores se escriben otra vez en el almacenamiento elegido. Así garantizas que la preferencia visual permanece entre sesiones sin código adicional (Core legacy en `fletplus/core_legacy.py`).

> 🧭 Si también deseas persistir preferencias de accesibilidad (escala de texto, contraste, movimiento), consulta cómo reutilizar `AccessibilityPreferences` junto al `ThemeManager` en [la guía de componentes](components.md#preferencias-accesibilidad).

## Soporte PWA

El módulo `fletplus.web.pwa` incluye tres utilidades clave:

- `generate_service_worker(static_files, output_dir)` crea un `service_worker.js` con una caché estática (`STATIC_ASSETS`) e instala controladores `install` y `fetch` para responder con recursos cacheados cuando sea posible.
- `generate_manifest(name, icons, start_url, output_dir)` genera un `manifest.json` con nombre, URL inicial y lista de iconos.
- `register_pwa(page, manifest_url, service_worker_url)` añade la etiqueta `<link rel="manifest">` al `<head>` de la página y registra el *service worker* asegurándose de que las rutas sean del mismo origen.

Una vez generados ambos archivos, sirve el directorio que los contiene y llama a `register_pwa(page)` durante la inicialización de tu app web para activar la experiencia instalable.

## Política de upgrade de Flet y release

Esta política define cómo mantenemos la compatibilidad de FletPlus con Flet y cómo hacemos trazable cada salto de versión.

### Versión objetivo, cadencia y rollback

- **Versión objetivo vigente**: `flet==0.80.x` (target de migración en CI).
- **Estado del target vigente**: ✅ validado oficialmente para la serie `0.80.x` (incluyendo el parche más reciente validado en esta iteración).
- **Baseline de validación en CI**: `flet>=0.29,<0.30` (`min-supported`).
- **Mínimo de empaquetado**: `flet>=0.29,<0.81` (publicado en `pyproject.toml` y replicado en plantillas/dev).
- **Cadencia de actualización**: revisión **mensual** de nuevas versiones de Flet, con posibilidad de adelanto por seguridad o correcciones críticas.
- **Rollback**: se revierte al objetivo anterior cuando ocurra cualquiera de estos escenarios:
  1. Ruptura de API pública de FletPlus.
  2. Fallo reproducible en demos oficiales.
  3. Fallo en checks de CI sin mitigación dentro de la ventana de release.
  4. Regresión funcional en la matriz de compatibilidad (`baseline` o `target`) que bloquee contratos críticos de navegación, tema o demo.

Todo upgrade/rollback debe registrarse en `CHANGELOG.md` indicando versión evaluada, decisión y motivo.

### Contrato de versión vigente

Este bloque es la referencia **única** para evitar desalineaciones entre documentación, CI y validación local:

- **Mínimo de paquete (distribución)**: `pyproject.toml` declara `flet>=0.29,<0.81`.
- **Baseline/target en CI**: `.github/workflows/reusable-quality.yml` valida `min-supported` (`flet>=0.29,<0.30`) y `latest-migration-target` (`flet>=0.80,<0.81`).
- **Validación local de minors permitidos**: `tools/flet_version_matrix_config.py` define `FLET_MATRIX_MINORS = ("0.29", "0.80")` y `ALLOWED_FLET_MINORS`.
- **Sin minors legacy fuera del contrato**: `ALLOWED_FLET_MINORS` debe coincidir exactamente con `FLET_MATRIX_MINORS`; no se aceptan tolerancias residuales (como `0.27`) en validaciones locales o CI.

Regla operativa: cualquier cambio de baseline o target se realiza primero en `tools/flet_version_matrix_config.py` y luego se replica de forma idéntica en el workflow de CI y documentación asociada.

### Upgrade de Flet (paso a paso)

1. **Actualizar manifiestos de dependencias**
   - Ajustar la versión objetivo en `pyproject.toml` y en los `requirements*` usados por desarrollo/CI (`requirements.txt`, `requirements-dev.txt`, `requirements-docs.txt` si aplica).
   - Confirmar que las restricciones mínimas siguen siendo coherentes con la baseline soportada en CI.
2. **Actualizar la matriz de CI**
   - Revisar workflows (`.github/workflows/*.yml`) para asegurar que la matriz `baseline/target` refleja la nueva minor objetivo.
   - Verificar que los jobs de QA ejecuten la combinación mínima y la objetivo antes de aprobar release.
3. **Revisión de `flet_compat`**
   - Auditar `fletplus/flet_compat.py` y cualquier capa de compatibilidad asociada.
   - Mantener wrappers/guards para APIs de Flet deprecadas hasta que dejen de ser necesarias por política de soporte.
4. **Ejecutar suites mínimas de contrato**
   - Ejecutar como mínimo la suite de contrato y una pasada rápida de regresión sobre CLI/demo.
   - Comandos recomendados:

```bash
python -m pytest tests/contracts -q
python -m pytest tests/cli -q
python -m pytest tests/demo -q
```

### Checklist de aceptación para upgrade de Flet

Antes de cerrar el upgrade, verificar:

- [ ] No se rompe ninguna API pública de FletPlus.
- [ ] La demo oficial no presenta regresiones funcionales ni visuales críticas.
- [ ] La CLI principal (`fletplus`) mantiene comandos y comportamiento documentado.
- [ ] Los tests de contrato pasan en baseline y target de la matriz.
- [ ] `CHANGELOG.md` documenta versión evaluada, decisión (upgrade o rollback) y motivo.

### Criterio de rollback y reversión rápida de minor

Se activa rollback inmediato si aparece cualquiera de estos casos tras subir la minor objetivo:

1. Ruptura de API pública de FletPlus.
2. Regresión crítica en demo o CLI sin mitigación en la ventana de release.
3. Fallo consistente en tests de contrato (baseline o target) que comprometa compatibilidad.

Para revertir rápidamente la minor objetivo:

1. Restablecer la versión anterior en `pyproject.toml` y `requirements*`.
2. Restaurar la matriz de CI previa (`baseline/target`) en workflows.
3. Revertir ajustes de `flet_compat` introducidos exclusivamente para la minor fallida.
4. Ejecutar de nuevo `tests/contracts`, `tests/cli` y `tests/demo` para confirmar estabilización.
5. Registrar rollback en `CHANGELOG.md` con causa raíz y plan de reintento.

## Workflow de documentación

El repositorio incluye el workflow [`.github/workflows/docs.yml`](../.github/workflows/docs.yml), que valida la documentación en `pull_request` (ramas `main` y `develop`) y la publica en GitHub Pages cuando hay `push` a `main`. El job `build` instala Python 3.11, las dependencias de `requirements-docs.txt` y ejecuta `mkdocs build --strict --site-dir site` antes de subir el resultado como artefacto de Pages:

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

El job `deploy` depende de ese artefacto y ejecuta `actions/deploy-pages@v4`, exponiendo la URL final a través de la salida `page_url`:

```yaml
  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    steps:
      - id: deploy
        uses: actions/deploy-pages@v4
```

> ✅ Recuerda habilitar GitHub Pages la primera vez desde **Settings → Pages** seleccionando “GitHub Actions” como fuente. Después de ese paso manual, cada `pull_request` a `main`/`develop` validará la documentación sin publicar y cada `push` sobre `main` publicará la nueva versión.

Para mantener la compatibilidad de enlaces entre el `README.md` en GitHub y el `index.md` de MkDocs (que incluye ese README), sigue también la guía breve de [estilo de enlaces](link-style.md).

Además, `tools/check_ci_workflow_contract.py` valida automáticamente el contrato mínimo de CI para documentación y rendimiento, junto con la política de permisos mínimos en workflows QA:

- `docs.yml` debe conservar los jobs `build`/`deploy`; el workflow debe incluir `pull_request` hacia `main` y `develop`, `build` debe ejecutar `mkdocs build --strict` y usar `actions/configure-pages` + `actions/upload-pages-artifact`, y `deploy` debe usar `needs: build`, `actions/deploy-pages` y la condición `if: github.event_name == 'push' && github.ref == 'refs/heads/main'`.
- `perf.yml` debe instalar dependencias de desarrollo (`pip install -r requirements-dev.txt`) y ejecutar benchmarks con `python -m pytest -m perf`. Si `pytest.ini` define una exclusión global del marker `perf` (por ejemplo, `addopts = -m "not perf"`), entonces el workflow debe forzar el override `-o addopts=` para garantizar que los benchmarks sí se ejecuten en CI.
- `qa.yml`, `quality.yml` y `reusable-quality.yml` deben declarar `permissions` explícitos con `contents: read` (a nivel workflow o job), evitando permisos de escritura innecesarios en CI.

Estos checks se ejecutan en tests (`tests/test_check_ci_workflow_contract.py`) para detectar drift antes de mezclar cambios en workflows.
