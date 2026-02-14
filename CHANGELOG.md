# Changelog

## Unreleased

### Changed
- Se fija el contrato público de `FletPlusApp` en `from fletplus import FletPlusApp`, redirigido a la implementación de `fletplus.core_legacy` para preservar compatibilidad.
- Se añade nota de migración: la core desacoplada (`fletplus.core`) con firma `FletPlusApp(layout=..., state=...)` continúa disponible para transición gradual hacia una futura versión mayor.
- Se actualiza la documentación (README y docs) para reflejar un único camino oficial de importación pública.
