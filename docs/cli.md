# CLI de FletPlus

La línea de comandos `fletplus` facilita el ciclo de vida de una aplicación construida
con FletPlus. Tras instalar el paquete podrás ejecutar el comando `fletplus`
desde cualquier terminal.

## Instalación

```bash
pip install fletplus
```

## Comandos disponibles

### `fletplus create <nombre>`

Genera una estructura base para comenzar un nuevo proyecto. Por defecto el
directorio se crea dentro de la carpeta actual, aunque puedes indicar una ruta
distinta con `--directorio`.

Archivos generados:

- `README.md` con instrucciones básicas.
- `requirements.txt` con dependencias mínimas.
- `.gitignore` preconfigurado.
- Paquete `src/` con un `main.py` listo para ejecutar.

### `fletplus run`

Inicia el servidor de desarrollo con recarga automática y DevTools activado.
Opciones relevantes:

- `--app PATH`: Archivo principal de la aplicación (por defecto `src/main.py`).
- `--port PORT`: Puerto HTTP para abrir la vista web (por defecto `8550`).
- `--no-devtools`: Desactiva DevTools.
- `--watch PATH`: Carpeta a monitorear para la recarga (por defecto el directorio actual).

El comando mantiene un observador de archivos usando `watchdog`; cada vez que se
detecta un cambio se reinicia el proceso `flet run` con la opción `--devtools`.

### `fletplus build`

Reservado para futuros flujos de empaquetado. Por ahora muestra un mensaje con
recomendaciones para usar herramientas existentes como `flet pack`.
