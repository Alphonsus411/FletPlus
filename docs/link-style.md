# Estilo de enlaces en documentación

Guía corta para evitar enlaces rotos cuando `README.md` se renderiza en dos contextos:

- **GitHub**: `README.md` se abre desde la raíz del repo.
- **MkDocs**: `docs/index.md` incluye `README.md` y los enlaces se resuelven desde `docs/`.

## Regla recomendada (estrategia dual)

Para enlaces hacia archivos dentro de `docs/` en `README.md`, usa referencias duales:

1. Un enlace interno de MkDocs (por ejemplo `cli.md`).
2. Un fallback absoluto a GitHub (`https://github.com/FletPlus/FletPlus/blob/main/docs/cli.md`).

Ejemplo:

```md
- [CLI][doc-cli] ([GitHub][gh-doc-cli])

[doc-cli]: cli.md
[gh-doc-cli]: https://github.com/FletPlus/FletPlus/blob/main/docs/cli.md
```

## Reglas rápidas

- En archivos dentro de `docs/` (distintos de `README.md`), usa enlaces relativos normales (`components.md`, `tooling.md#ancla`).
- Evita enlazar como `docs/*.md` dentro de `README.md`; en MkDocs eso suele resolver a `docs/docs/*.md`.
- Si cambias un título que define un ancla, revisa también los enlaces `#ancla` asociados.
- No publiques artefactos de tooling en el contenido final: elimina marcas automáticas como `【F:...】`, `†L...` u otros fragmentos de citación interna antes de hacer merge.
- Si necesitas mencionar origen de implementación en docs públicas, usa texto normal o enlaces Markdown estándar a rutas del repo (por ejemplo `../fletplus/cli/main.py`).
- Antes de publicar, valida con:

```bash
python -m mkdocs build --strict
```
