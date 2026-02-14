# Nota de mantenimiento de workflows

Los workflows `qa.yml` y `quality.yml` son wrappers de eventos y delegan su ejecución en `reusable-quality.yml`.

## Regla para futuras modificaciones

- Haz cambios de pasos, herramientas, políticas de seguridad o matriz de Python **solo** en `reusable-quality.yml`.
- No dupliques lógica en `qa.yml` ni en `quality.yml`.
