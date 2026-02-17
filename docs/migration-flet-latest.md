# Migración a Flet (última versión)

## Objetivo

Este documento define una migración **controlada por fases** para compatibilizar FletPlus con la versión más reciente de Flet, cubriendo las áreas:

- `fletplus/components/`
- `fletplus/themes/`
- `fletplus/utils/`
- `fletplus/core_legacy.py`
- `fletplus_demo/`

---

## 1) Checklist de compatibilidad por áreas

> Estado: `✅ completado`, `🟡 en progreso`, `⬜ pendiente`.

### A. `fletplus/themes/`

- ✅ Verificar API de tema base (`ft.Theme`, `ft.ThemeMode`, `color_scheme_seed`).
- ✅ Verificar sincronización de modo oscuro por plataforma (`platform_brightness` / `platform_theme`, listeners de plataforma).
- ✅ Revisar compatibilidad de helpers legacy (`primary_color`, `set_primary_color`).
- ✅ Confirmar aplicación de tokens extra como atributos custom (`radii`, `spacing`, `borders`, `shadows`).

### B. `fletplus/utils/`

- ✅ Verificar API de accesibilidad aplicada sobre `page.theme`.
- ✅ Revisar `PageTransitionsTheme` y `PageTransitionTheme.NONE` para reducción de movimiento.
- ✅ Revisar dependencia de atributos de `page` (`width`, `height`, `on_resize`, `update`).
- ✅ Revisar utilidades con contratos retrocompatibles (`ResponsiveStyle` vs dict por breakpoint).

### C. `fletplus/core_legacy.py`

- ✅ Verificar atributos de página y shell (`title`, `scroll`, `padding`, `spacing`, `controls`, `add`).
- ✅ Revisar navegación adaptativa (`NavigationBar`, `NavigationDrawer`, `router.go/replace`).
- ✅ Revisar iconografía (`ft.Icons.*`) en botones y destinos de navegación.
- ✅ Revisar integración opcional con ventana (`WindowManager`) y comportamiento por plataforma.

### D. `fletplus/components/`

- ✅ Revisar componentes de navegación (`AdaptiveNavigationLayout`, `UniversalAdaptiveScaffold`).
- ✅ Revisar iconos en componentes visuales (`sidebar`, `caption_overlay`, `smart_table`).
- ✅ Identificar puntos sensibles de atributos de ventana/página (`window_width` en layout adaptativo).
- ✅ Verificar uso de APIs de transición o navegación embebidas en componentes.

### E. `fletplus_demo/`

- ✅ Verificar compatibilidad del contrato de `FletPlusApp` legacy expuesto públicamente.
- ✅ Revisar uso de rutas + sidebar + iconos en demo.
- ✅ Confirmar que el bootstrap CLI (`run`, `--capture`, `--record`) mantiene compatibilidad.

---

## 2) Inventario de APIs sensibles y equivalencias/deprecaciones

La tabla siguiente registra las APIs de Flet más sensibles para upgrades, su estado esperado en versiones nuevas y la acción requerida en FletPlus.

| Área | API actual usada en FletPlus | Estado en versión nueva | Equivalencia / deprecación | Acción requerida |
|---|---|---|---|---|
| `themes` | `ft.Theme(color_scheme_seed=...)` | Vigente | Sin deprecación relevante para este uso | Mantener y cubrir con tests de `ThemeManager`. |
| `themes` | `page.theme_mode = ft.ThemeMode.DARK/LIGHT` | Vigente | Sin cambio funcional | Mantener; validar toggles de modo oscuro. |
| `themes` | `primary_color` (argumento legacy propio) | Vigente en FletPlus (wrapper) | Equivale a `tokens.colors.primary` en el modelo nuevo de tokens | Mantener como compatibilidad; priorizar tokens en nuevas integraciones. |
| `themes` | `platform_brightness` / `platform_theme` + listeners | Vigente con variaciones por runtime | Se soportan ambas variantes como equivalencia | Mantener doble lectura/listener para robustez cross-runtime. |
| `utils` | `ft.PageTransitionsTheme` + `ft.PageTransitionTheme.NONE` | Vigente | Sin deprecación directa detectada | Mantener para modo accesible (reduce motion). |
| `utils` | `page.on_resize`, `page.width`, `page.height` | Vigente | Sin deprecación directa detectada | Mantener; evitar asumir valores no nulos. |
| `core_legacy` | `ft.NavigationBar` + `NavigationBarDestination` | Vigente | Sin deprecación directa detectada | Mantener y aislar en fase de componentes base. |
| `core_legacy` | `ft.NavigationDrawer` + `NavigationDrawerDestination` | Vigente | Sin deprecación directa detectada | Mantener y validar sincronización de índice seleccionado. |
| `core_legacy` | `router.go(...)`, `router.replace(...)` (abstracción propia) | Vigente dentro de FletPlus | Equivale a navegación declarativa interna (no API Flet directa) | Mantener contrato y tests de rutas. |
| `components` | `ft.NavigationRail` / `ft.NavigationBar` adaptativos | Vigente | Sin deprecación directa detectada | Mantener; validar breakpoints y cambio de layout. |
| `components` | `ft.Icons.*` para iconografía | Vigente | Si un icono cambia en upstream, reemplazar por alias cercano | Añadir validación visual/funcional en tests de componentes. |
| `components` | escritura de `page.window_width` en `adaptive_layout` | Sensible (API histórica) | En runtimes recientes suele preferirse `page.window.width` | Introducir normalización/adapter en fase de refactor de componentes. |
| `core_legacy` / `demo` | atributos directos de `page` (`title`, `scroll`, `controls`, `update`) | Vigente | Sin deprecación directa detectada | Mantener; reforzar tests de smoke de demo. |
| `window/page attrs` | Gestión de ventana encapsulada en `WindowManager` | Vigente (sujeto a runtime) | Equivalencia recomendada: encapsular cambios en helper único | Mantener centralización en `WindowManager` y evitar acceso disperso. |

> Nota: cuando el upstream de Flet introduce cambios de nombre o semántica por plataforma, la estrategia recomendada aquí es **compatibilidad por adaptación (feature detection)** en lugar de ruptura directa.

---

## 3) Ejecución por fases (aislamiento de fallos)

### Fase 1 — Core utilidades (`themes` + `utils` + `core_legacy`)

**Objetivo:** estabilizar APIs base de tema, responsive, accesibilidad, navegación legacy y preferencias.

**Criterio de cierre:** tests de base y ejemplos mínimos relacionados en verde.

Checklist:
- ✅ Revisado inventario de APIs sensibles.
- ✅ Ejecutar tests de `ThemeManager`, `WindowManager`, preferencias, responsive y `FletPlusApp`.

### Fase 2 — Componentes base (`fletplus/components/`)

**Objetivo:** validar que los componentes adaptativos y de navegación siguen siendo compatibles.

**Criterio de cierre:** tests de componentes base + ejemplos mínimos de componentes en verde.

Checklist:
- ✅ Ejecutar tests de layout/navegación adaptativa y componentes principales.
- ✅ Confirmar estabilidad de iconos y eventos de navegación.

### Fase 3 — Demo y CLI (`fletplus_demo/` + `examples/`)

**Objetivo:** garantizar que la app de demo y su flujo CLI continúan operativos.

**Criterio de cierre:** tests de CLI/demo + ejemplos mínimos en verde.

Checklist:
- ✅ Ejecutar tests de CLI y smoke tests de ejemplos.
- ✅ Confirmar bootstrap/import de ejemplos.

---

## 4) Registro de validación por fase

> Este bloque debe actualizarse en cada iteración de migración.

### Resultado Fase 1

- Estado: ✅ Cerrada.
- Evidencia: tests de temas/utilidades/core legacy ejecutados y pasando.

### Resultado Fase 2

- Estado: ✅ Cerrada.
- Evidencia: tests de componentes base/adaptativos ejecutados y pasando.

### Resultado Fase 3

- Estado: ✅ Cerrada.
- Evidencia: tests de CLI y ejemplos mínimos ejecutados y pasando.

---

## 5) Acciones de seguimiento recomendadas

1. Añadir un adaptador explícito para atributos de ventana (`page.window_width` ↔ `page.window.width`) y reutilizarlo desde componentes/core.
2. Añadir pruebas específicas de compatibilidad de iconos críticos en demo (fallback controlado).
3. Mantener una matriz de compatibilidad por versión de Flet en CI para detectar regresiones tempranas.
