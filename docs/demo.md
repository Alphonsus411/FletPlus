# Demo de FletPlus

Tras instalar el paquete puedes ejecutar la demostración de dos formas equivalentes.
Desde la versión actual el alias oficial con guion (`fletplus-demo`) queda
registrado automáticamente, aunque el comando clásico con guion bajo se mantiene
por compatibilidad:

```bash
fletplus-demo
```

o bien utilizando `pipx` si prefieres ejecutar la demo sin instalarla globalmente
o comprobarla tras reinstalar el paquete:

```bash
pipx run fletplus_demo
```

Ambos comandos lanzan la aplicación definida en `fletplus_demo.main`.

## Capturas automatizadas de la demo

Si necesitas recursos actualizados para documentación o presentaciones puedes
solicitar que la demo renderice cada pantalla fuera de cámara y genere los
archivos correspondientes:

```bash
fletplus-demo --capture docs/assets/demo/capturas
```

El comando anterior guardará un PNG por ruta (`inicio.png`, `dashboard.png`,
etc.) utilizando un *viewport* de 1280×720 píxeles por defecto. Para generar
clips MP4 estáticos (basados en dichas capturas) añade la opción `--record`:

```bash
fletplus-demo \
  --capture docs/assets/demo/capturas \
  --record docs/assets/demo/videos \
  --width 1440 --height 900 --duration 4 --fps 30
```

La grabación requiere instalar dependencias opcionales:

```bash
pip install imageio imageio-ffmpeg
```

Los nombres de archivo reflejan el estado actual de cada vista definida en la
aplicación (`inicio`, `dashboard`, `reportes`, `usuarios` y `configuracion`).
Cuando únicamente se solicitan capturas o grabaciones la herramienta finaliza
una vez exportados los recursos, sin abrir la interfaz interactiva. Si deseas
generar los activos y, además, abrir la aplicación, añade la bandera `--launch`.
