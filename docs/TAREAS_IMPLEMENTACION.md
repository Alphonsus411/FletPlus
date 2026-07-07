# Tareas estructuradas para implementación (post-revisión)

## Objetivo
Cerrar fisuras detectadas en robustez, calidad continua y mantenimiento de documentación.

## Bloque 1 — Robustez de API y compatibilidad
- [ ] **T1.1** Definir política oficial de uso entre `core` y `core_legacy` en README/docs.
- [ ] **T1.2** Etiquetar pruebas por dominio (core moderno vs legacy) para evitar regresiones por imports cruzados.
- [ ] **T1.3** Añadir casos de compatibilidad mínimos para APIs históricas con mensajes de deprecación claros.

## Bloque 2 — Calidad de tests
- [ ] **T2.1** Revisar tests que consumen componentes con API evolucionada (`ResponsiveContainer`, layouts, etc.).
- [ ] **T2.2** Añadir tests de regresión para inicializaciones parciales de `ThemeManager` (fallbacks defensivos).
- [ ] **T2.3** Integrar una fase de “smoke-tests” rápida para PRs y dejar la suite completa para quality/perf.

## Bloque 3 — CI/CD GitHub Actions
- [x] **T3.1** Añadir validación automática de workflows (parseo YAML + lint de actions).
- [x] **T3.2** Versionar matriz de Python en un único origen (mantener `reusable-quality.yml` como fuente de verdad).
- [ ] **T3.3** Publicar en la documentación interna una tabla de checks obligatorios por tipo de rama.

## Bloque 4 — Documentación técnica
- [ ] **T4.1** Corregir anchors rotos reportados por MkDocs (ej. `index.md#gestion-de-estado-reactivo`).
- [ ] **T4.2** Incluir en `nav` páginas huérfanas útiles (`REVISION_INGENIERIA_2025.md`, `pyrust-auto.md`) o moverlas a sección interna.
- [ ] **T4.3** Mantener `informe_tests.md` como bitácora viva de calidad por iteración.

## Bloque 5 — Endurecimiento operativo
- [ ] **T5.1** Añadir guía de resolución rápida para dependencias faltantes en entornos de CI local.
- [ ] **T5.2** Documentar política de manejo de excepciones defensivas (dónde loggear y dónde propagar).
- [ ] **T5.3** Definir checklist de release con pruebas mínimas + docs build + seguridad.

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
- [ ] **A1. Contrato de `Page.window` y dimensiones**
  - Verificar en tests que el contrato soporte `Page.window.width/height` cuando `Page.width/height` no estén definidos como atributos de clase.
  - Añadir casos de regresión para evitar falsos negativos por cambios de API en Flet.
- [ ] **A2. Eliminar usos de API deprecada de `padding`**
  - Migrar `ft.padding.symmetric(...)` a `ft.Padding.symmetric(...)` en componentes interactivos.
  - Ejecutar suite enfocada en contratos Flet para confirmar ausencia de warnings deprecados en rutas críticas.
- [ ] **A3. Revisión de alias legacy opcionales**
  - Validar que `enable_compat_patches()` no silencie errores relevantes y mantener compatibilidad hacia atrás sin romper apps nuevas.

### Bloque B — Bugs funcionales y robustez
- [ ] **B1. Cobertura de componentes responsive con contratos mínimos de `Page`**
  - Revisar componentes que leen `page.width/page.height` para asegurar fallback robusto.
  - Priorizar `responsive_*`, `adaptive_*` y layouts con `on_resize`.
- [ ] **B2. Endurecimiento de errores silenciosos (`except Exception: pass`)**
  - Clasificar por criticidad los puntos donde se ignoran excepciones.
  - Reemplazar por excepciones específicas o logging controlado cuando aplique.

### Bloque C — Seguridad operacional
- [ ] **C1. Subprocess hardening**
  - Revisar entradas que llegan a `safe_subprocess` y asegurar validación de comandos/argumentos en capas llamadoras.
  - Documentar explícitamente el modelo de amenaza para comandos CLI.
- [ ] **C2. Política Bandit y excepciones justificadas**
  - Añadir anotaciones justificadas (`# nosec`) solo donde el riesgo esté mitigado y auditado.
  - Mantener cero hallazgos Medium/High y reducir Low no accionables.

### Bloque D — Validación continua
- [ ] **D1. Pipeline mínimo de auditoría local**
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
- [ ] **F85-C3. Dependencias locales de validación**: asegurar que entornos de desarrollo instalan `requirements-dev.txt` antes de ejecutar checks que importan `yaml`.

### Bloque F85-D — Validación
- [x] **F85-D1. Ejecutar contrato Flet 0.85.x**: `FLET_MATRIX_EXPECTED_MINOR=0.85 python -m pytest tests/test_flet_version_matrix.py tests/test_flet_compat.py tests/test_flet_api_contracts.py -q`.
- [x] **F85-D2. Ejecutar drift check**: `python tools/check_flet_target_drift.py`.
- [ ] **F85-D3. Ejecutar contrato CI completo**: `python tools/check_ci_workflow_contract.py` requiere dependencias dev instaladas (`PyYAML`).

