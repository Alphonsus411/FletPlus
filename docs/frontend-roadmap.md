# Roadmap frontend de FletPlus

Esta guía dedicada organiza el trabajo frontend sin reemplazar el backlog general. El historial y las tareas transversales continúan en [`TAREAS_IMPLEMENTACION.md`](TAREAS_IMPLEMENTACION.md); esta página solo desglosa la planificación específica de interfaz, experiencia visual y plantillas.

## Módulos de referencia

Usa estos módulos como punto de partida antes de abrir nuevas tareas o crear implementaciones paralelas:

- `fletplus/frontend/config.py`: configuración declarativa de paletas, tokens, fuentes, densidades, perfiles responsive y aplicación sobre `ft.Page`.
- `fletplus/utils/viewport.py`: lectura robusta de viewport, orientación, perfil activo, padding seguro y helpers de contenedor adaptable.
- `fletplus/components/frontend_layouts.py`: layouts reutilizables para shell, secciones, hero, toolbars, footers y composición responsive.
- `fletplus/cli/templates/*`: plantillas CLI por target (`web`, `desktop`, `mobile`) y archivos base que deben mantenerse alineados con la documentación.

## Criterio común de finalización

Cada bloque se considera listo cuando cumple las tres evidencias mínimas:

1. **Tests**: añade o actualiza pruebas unitarias/smoke que cubran el contrato cambiado.
2. **Docs**: actualiza la página afectada (`frontend-projects.md`, `themes.md`, `responsive.md`, `cli.md` o esta guía) con ejemplos y decisiones relevantes.
3. **Ejemplo funcional**: valida al menos una plantilla o miniapp que use el flujo documentado (`fletplus create`, `fletplus run` o una vista mínima equivalente).

## Bloque 1 — Paletas y tokens visuales

**Objetivo:** consolidar un sistema de color editable, consistente por target y fácil de auditar.

- [ ] Revisar que `FrontEndConfig.palette_for_target()` conserve tokens base cuando existan overrides por plataforma.
- [ ] Documentar paletas recomendadas por tipo de producto: landing, dashboard, admin, SaaS, ecommerce y mobile app.
- [ ] Añadir ejemplos de tokens semánticos (`brand`, `surface_soft`, `focus_ring`, `success`, `error`) en plantillas CLI.
- [ ] Validar contraste mínimo en componentes principales y estados interactivos.

**Módulos implicados:** `fletplus/frontend/config.py`, `fletplus/cli/templates/*`.

**Criterio de finalización del bloque:** tests de resolución de paletas, docs con matriz de uso y ejemplo funcional que cambie paleta desde CLI o `pyproject.toml`.

## Bloque 2 — Pantalla, viewport y perfiles responsive

**Objetivo:** asegurar que web, escritorio y móvil respondan de forma predecible ante tamaños, orientación y APIs cambiantes de Flet.

- [ ] Reforzar fallback entre `Page.width/height`, `Page.window.width/height` y valores de configuración.
- [ ] Cubrir orientación y perfiles (`mobile`, `tablet`, `desktop`, `large_desktop`) en pruebas de regresión.
- [ ] Documentar patrones para SafeArea, padding seguro y ancho máximo por target.
- [ ] Añadir guía de revisión manual para breakpoints críticos antes de publicar.

**Módulos implicados:** `fletplus/utils/viewport.py`, `fletplus/frontend/config.py`, `fletplus/components/frontend_layouts.py`.

**Criterio de finalización del bloque:** tests de viewport, docs responsive actualizadas y ejemplo funcional redimensionable en al menos web o escritorio.

## Bloque 3 — Layout y composición de pantallas

**Objetivo:** ofrecer estructuras reutilizables que eviten duplicación entre landing, dashboard, admin y móvil.

- [ ] Auditar helpers existentes para shell, content width, secciones, hero y footer.
- [ ] Definir patrones oficiales para sidebar desktop, navegación inferior móvil y contenido centrado web.
- [ ] Alinear spacing, padding y densidad con `FrontEndConfig` en todos los helpers.
- [ ] Añadir ejemplos de composición con tarjetas, acciones primarias y estados vacíos.

**Módulos implicados:** `fletplus/components/frontend_layouts.py`, `fletplus/frontend/config.py`, `fletplus/cli/templates/*`.

**Criterio de finalización del bloque:** tests/smoke de helpers de layout, docs con patrones por target y plantilla funcional que renderice un layout completo.

## Bloque 4 — Fuentes y tipografía

**Objetivo:** mantener una escala tipográfica responsive y configurable sin tamaños hardcodeados en vistas.

- [ ] Revisar roles tipográficos (`display`, `headline`, `title`, `body`, `label`, `caption`) y roles personalizados.
- [ ] Documentar carga de fuentes locales, fallbacks, pesos y estilos en `pyproject.toml`.
- [ ] Asegurar que `text_style()` degrade correctamente cuando falten tokens por perfil.
- [ ] Añadir ejemplos de navegación, badges y ayudas contextuales con roles semánticos.

**Módulos implicados:** `fletplus/frontend/config.py`, `fletplus/components/frontend_layouts.py`, `fletplus/cli/templates/*`.

**Criterio de finalización del bloque:** tests de resolución tipográfica, docs con fuente local y ejemplo funcional que aplique una familia personalizada.

## Bloque 5 — Assets e iconografía

**Objetivo:** centralizar rutas y convenciones de recursos para evitar referencias frágiles.

- [ ] Normalizar estructura `assets/fonts`, `assets/icons`, `assets/images` en plantillas.
- [ ] Mantener `frontend/assets.py` como punto único para constantes de recursos.
- [ ] Documentar requisitos PWA, iconos de escritorio y assets móviles.
- [ ] Añadir validación liviana de existencia de assets críticos antes de build.

**Módulos implicados:** `fletplus/cli/templates/*`, `fletplus/frontend/config.py`.

**Criterio de finalización del bloque:** tests o checks de assets críticos, docs de estructura de recursos y ejemplo funcional que cargue logo/fuente desde `assets/`.

## Bloque 6 — Plantillas CLI

**Objetivo:** garantizar que `fletplus create` genere proyectos modernos, consistentes y documentados.

- [ ] Comparar plantillas `web`, `desktop` y `mobile` para evitar divergencias accidentales.
- [ ] Sincronizar presets, paletas, densidad, fuentes y layout inicial con esta guía.
- [ ] Añadir smoke-tests de generación para presets principales.
- [ ] Mantener README de plantilla y docs de CLI con el mismo contrato de dependencias y comandos.

**Módulos implicados:** `fletplus/cli/templates/*`, `fletplus/frontend/config.py`, `fletplus/utils/viewport.py`.

**Criterio de finalización del bloque:** tests de generación CLI, docs de comandos actualizadas y ejemplo funcional creado desde plantilla limpia.

## Bloque 7 — Componentes frontend

**Objetivo:** reforzar componentes reutilizables para que consuman tokens y perfiles sin acoplarse a una app concreta.

- [ ] Inventariar componentes que ya consumen `FrontEndConfig` o helpers de viewport.
- [ ] Migrar colores, spacing y tipografía hardcodeados a tokens cuando sea viable.
- [ ] Documentar contratos mínimos de props para secciones, toolbars, layouts y estados de UI.
- [ ] Añadir ejemplos de loading, empty, error y success reutilizables.

**Módulos implicados:** `fletplus/components/frontend_layouts.py`, `fletplus/frontend/config.py`, `fletplus/utils/viewport.py`.

**Criterio de finalización del bloque:** tests de componentes, docs con API/ejemplos y ejemplo funcional que combine varios componentes en una pantalla.

## Bloque 8 — Validación y calidad continua

**Objetivo:** convertir el roadmap frontend en una rutina verificable antes de merge o release.

- [ ] Definir suite mínima: tests de config, viewport, layouts y generación CLI.
- [ ] Ejecutar `mkdocs build --strict` cuando cambien páginas de documentación.
- [ ] Registrar limitaciones conocidas en el backlog general si exceden el alcance frontend.
- [ ] Mantener esta guía enlazada desde el backlog para conservar trazabilidad.

**Módulos implicados:** `fletplus/frontend/config.py`, `fletplus/utils/viewport.py`, `fletplus/components/frontend_layouts.py`, `fletplus/cli/templates/*`, `docs/TAREAS_IMPLEMENTACION.md`.

**Criterio de finalización del bloque:** suite mínima documentada y ejecutada, docs compiladas y ejemplo funcional referenciado en la evidencia del cambio.

## Orden recomendado de ejecución

1. Paletas y tokens visuales.
2. Pantalla, viewport y perfiles responsive.
3. Layout y composición de pantallas.
4. Fuentes y tipografía.
5. Assets e iconografía.
6. Plantillas CLI.
7. Componentes frontend.
8. Validación y calidad continua.

## Relación con el backlog general

- Las tareas frontend nuevas deben enlazar esta página cuando afecten experiencia visual, plantillas, componentes o responsive.
- Las tareas de arquitectura, CI/CD, seguridad, release o compatibilidad transversal continúan en `docs/TAREAS_IMPLEMENTACION.md`.
- Si un bloque frontend descubre deuda fuera de su alcance, registra la deuda en el backlog general y conserva aquí solo el enlace o la decisión de producto.
