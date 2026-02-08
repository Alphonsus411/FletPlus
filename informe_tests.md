# Informe de tests

## Paso a paso
1. Ejecuté la suite de pruebas con `pytest`.
2. La colección falló por dependencias faltantes (`websockets` y `watchdog`).

## Resultados
- Se recolectaron 220 tests.
- 6 tests se omitieron (skipped).
- 3 errores durante la recolección por módulos faltantes:
  - `websockets` en `tests/devtools/test_server.py`.
  - `watchdog` en `fletplus/cli/main.py` (afecta `tests/test_cli_build.py` y `tests/test_cli_create.py`).

## Propuestas
- Instalar dependencias faltantes en el entorno de test:
  - `pip install websockets watchdog` o agregar a los requisitos de desarrollo si aplica.
- Reintentar `pytest` tras instalar dependencias para validar el estado real de la suite.

## Cambios realizados
- Se creó este informe `informe_tests.md` con los resultados y propuestas.
