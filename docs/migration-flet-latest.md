# Migración a Flet (última versión)

## Objetivo

Este documento define una migración **controlada por fases** para compatibilizar FletPlus con la versión más reciente de Flet, cubriendo las áreas:

- `fletplus/components/`
- `fletplus/themes/`
- `fletplus/utils/`
- `fletplus/core_legacy.py`
- `fletplus_demo/`

**Baseline de validación (estado actual en CI)**: `flet>=0.29,<0.30` (job `min-supported`).  
**Versión objetivo de migración (estado objetivo en CI)**: `flet>=0.80,<0.81` (job `latest-migration-target`).  
**Estado oficial del target**: ✅ **validado para toda la serie del minor objetivo vigente**, incluyendo el parche más reciente disponible durante esta iteración de validación.  
**Rango contractual de paquete (distribución/dev/plantillas)**: `flet>=0.29,<0.81` (según `pyproject.toml`, `requirements-dev.txt` y template CLI).

---

## Dependencias necesarias

Para evitar drift entre CI, desarrollo local y plantillas CLI, esta tabla fija la política de rangos activos:

| Dependencia | Versión mínima | Versión máxima (exclusiva) | Referencia contractual |
|---|---:|---:|---|
| `flet` | `0.29` (baseline contractual y paquete distribuible) | `0.81` | `pyproject.toml`, `requirements-dev.txt`, `fletplus/cli/templates/app/requirements.txt` |
| `websockets` | `13` | `14` | `pyproject.toml`, `requirements-dev.txt` |
| `httpx` | `0.28` | `1` | `pyproject.toml`, `requirements-dev.txt` |
| `watchdog` | `3` | `7` | `pyproject.toml` (`optional-dependencies.dev`), `requirements-dev.txt` |
| `pytest` | `7.4` | `9` | `pyproject.toml` (`optional-dependencies.dev`), `requirements-dev.txt` |

> Nota operacional: con el contrato vigente no hay dualidad baseline/paquete para `flet`; tanto baseline CI como manifiestos de distribución y desarrollo parten de `0.29`.

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
| `components` | escritura de `page.window_width` en `adaptive_layout` | Sensible (API histórica) | En runtimes recientes suele preferirse `page.window.width` | Implementado mediante helpers de compatibilidad y reutilizado en componentes. |
| `core_legacy` / `demo` | atributos directos de `page` (`title`, `scroll`, `controls`, `update`) | Vigente | Sin deprecación directa detectada | Mantener; reforzar tests de smoke de demo. |
| `window/page attrs` | Gestión de ventana encapsulada en `WindowManager` | Vigente (sujeto a runtime) | Equivalencia recomendada: encapsular cambios en helper único | Mantener centralización en `WindowManager` y evitar acceso disperso. |

> Nota: cuando el upstream de Flet introduce cambios de nombre o semántica por plataforma, la estrategia recomendada aquí es **compatibilidad por adaptación (feature detection)** en lugar de ruptura directa.

---


### Inventario operativo de puntos sensibles (fuente de contratos)

Este inventario se usa como referencia directa de los contratos de prueba:

- **Navegación responsive (`fletplus/components/`)**: construcción y cambio de estado de `NavigationBar`, `NavigationRail`, `NavigationDrawer`, apertura/cierre de drawer y sincronización de índice seleccionado.
- **Atributos `Page`/`window` (`fletplus/components/`, `fletplus/core_legacy.py`)**: lectura/escritura de ancho y alto mediante `page.window.width|height`, `page.window_width|window_height` y fallback a `page.width|height`.
- **Navegación y rutas (`fletplus/router/`)**: contrato de `router.go/replace`, observadores, fallback cuando backends nativos no están disponibles y resolución determinista de rutas.
- **Tema por plataforma (`fletplus/themes/`)**: lectura de `platform_brightness`/`platform_theme`, listeners de plataforma, aplicación de `theme_mode`, y no-regresión de tokens custom.
- **Iconografía crítica (`fletplus/components/`, `fletplus/icons/`)**: uso de `ft.Icons.*` en navegación y overlays con fallback explícito cuando upstream renombra iconos.

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

1. ✅ Añadir un adaptador explícito para atributos de ventana (`page.window_width` ↔ `page.window.width`) y reutilizarlo desde componentes/core.
2. ✅ Añadir pruebas específicas de compatibilidad de iconos críticos en demo/componentes (fallback controlado).
3. ✅ Mantener una matriz de compatibilidad por versión de Flet en CI para detectar regresiones tempranas.

---

## 6) Criterio de compatibilidad

Se considera que la migración es compatible **sin ruptura** solo si se mantiene el contrato público y operativo de estos módulos:

- `fletplus/components`: navegación adaptativa, layout responsive e iconografía crítica.
- `fletplus/themes`: `ThemeManager`, tokens, modo oscuro y sincronización por plataforma.
- `fletplus/utils`: accesibilidad, responsive y utilidades de `Page`/`window`.
- `fletplus_demo`: arranque, rutas principales y smoke de ejecución.

Cualquier cambio en Flet que rompa uno de estos cuatro bloques mantiene la migración en estado **abierto** hasta corregir el contrato.

## 7) Estado actual vs estado objetivo (única tabla de referencia)

| Ámbito | Estado actual (observado en repo) | Estado objetivo de migración | Fuente de verdad |
|---|---|---|---|
| Manifiesto de paquete | `pyproject.toml`: `flet>=0.29,<0.81` | Mantener rango contractual de distribución/desarrollo hasta nuevo contrato | `pyproject.toml` |
| CI baseline (`flet-version-matrix`) | `flet>=0.29,<0.30` (`min-supported`) | Mantener baseline contractual de regresión | `.github/workflows/reusable-quality.yml` |
| CI target (`flet-version-matrix`) | `flet>=0.80,<0.81` (`latest-migration-target`) | Consolidar compatibilidad funcional sobre `0.80.x` | `.github/workflows/reusable-quality.yml` |
| Validación local de minors | `FLET_MATRIX_MINORS = ("0.29", "0.80")` y `ALLOWED_FLET_MINORS = frozenset(FLET_MATRIX_MINORS)` | Mantener sincronía exacta con matriz CI sin tolerancias legacy | `tools/flet_version_matrix_config.py` |
| Dependencias legacy fuera de contrato | Cualquier pin histórico fuera de baseline/target activo | No permitido en contrato vigente; eliminar tolerancias locales y en pruebas | Revisión en PR + checks contractuales |

> Regla operativa: para el contrato activo usar únicamente la sección [Contrato de versión vigente](tooling.md#contrato-de-version-vigente). Esta tabla se mantiene alineada con ese bloque en cada cambio de baseline/target.


## 8) Procedimiento operacional mensual (actualización de target)

> Fuente de verdad única para mover baseline/target: `tools/update_flet_target.py`.

1. Detectar la nueva **minor estable** publicada en PyPI para `flet` (ignorando pre-releases).
2. Definir valores de trabajo:
   - `--baseline-minor X.Y` = minor baseline contractual vigente.
   - `--target-minor A.B` = minor estable nueva que se quiere validar como target.
3. Ejecutar la actualización atómica (workflow + config + documento):

   ```bash
   python tools/update_flet_target.py --baseline-minor X.Y --target-minor A.B
   ```

4. Validar que no exista drift y que la matriz CI refleje exactamente `tools/flet_version_matrix_config.py`:

   ```bash
   python tools/check_flet_target_drift.py
   ```

5. Ejecutar la validación de contrato CI/docs antes de abrir PR:

   ```bash
   python tools/check_ci_workflow_contract.py
   ```

6. Correr la batería de QA del proyecto (`bash tools/qa.sh --scope tests-matrix` o pipeline completo) y actualizar este documento solo para evidencias/resultados de la iteración.

## 9) Checklist final de aceptación técnica

La migración solo se puede cerrar cuando **todos** los puntos siguientes estén en verde:

- [x] **Contratos de API sensible**: `tests/test_flet_api_contracts.py` valida navegación, `Page.window`, `update/update_async` y transiciones.
- [x] **Compatibilidad de iconos críticos**: `tests/test_icons.py` valida resolución de `ft.Icons.*` y fallback explícito.
- [x] **Smoke de demo**: `tests/test_demo_template_smoke.py` confirma arranque básico del flujo demo/template.
- [x] **Matriz CI de versiones Flet**: `tests/test_flet_version_matrix.py` en verde para `min-supported` y `latest-migration-target`.
- [x] **Regresión CLI mínima**: `tests/test_cli_main.py` y `tests/test_cli_build.py` en verde.

Si cualquier ítem falla, el estado de migración permanece **abierto** y no se promueve la versión objetivo como estable.

## 10) Resultado final de migración (iteración actual)

- Estado final: ✅ **migración cerrada para el minor target vigente**.
- Decisión operativa: el target `latest-migration-target` queda oficialmente validado y vigente.
- Alcance de deuda legacy: se mantiene únicamente por compatibilidad histórica local y queda fuera del contrato activo de soporte.
