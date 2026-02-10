# Informe de tests

## Paso a paso
1. Instalé dependencias de test/QA con:
   - `python -m pip install -e .[dev,qa,cli]`
2. Ejecuté la validación temprana de imports críticos:
   - `python tools/check_test_dependencies.py`
3. Ejecuté la suite completa:
   - `python -m pytest`

## Resultados actuales
- La validación temprana pasó correctamente:
  - `OK: dependencias críticas disponibles (websockets, watchdog).`
- `pytest` recolectó **235 tests**.
- Resultado de ejecución:
  - **221 passed**
  - **15 skipped**
  - **5 failed**

## Fallos detectados (estado actualizado)
1. `tests/test_core_logging.py::test_load_route_invalid_index_logs_error`
   - `AttributeError: 'FletPlusApp' object has no attribute '_load_route'`
2. `tests/test_device_detection.py::test_fletplus_app_platform_tokens`
   - `TypeError: FletPlusApp.__init__() got an unexpected keyword argument 'theme_config'`
3. `tests/test_layouts.py::test_responsive_container_adjusts_style`
   - `TypeError: ResponsiveContainer.__init__() missing 1 required positional argument: 'styles'`
4. `tests/test_router.py::test_router_prefers_static_over_dynamic`
   - `ValueError` por ambigüedad de rutas (`/items/settings` y `/items/<item_id>`)
5. `tests/test_token_merge_layers.py::test_refresh_effective_tokens_uses_merge_layers`
   - `AttributeError: '_MergeHarness' object has no attribute '_palette_tokens'`

## Conclusión
- Se reemplazó el estado previo del informe (errores de recolección por dependencias faltantes) por resultados reales de ejecución completa.
- Ahora el fallo por dependencias faltantes queda explícito y temprano con el script de precheck, y la suite llega a correr en su totalidad.
