# Estilo de enlaces en documentación

Guía corta para evitar regresiones y mantener una convención única de enlaces.

## Convención única (README en raíz)

Para enlaces desde `README.md` hacia archivos dentro de `docs/`, usa siempre:

1. **Enlace principal relativo desde la raíz**: `docs/<archivo>.md`.
2. **Enlace alternativo opcional de GitHub**: `gh-doc-*` apuntando a `https://github.com/<org>/<repo>/blob/main/docs/<archivo>.md`.

Ejemplo:

```md
- [CLI][doc-cli] ([GitHub][gh-doc-cli])

[doc-cli]: docs/cli.md
[gh-doc-cli]: https://github.com/FletPlus/FletPlus/blob/main/docs/cli.md
```

## Reglas rápidas

- En `README.md`, evita usar rutas sin prefijo (`cli.md`, `tooling.md`, etc.).
- En archivos dentro de `docs/` (distintos de `README.md`), usa enlaces relativos normales (`components.md`, `tooling.md#ancla`).
- Si cambias un título que define un ancla, revisa también los enlaces `#ancla` asociados.
- No publiques artefactos de tooling en el contenido final: elimina marcas automáticas como `【F:...】`, `†L...` u otros fragmentos de citación interna antes de hacer merge.
- Si necesitas mencionar origen de implementación en docs públicas, usa texto normal o enlaces Markdown estándar a rutas del repo (por ejemplo `../fletplus/cli/main.py`).

## Validación recomendada

Antes de publicar, valida con:

```bash
python -m mkdocs build --strict
```
