# Herramientas de desarrollo y publicación

Esta guía reúne los apoyos disponibles durante el ciclo de vida de una app FletPlus: desde las utilidades de depuración, pasando por la recarga en caliente de la CLI y los gestores de escritorio, hasta la automatización de despliegue de la documentación.

## DevTools integrados

`DevToolsServer` expone un servidor WebSocket ligero que reenvía mensajes entre clientes conectados. Cada vez que un cliente envía un *frame*, el servidor lo redistribuye al resto y guarda instantáneas iniciales (payloads con tipo `snapshot`) para nuevos suscriptores. De esta manera puedes abrir la vista de DevTools en múltiples navegadores y mantenerlos sincronizados mientras inspeccionas el estado de la app.【F:fletplus/devtools/server.py†L15-L86】

Para integrarlo en tu proyecto, arranca `DevToolsServer().listen()` dentro de un `asyncio.Task` y comparte la URL en tus herramientas de depuración o paneles administrativos.

## Recarga en caliente desde la CLI

El comando `fletplus run` monitoriza el árbol del proyecto (ignorando carpetas temporales como `.git`, `__pycache__` o `build`) mediante `watchdog`. Cuando detecta cambios en archivos Python, JSON o YAML, detiene el proceso actual de `flet run` y lo reinicia, conservando las opciones de puerto y activando los DevTools salvo que se haya pasado `--no-devtools`. También admite seleccionar el archivo principal con `--app` y la carpeta a vigilar con `--watch`.【F:fletplus/cli/main.py†L83-L171】

## Gestores de escritorio

### Ventanas adicionales

`WindowManager` mantiene un registro de páginas abiertas y permite alternar el foco entre ellas. La instancia principal se guarda bajo la clave `"main"`; al crear una nueva ventana basta con llamar a `open_window` con un nombre identificador. Si la página expone `window_to_front`, el gestor la llama automáticamente al recuperar el foco con `focus_window` para asegurar que quede visible.【F:fletplus/desktop/window_manager.py†L1-L38】

### Bandeja del sistema

`SystemTray` ofrece una envoltura mínima sobre el icono de bandeja, manteniendo su visibilidad y un manejador de clic configurable a través de `on_click`. Puedes mostrar u ocultar el icono con `show()`/`hide()` y simular eventos durante pruebas con `_emit_click`. Es útil para exponer accesos rápidos a estados de la app cuando se minimiza a la bandeja.【F:fletplus/desktop/system_tray.py†L1-L25】

## Preferencias persistentes y temas

`PreferenceStorage` determina el backend disponible en tiempo de ejecución: si la página cuenta con `client_storage` (p. ej. aplicaciones empaquetadas con Flet), se guarda bajo una clave JSON; de lo contrario utiliza un archivo local configurable vía `FLETPLUS_PREFS_FILE`. Los métodos `load()` y `save()` devuelven/reciben diccionarios con los valores a persistir.【F:fletplus/utils/preferences.py†L19-L107】

`FletPlusApp` crea automáticamente una instancia de `PreferenceStorage` y observa los cambios de `ThemeManager`. Al iniciar la app se restauran el modo claro/oscuro y los *tokens* guardados; cada vez que el usuario cambia el tema, los nuevos valores se escriben otra vez en el almacenamiento elegido. Así garantizas que la preferencia visual permanece entre sesiones sin código adicional.【F:fletplus/core.py†L120-L175】

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
