# Changelog

## Unreleased

### Changed
- Se fija el contrato público de `FletPlusApp` en `from fletplus import FletPlusApp`, redirigido a la implementación de `fletplus.core_legacy` para preservar compatibilidad.
- Se añade nota de migración: la core desacoplada (`fletplus.core`) con firma `FletPlusApp(layout=..., state=...)` continúa disponible para transición gradual hacia una futura versión mayor.
- Se actualiza la documentación (README y docs) para reflejar un único camino oficial de importación pública.
- Se fija como URL pública canónica del repositorio `https://github.com/FletPlus/FletPlus` y se migra la metadata desde URLs históricas de `Alphonsus411/fletplus`.
- Se documenta la política de versión objetivo de Flet (cadencia de actualización, criterios de rollback y checklist de release) en `README.md` y `docs/tooling.md`, y se adopta como referencia obligatoria para trazabilidad de próximos upgrades.
- Se actualiza la matriz de compatibilidad de Flet en CI al baseline `0.28.x` y target estable `0.80.x`, alineando `reusable-quality.yml`, `tools/flet_version_matrix_config.py` y la política de versión en `README.md`.
- 2026-02-21: salto de target de Flet a `0.80.x` (manteniendo baseline `0.28.x`) por deprecaciones/acoples acumulados en versiones intermedias y para cubrir validación preventiva ante fixes potencialmente breaking en releases críticos.
