# Tareas estructuradas para implementación (post-revisión)

## Objetivo
Cerrar fisuras detectadas en robustez, calidad continua y mantenimiento de documentación.

> Nota frontend: las tareas específicas de paletas, viewport, layout, tipografía, assets, plantillas CLI, componentes y validación se detallan en el [Roadmap frontend](frontend-roadmap.md). Este backlog conserva el historial general y las iniciativas transversales.

## Bloque 1 — Robustez de API y compatibilidad
- [x] **T1.1** Definir política oficial de uso entre `core` y `core_legacy` en README/docs.
- [x] **T1.2** Etiquetar pruebas por dominio (core moderno vs legacy) para evitar regresiones por imports cruzados. — Evidencia: markers `domain_core`/`domain_legacy` en `pytest.ini` y contrato estático en `tests/test_domain_isolation_contract.py`.
- [x] **T1.3** Añadir casos de compatibilidad mínimos para APIs históricas con mensajes de deprecación claros. — Evidencia: `DEPRECATED_ALIASES` + `warnings.warn(DeprecationWarning)` en `fletplus/__init__.py` para `FloatingMenuOptions` y `ResponsiveNavigationConfig`; `FletPlusApp` se mantiene sin aviso por ser el contrato público oficial. Tests en `tests/test_public_api_entrypoints.py`.

## Bloque 2 — Calidad de tests
- [x] **T2.1** Revisar tests que consumen componentes con API evolucionada (`ResponsiveContainer`, layouts, etc.).
- [x] **T2.2** Añadir tests de regresión para inicializaciones parciales de `ThemeManager` (fallbacks defensivos). — Evidencia: `927c863` (2026-02-14), fallback `getattr(self, "_palette_tokens", {})` cubierto por `tests/test_token_merge_layers.py`.
- [x] **T2.3** Integrar una fase de “smoke-tests” rápida para PRs y dejar la suite completa para quality/perf. — Evidencia: scope `smoke` en `tools/qa.sh`, job `smoke-tests` + input `test-scope` en `reusable-quality.yml`, `qa.yml` (`smoke`) y `quality.yml` (`full`); documentado en `docs/tooling.md`.

## Bloque 3 — CI/CD GitHub Actions
- [x] **T3.1** Añadir validación automática de workflows (parseo YAML + lint de actions).
- [x] **T3.2** Versionar matriz de Python en un único origen (mantener `reusable-quality.yml` como fuente de verdad).
- [x] **T3.3** Publicar en la documentación interna una tabla de checks obligatorios por tipo de rama. — Evidencia: sección “Checks obligatorios por tipo de rama” en `docs/tooling.md`, derivada de `.github/workflows/` y validada por `python tools/check_ci_workflow_contract.py`.

## Bloque 4 — Documentación técnica
- [x] **T4.1** Corregir anchors rotos reportados por MkDocs (ej. `index.md#gestion-de-estado-reactivo`). — Evidencia: `927c863` (2026-02-14) corrigió `docs/app.md` a `app.md#hooks-reactivos`; los 8 enlaces con ancla del repo resuelven.
- [x] **T4.2** Incluir en `nav` páginas huérfanas útiles (`REVISION_INGENIERIA_2025.md`, `pyrust-auto.md`) o moverlas a sección interna.
- [x] **T4.3** Mantener `informe_tests.md` como bitácora viva de calidad por iteración. — Evidencia: convención declarada al inicio del documento y entrada fechada “Iteración 2026-11-01” con comandos y resultados.

## Bloque 5 — Endurecimiento operativo
- [x] **T5.1** Añadir guía de resolución rápida para dependencias faltantes en entornos de CI local. — Evidencia: sección “Resolución rápida de dependencias faltantes en CI local” en `docs/tooling.md` (tabla síntoma → dependencia → instalación + preflight `tools/check_test_dependencies.py`).
- [x] **T5.2** Documentar política de manejo de excepciones defensivas (dónde loggear y dónde propagar). — Evidencia: sección “Política de manejo de excepciones defensivas” en `docs/tooling.md`, con criterio de decisión, tabla de categorías (fallback nativo, frontera de UI, transacción del router, arranque, normalización de atributos, comparación tolerante) e inventario verificado de sitios reales en `fletplus/`.
- [x] **T5.3** Definir checklist de release con pruebas mínimas + docs build + seguridad. — Evidencia: sección “Checklist de release de FletPlus” en `docs/tooling.md` (4 bloques: pruebas mínimas, build de documentación, seguridad/estática y consistencia/cierre) con comandos reales de `tools/qa.sh`, `mkdocs build --strict` y el scope `static-security`, más referencia cruzada a la tabla de checks por rama.

---

## Orden recomendado de ejecución
1. Bloque 1
2. Bloque 2
3. Bloque 3
4. Bloque 4
5. Bloque 5

## Criterio de finalización
Se considera completado cuando:
- `pytest -q` esté en verde.
- Workflows de `.github/workflows` validados.
- Documentación compile con `mkdocs build --strict`.
- El estado quede reflejado en `informe_tests.md`.


## Registro interno — cierre de migración Flet 0.80.x

- Estado: ✅ **target `0.80.x` validado oficialmente** (incluyendo el parche más reciente validado en la iteración).
- Evidencia técnica registrada en:
  - `docs/migration-flet-latest.md` (estado oficial + checklist final cerrado).
  - `docs/tooling.md` (contrato vigente y deuda legacy acotada).
  - `tests/test_flet_version_matrix.py` (símbolos sensibles reforzados para componentes/router/tema).
- Decisión: mantener baseline `0.28.x` y target `0.80.x` hasta nueva revisión mensual o evento extraordinario de upstream.

## Plan de implementación (auditoría funcional + seguridad + Flet latest)

### Bloque A — Compatibilidad con Flet 0.80.x/0.81-ready
- [x] **A1. Contrato de `Page.window` y dimensiones**
  - Verificar en tests que el contrato soporte `Page.window.width/height` cuando `Page.width/height` no estén definidos como atributos de clase.
  - Añadir casos de regresión para evitar falsos negativos por cambios de API en Flet.
- [x] **A2. Eliminar usos de API deprecada de `padding`**
  - Migrar `ft.padding.symmetric(...)` a `ft.Padding.symmetric(...)` en componentes interactivos.
  - Ejecutar suite enfocada en contratos Flet para confirmar ausencia de warnings deprecados en rutas críticas.
- [x] **A3. Revisión de alias legacy opcionales**
  - Validar que `enable_compat_patches()` no silencie errores relevantes y mantener compatibilidad hacia atrás sin romper apps nuevas.

### Bloque B — Bugs funcionales y robustez
- [x] **B1. Cobertura de componentes responsive con contratos mínimos de `Page`** — Evidencia: `e02dc65` (2026-02-21), tests de fallback adaptativo y endurecimiento de `adaptive_layout.py`/`universal_scaffold.py`.
  - Revisar componentes que leen `page.width/page.height` para asegurar fallback robusto.
  - Priorizar `responsive_*`, `adaptive_*` y layouts con `on_resize`.
- [x] **B2. Endurecimiento de errores silenciosos (`except Exception: pass`)** — Evidencia: endurecidos ~25 sitios de `fletplus/` según la política de `docs/tooling.md` §“Política de manejo de excepciones defensivas”: `except Exception` → `except ImportError` en cargas de extensiones nativas opcionales (`router/router_pr.py`, `storage/session.py`, `storage/local.py`), `except Exception` → `except (AttributeError, TypeError)` en normalización de atributos dependiente de la versión de Flet (`icons/__init__.py` ×2, `styles/style.py`, `utils/accessibility.py`), y comentarios justificativos con `# pragma: no cover` en los sitios que conservan captura amplia (shims `*_rs`, `smart_table.py`, `responsive_grid.py`, `command_palette.py`, `http/client.py`, `http/disk_cache*.py`, `devtools/server.py`, `core_legacy.py`, `themes/theme_manager.py`, `utils/responsive_manager.py`, `state/state.py`, `state/_native.py`). Verificado con subconjunto de tests: 50 passed, 6 skipped; los 8 fallos son ambientales (`ft.Border.all`, `ft.Padding.all/symmetric`, `ft.BorderRadius.all` no existen en el `flet` 0.28.3 instalado; baseline exige ≥0.80), no atribuibles a los cambios.
  - Clasificar por criticidad los puntos donde se ignoran excepciones.
  - Reemplazar por excepciones específicas o logging controlado cuando aplique.

### Bloque C — Seguridad operacional
- [x] **C1. Subprocess hardening** — Evidencia: `5761e60` y `a17cb8f` (2026-02-21, wrapper seguro + whitelist de entorno) y `6c98f8e` (2026-03-06, modelo de amenaza en `docs/tooling.md` §168).
  - Revisar entradas que llegan a `safe_subprocess` y asegurar validación de comandos/argumentos en capas llamadoras.
  - Documentar explícitamente el modelo de amenaza para comandos CLI.
- [x] **C2. Política Bandit y excepciones justificadas** — Evidencia: `python -m bandit -c pyproject.toml -r fletplus` → “No issues identified” (0 hallazgos; antes 6 `Low` no accionables). Añadidas anotaciones justificadas con motivo e identificador de test: `# nosec B404` en `utils/safe_subprocess.py:5`, `cli/build.py:9`, `cli/main.py:11`, `desktop/notifications.py:7` y `# nosec B603` en `utils/safe_subprocess.py:76`/`:98`. Documentada la política en `docs/tooling.md` §“Política de excepciones Bandit (`# nosec`)” (umbral cero Medium/High, regla de `Low` accionable vs no accionable, prohibición de `# nosec` desnudo y tabla de anotaciones vigentes). `python tools/check_bandit_command_sync.py` → OK.
  - Añadir anotaciones justificadas (`# nosec`) solo donde el riesgo esté mitigado y auditado.
  - Mantener cero hallazgos Medium/High y reducir Low no accionables.

### Bloque D — Validación continua
- [x] **D1. Pipeline mínimo de auditoría local** — Evidencia: `python tools/check_flet_target_drift.py` cableado en el scope `tests-matrix` de `tools/qa.sh:37` (y reflejado en el orden de QA de `docs/tooling.md` y en los comandos estándar de `README.md`); `bandit` y `pip-audit` ya están en el scope `static-security` y los tests de contrato Flet corren vía `pytest`. Evidencia publicada por iteración en `informe_tests.md` §“Cierre de Bloque B (B2), Bloque C (C2) y Bloque D (D1)” con tabla de comandos: drift OK, bandit sin hallazgos, contratos CI/docs OK. `pip-audit` no es ejecutable en local sin red (cubierto por CI).
  - `check_flet_target_drift` + tests de contrato Flet + `bandit` + `pip-audit`.
  - Publicar evidencia resumida por iteración en `informe_tests.md`.

### Orden de ejecución recomendado
1. A1 → A2
2. B1 → B2
3. C1 → C2
4. D1

## Plan estructurado — actualización Flet 0.85.x (2026-07-07)

### Bloque F85-A — Contrato de versión y distribución
- [x] **F85-A1. Detectar última versión publicada**: PyPI informa `flet 0.85.3` como última versión estable disponible.
- [x] **F85-A2. Actualizar rango contractual**: ampliar manifiestos y plantillas a `flet>=0.80,<0.86` para cubrir toda la serie 0.85.x sin perder baseline 0.80.x.
- [x] **F85-A3. Sincronizar matriz CI**: mantener `min-supported` en 0.80.x y elevar `latest-migration-target` a 0.85.x.

### Bloque F85-B — Adaptación funcional de FletPlus
- [x] **F85-B1. Validar APIs sensibles**: confirmar símbolos de navegación, tema, iconos, colores y métodos de `Page` con la matriz de compatibilidad.
- [x] **F85-B2. Revisar capa `flet_compat`**: conservar detección por capacidades para `Page.window`, dimensiones, drawer, screenshots, iconos/colores y controles de navegación.
- [x] **F85-B3. Corregir deuda temporal vencida**: mover la fecha de retirada de fallbacks internos a una ventana futura auditada para evitar documentación obsoleta tras julio de 2026.

### Bloque F85-C — Bugs/fisuras detectadas
- [x] **F85-C1. Drift de versión**: el repositorio seguía apuntando a 0.82.x aunque PyPI ya publica 0.85.3; queda corregido en manifests, CI y docs.
- [x] **F85-C2. Documentación de plantilla desalineada**: el README de la plantilla CLI conservaba `flet>=0.80,<0.83`; queda alineado al rango nuevo.
- [x] **F85-C3. Dependencias locales de validación**: el preflight oficial `tools/check_test_dependencies.py` (`--suite unit`, primer paso del gate `tests-matrix` en `tools/qa.sh`) ahora valida `yaml`, de modo que un entorno sin `requirements-dev.txt` falla de forma temprana con la instrucción de instalación antes de alcanzar los checks que importan `yaml` (`check_github_workflows.py`, `check_ci_workflow_contract.py`). Documentado en `docs/tooling.md` (lista de suites y tabla de resolución rápida) y `README.md`. Evidencia: `python tools/check_test_dependencies.py --suite unit --suite cli --suite websocket` → “OK: dependencias críticas disponibles para suite(s): unit, cli, websocket (yaml, watchdog, websockets)”.

### Bloque F85-D — Validación
- [x] **F85-D1. Ejecutar contrato Flet 0.85.x**: `FLET_MATRIX_EXPECTED_MINOR=0.85 python -m pytest tests/test_flet_version_matrix.py tests/test_flet_compat.py tests/test_flet_api_contracts.py -q`.
- [x] **F85-D2. Ejecutar drift check**: `python tools/check_flet_target_drift.py`.
- [x] **F85-D3. Ejecutar contrato CI completo**: `python tools/check_ci_workflow_contract.py` con `PyYAML` instalado (vía `requirements-dev.txt`) → “OK: contrato CI/docs validado (workflow reusable por jobs, tools/qa.sh, nox y docs sincronizados)”. La dependencia queda garantizada por el preflight `unit` (ver F85-C3).

