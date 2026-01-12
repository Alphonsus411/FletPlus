# Reporte de auto-rustyficación

## Entorno y ejecución

1. Instalación de dependencias para Rust:

   ```bash
   pip install .[rust]
   ```

2. Intento de ejecución del wrapper de Make:

   ```bash
   make rustify-auto
   ```

   Falló con el error `Makefile:17: *** missing separator`.

3. Ejecución directa del pipeline con un *entrypoint* ligero:

   ```bash
   tools/pyrust_native_auto.sh \
     --entrypoint tools/pyrust_profile_entrypoint.py \
     --hotspot-limit 25 \
     --min-runtime-pct 2 \
     --profile-limit 50
   ```

4. Verificación del reporte generado en:

   ```
   tools/pyrust_auto_report.md
   ```

## Entry-point usado

Para evitar dependencias de extensiones compiladas durante el perfilado,
se añadió `tools/pyrust_profile_entrypoint.py`, que carga y ejercita módulos
puros (por ejemplo `fletplus/utils/device_profiles.py` y
`fletplus/utils/responsive_breakpoints.py`) usando `importlib`.

## Resultados

- Hotspots seleccionados: 0
- Targets rustificados: 0
- Fallos de recarga: 0
- Runtime total (s): 0.008459
- Muestras de profiling: 50
- Targets analizados: 2106
- Targets transpilados: 2106
- Recargas exitosas: 0

El reporte completo queda disponible en `tools/pyrust_auto_report.md`.

## Acciones adicionales

- No se agregaron módulos nuevos en `[tool.pyrust-native]` porque no se
  detectaron hotspots relevantes en esta ejecución.
