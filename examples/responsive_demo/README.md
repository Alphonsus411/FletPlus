# Demostraciones responsivas

Este directorio contiene demos enfocadas en navegación y layouts adaptables.

## floating_navigation_demo.py

Muestra una navegación flotante orientada a móvil con breakpoints y
transiciones del panel lateral.

```bash
python floating_navigation_demo.py
```

> Nota: otros ejemplos responsivos del proyecto viven en `examples/` y se
> documentan en la sección principal de demos del repositorio.



## viewport_density_demo.py

Muestra los nuevos helpers de `fletplus.utils.viewport`: ancho/alto seguro,
orientación, perfil activo, padding mobile y densidad visual.

```bash
python viewport_density_demo.py
```

Redimensiona la ventana o rota el dispositivo para ver cómo cambian
`portrait`/`landscape`, el perfil (`mobile`, `tablet`, `desktop`) y la densidad
`compact`, `normal` o `comfortable`.
