# Revisión general del proyecto FletPlus (perspectiva ingeniería senior)

**Fecha:** Febrero 2025  
**Alcance:** Estructura, arquitectura, estado, callbacks, dependencias, testabilidad y mantenibilidad.  
**Excluido:** Estilo, formato y naming salvo cuando afectan al diseño.

---

## 1. Resumen general del estado del proyecto

El proyecto es una biblioteca Python sobre Flet que aporta componentes avanzados, enrutamiento, gestión de estado (dos modelos: `AppState` en core y `Signal`/`Store` en state), temas, contextos reactivos y una aplicación “shell” con sidebar, paleta de comandos y navegación adaptable.

**Puntos fuertes:**
- **Core desacoplada** (`fletplus/core/`): diseño claro con `StateProtocol`, `LayoutComposition`, `FletPlusApp` con ciclo de vida y hooks; separación explícita entre estado, layout y refresco de UI.
- **Router** bien acotado, con observadores y sin depender de la UI.
- **Contextos** (`contextvars` + `ContextProvider`) bien definidos para tema, usuario e idioma.
- Buena cobertura de tests por módulo y uso de backends opcionales (Cython/Rust) con fallbacks.

**Problemas principales:**
- **Inconsistencia de API pública:** Lo que se exporta como `FletPlusApp` desde `fletplus.core` es la **nueva** app (layout + state). La demo y los tests de aplicación usan la **API legacy** (page, routes, sidebar, `build()`). Esa API vive en `core_legacy.py`, no reexportada por `core`. **Consecuencia:** los tests en `test_fletplus_app.py` fallan todos (AttributeError: no `build`, no `theme`, etc.) y la demo, si usara `from fletplus import FletPlusApp`, rompería con la firma actual de core.
- **Dos “cores” sin un contrato unificado:** Core nueva (desacoplada) y Core legacy (~1000 líneas, muchas responsabilidades en una sola clase) coexisten; la documentación indica usar `core_legacy` para la app completa, pero el paquete expone la nueva core como `FletPlusApp`.
- **Core legacy:** Alta concentración de responsabilidades (navegación, tema, sidebar, comandos, ventanas, responsive, contextos, preferencias, animación), mutación de `page` (state, contexts), callbacks que mezclan navegación, actualización de UI y lógica de layout. Dificulta pruebas unitarias y evolución.
- **Estado y contexto global implícito:** En `state/hooks.py`, la pila de contexto reactivo es global (`_context_stack`). En `context/__init__.py`, los contextos se registran en un diccionario de clase (`Context._registry`). Riesgo de fugas o interferencia entre tests si no se aísla correctamente.
- **Callbacks con varias responsabilidades** en componentes (SidebarAdmin, CommandPalette) y en core_legacy (handlers que actualizan estado, UI y negocio en uno).

La base (core nueva, router, state protocol, contextos) es sólida; el mayor riesgo y deuda están en la convivencia de las dos cores, la exportación incorrecta respecto a tests/demo y el tamaño/acoplamiento de core_legacy.

---

## 2. Lista priorizada de problemas

### Impacto ALTO (errores actuales o bloqueantes)

| # | Problema | Tipo | Dónde |
|---|-----------|------|--------|
| 1 | **Tests de FletPlusApp fallan:** importan `FletPlusApp` de `fletplus.core` (nueva API) pero ejercitan la API legacy (page, routes, `build()`, `theme`, etc.). Los 6 tests dan `AttributeError`. | Error actual | `tests/test_fletplus_app.py` importa `fletplus.core`; la API usada es la de `core_legacy`. |
| 2 | **Demo incompatible con la API expuesta:** `fletplus_demo/app.py` usa `from fletplus import FletPlusApp` y llama `FletPlusApp(page, routes=..., sidebar_items=...)`. El `FletPlusApp` que expone el paquete es el de `fletplus.core`, que tiene firma `(layout, state=..., on_start=..., ...)`. La demo no puede funcionar con ese constructor sin cambiar imports o código. | Error latente | `fletplus_demo/app.py`; `fletplus/__init__.py` (LAZY_IMPORTS apunta a `fletplus.core`). |
| 3 | **Inyección de estado en `page`:** En core_legacy se hace `setattr(self.page, "state", self.state)` y luego `setattr(self.page, "contexts", self.contexts)`. Mutar el objeto `page` de Flet acopla la app al contrato implícito “page tiene state/contexts” y dificulta tests y reutilización con otra página. | Riesgo arquitectónico | `fletplus/core_legacy.py` (__init__ y _activate_contexts). |
| 4 | **Limpieza en `__del__`:** Tanto `core_legacy.FletPlusApp` como `CommandPalette` usan `__del__` para dispose/unsubscribe. El orden de destrucción de objetos en Python no está garantizado; puede haber intentos de usar objetos ya destruidos o recursos ya liberados. | Riesgo / deuda | `core_legacy.py` (__del__), `command_palette.py` (__del__). |

### Impacto MEDIO (riesgos futuros y deuda técnica)

| # | Problema | Tipo | Dónde |
|---|-----------|------|--------|
| 5 | **Core legacy como “god class”:** Una sola clase inicializa y orquesta router, theme, sidebar, command palette, shortcuts, responsive, contextos, preferencias, animación, ventanas, navegación móvil/tablet/desktop. Cualquier cambio en una de estas áreas toca el mismo archivo; testing unitario de una pieza requiere montar gran parte del resto. | Deuda técnica | `fletplus/core_legacy.py`. |
| 6 | **Callbacks con múltiples responsabilidades:** Ejemplos: `_handle_route_change` actualiza contenido, índice de navegación, cierra menú flotante y llama `page.update()`; `_toggle_theme` cambia tema, actualiza header, reconstruye navegación flotante y aplica layout. Mezcla lógica de negocio, estado y UI en un mismo handler. | Anti‑patrón | `core_legacy.py` (_handle_route_change, _toggle_theme, _apply_layout_mode, etc.). |
| 7 | **SidebarAdmin:** `_select_item` actualiza estado interno, llama `on_select` y hace `e.control.page.update()`. Depende de `theme_context.get()` en el constructor; si no hay proveedor activo, lanza o usa fallback. Acoplamiento a contexto global en tiempo de construcción. | Acoplamiento | `fletplus/components/sidebar_admin.py`. |
| 8 | **CommandPalette:** `_execute` ejecuta el comando, cierra el diálogo y hace `page.update()`; además suscribe a `locale_context` y `user_context` en `_setup_context_bindings`. Si no hay proveedor activo, `subscribe` lanza; el `except LookupError` hace fallback pero deja el flujo frágil ante otros errores. | Acoplamiento / responsabilidades | `fletplus/components/command_palette.py`. |
| 9 | **Estado global en hooks reactivos:** `_context_stack` en `state/hooks.py` es una lista a nivel de módulo. Cualquier uso de `@reactive` / `use_state` / `use_signal` dentro de ese módulo depende de que la pila esté bien configurada; tests que usen hooks en paralelo o en orden inesperado pueden interferir. | Riesgo | `fletplus/state/hooks.py`. |
| 10 | **Context._registry:** Los contextos se reutilizan por nombre vía `Context._registry`. Correcto para singletons, pero si en tests se crean contextos con el mismo nombre en distintos escenarios, podrían compartir estado no deseado. | Riesgo (menor si los tests aíslan bien) | `fletplus/context/__init__.py`. |
| 11 | **Excepciones tragadas en notificación de estado:** En `core/state.py`, `AppState.notify()` hace `except Exception: logger.exception(...)` y sigue. El suscriptor que falla no rompe a los demás, pero el flujo que disparó el cambio (p. ej. un set) no recibe el error; el estado puede quedar inconsistente respecto a la UI. | Comportamiento / observabilidad | `fletplus/core/state.py` (notify). |

### Impacto BAJO (mejorable)

| # | Problema | Tipo | Dónde |
|---|-----------|------|--------|
| 12 | **Nomenclatura “State” vs “Store”:** El paquete expone tanto `State` (core: AppState key-value) como `Store` (state: otro modelo). Usuarios pueden confundir cuándo usar cada uno; la documentación podría aclarar el rol de cada uno. | Claridad API | `fletplus/__init__.py`, docs. |
| 13 | **Router.observe:** El callback de `observe` recibe `(RouteMatch, ft.Control)`. El router así conoce el tipo de control Flet; para un núcleo “desacoplado” sería más limpio que el router notifique solo el match y que el compositor de UI viva fuera. | Acoplamiento bajo | `fletplus/router/router.py`. |
| 14 | **Múltiples `except Exception` con solo log:** Varios módulos capturan `Exception` y solo registran el error (core/app.py _safe_page_update, core_legacy en dispose/cleanup, etc.). Reduce ruido pero puede ocultar fallos que convendría propagar o marcar de otra forma en entornos de desarrollo. | Operación / depuración | Varios (core, core_legacy, components, etc.). |

---

## 3. Recomendaciones: qué revisar o arreglar primero

1. **Alinear tests y API pública (prioridad inmediata)**  
   - Opción A: Hacer que los tests que ejercitan la app “completa” importen `FletPlusApp` desde `fletplus.core_legacy` (y dejar claro en comentarios/docs que esos tests son para la Core legacy).  
   - Opción B: Mantener `fletplus.core` como API principal y añadir tests que usen la nueva API (layout + state + run); los tests actuales de “app con sidebar/routes” moverlos a un módulo que importe explícitamente desde `core_legacy`.  
   Objetivo: que la batería de tests pase y que quede explícito qué API prueba cada grupo.

2. **Aclarar y documentar la API de entrada**  
   - Decidir qué se considera “recomendado” para nuevas apps: Core nueva (`fletplus.core`) o Core legacy (`fletplus.core_legacy`).  
   - Si la recomendación es la Core nueva: actualizar la demo para usar `core` (layout + state) o una pequeña capa de compatibilidad; si la recomendación es la legacy, documentar que para “app con sidebar y rutas” se use `from fletplus.core_legacy import FletPlusApp` y, si se desea, exponer un alias o un único punto de entrada documentado (por ejemplo en README y docs/app.md).

3. **Reducir dependencia de mutar `page`**  
   - Evitar `setattr(page, "state", ...)` y `setattr(page, "contexts", ...)` como contrato de uso. Alternativas: inyectar estado/contextos en un objeto de aplicación que los componentes reciban por parámetro o por un contexto ya existente (theme_context, etc.), de modo que no sea necesario tocar `page` para “estado de app”.

4. **Sustituir limpieza en `__del__` por API explícita**  
   - En core_legacy y CommandPalette, no depender de `__del__` para dispose/unsubscribe. Exponer `dispose()` (o similar) y documentar que el llamador debe invocarlo (p. ej. al cerrar la página o al dejar de usar el componente). Los tests ya llaman `app.dispose()`; asegurar que CommandPalette también tenga un método explícito de limpieza y que se use desde el contenedor (p. ej. desde core_legacy en su `dispose()`).

5. **Preparar a medio plazo la división de core_legacy**  
   - Sin reescribir todo: identificar bloques (navegación, tema, comandos, responsive, contextos) y extraer servicios o helpers que reciban `page` o dependencias mínimas, de forma que la clase principal orqueste pero no contenga toda la lógica. Así se podrán testear porciones (p. ej. “solo navegación” o “solo preferencias de tema”) sin montar la app completa.

6. **Extraer lógica de callbacks**  
   - En handlers que hoy hacen “actualizar estado + decidir qué mostrar + actualizar UI”, extraer al menos la parte “qué mostrar” o “qué ruta/index” a funciones puras o a un pequeño módulo de “navegación” o “layout”, y que el callback solo llame a esa función y luego actualice estado/UI. Esto mejora testabilidad y reduce el tamaño de los callbacks.

---

## 4. Qué NO tocar todavía (y por qué)

- **No unificar aún Core nueva y Core legacy en una sola implementación.** Son dos modelos de uso distintos (declarativo con layout+state vs imperativo con page+routes). Unificar requería un diseño claro de compatibilidad o migración; es mejor primero estabilizar tests y documentación y luego, si se quiere, plantear una capa de compatibilidad o un único punto de entrada bien definido.

- **No refactorizar en profundidad el router ni los contextos.** Funcionan y están relativamente acotados. Cambiar el contrato del router o de los contextos tendría impacto en muchos sitios; mejor abordar eso cuando se decida una evolución explícita de la API.

- **No eliminar ni reescribir los backends opcionales (Cython/Rust).** La estrategia de fallback a Python puro es razonable; tocar eso solo si hay un objetivo concreto de rendimiento o mantenibilidad.

- **No cambiar aún la nomenclatura masiva (State vs Store, etc.).** Es deuda de claridad, no un bug. Conviene documentar primero el uso recomendado y, si más adelante se hace un major version, considerar renombrar o alias.

- **No proponer refactors detallados de cada callback en este documento.** La revisión prioriza problemas y direcciones; los refactors concretos (qué función extraer, qué parámetros) se pueden hacer en pasos incrementales cuando se aborde cada componente.

---

## 5. Suposiciones explícitas

- Se asume que la intención del proyecto es mantener tanto la Core nueva (desacoplada) como la legacy durante un tiempo, con la nueva como base recomendada a largo plazo y la legacy para apps “completas” con sidebar y rutas ya montadas.
- No se ha revisado a fondo el código Cython/Rust ni los templates CLI; la revisión se centra en el código Python de la librería y en la integración entre módulos.
- La evaluación de “qué no tocar” asume que no hay requisitos inmediatos de breaking change (p. ej. una v2 que elimine la legacy); si los hubiera, algunas de esas recomendaciones podrían adelantarse.
- Se asume que la demo (`fletplus_demo`) debe poder ejecutarse con la API que el proyecto recomienda en README/docs; por eso la incoherencia entre “FletPlusApp” expuesto y la demo se considera un problema a resolver.

---

*Documento generado a partir de revisión de estructura del proyecto, core, core_legacy, state, context, router, componentes (sidebar, command_palette), hooks, tests y documentación existente.*
