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
