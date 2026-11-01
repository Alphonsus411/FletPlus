# Informe de tests y revisión técnica

> Bitácora viva: cada iteración añade una entrada fechada al final, sin reescribir las anteriores. El histórico inicial se conserva tal cual se documentó en su momento.

## Paso a paso ejecutado
1. Ejecuté la suite completa inicial:
   - `python -m pytest -q`
2. Identifiqué y corregí tres fallos:
   - Test legacy importando la app de core moderno.
   - Test de `ResponsiveContainer` usando API antigua.
   - Fusión de tokens sin `palette_tokens` inicializado en harness y fallback defensivo en `ThemeManager`.
3. Re-ejecuté tests focalizados:
   - `python -m pytest -q tests/test_core_logging.py tests/test_layouts.py tests/test_token_merge_layers.py`
4. Re-ejecuté la suite completa:
   - `python -m pytest -q`
5. Revisé dependencias críticas de suites de CI:
   - `python tools/check_test_dependencies.py --suite unit --suite cli --suite websocket`
6. Validé sintaxis YAML de workflows de GitHub Actions:
   - script Python con `yaml.safe_load` sobre `.github/workflows/*.yml`
7. Verifiqué que la documentación compila:
   - `python -m mkdocs build --strict --site-dir /tmp/fletplus-site`

## Resultado final
- Suite completa:
  - **304 passed**
  - **15 skipped**
  - **4 deselected**
- Workflows:
  - Archivos YAML válidos y parseables.
  - Estrategia actual coherente (`qa.yml`/`quality.yml` como wrappers y `reusable-quality.yml` como fuente única de QA).
- Documentación:
  - Compila correctamente en modo estricto.
  - Se reportan avisos informativos de navegación/anchors para mejora continua.

## Bugs/fisuras detectadas y corregidas
1. `tests/test_core_logging.py`
   - El test verificaba un método de la app legacy (`_load_route`) importando la app moderna.
   - Se ajustó el import al módulo correcto (`fletplus.core_legacy`).
2. `tests/test_layouts.py`
   - El test usaba una firma antigua de `ResponsiveContainer` (`breakpoints=` directo) y `init_responsive()`.
   - Se migró al contrato vigente: `styles=ResponsiveStyle(...)` + `build(page)`.
3. `fletplus/themes/theme_manager.py`
   - Se reforzó `_refresh_effective_tokens` con fallback defensivo cuando `_palette_tokens` aún no existe.

4. `tests/devtools/test_server.py`
   - Los tests usaban solo `additional_headers` (API de websockets reciente), incompatible con la versión fijada (`websockets>=13,<14`) en el entorno de desarrollo.
   - Se añadió helper de compatibilidad para usar `additional_headers` o `extra_headers` según la firma disponible de `websockets.connect`.

## Estado
- El repositorio queda con tests estables bajo el estado actual del código.
- CI/CD y docs quedan revisados y validados con checks ejecutables.

---

## Iteración 2026-11-01 — Cierre de pendientes (T1.2, T1.3, T2.3, T3.3)

### Cambios aplicados
1. **T1.2 — Etiquetado por dominio**: markers `domain_core`/`domain_legacy` en `pytest.ini` y contrato estático por AST en `tests/test_domain_isolation_contract.py`.
2. **T1.3 — Deprecación de APIs históricas**: `DEPRECATED_ALIASES` y `warnings.warn(DeprecationWarning, ...)` en `fletplus/__init__.py` para `FloatingMenuOptions` y `ResponsiveNavigationConfig`. `FletPlusApp` queda sin aviso por ser el contrato público oficial. Tests añadidos en `tests/test_public_api_entrypoints.py`.
3. **T2.3 — Fase smoke para PRs**: scope `smoke` en `tools/qa.sh`, job `smoke-tests` con input `test-scope` en `reusable-quality.yml`; `qa.yml` fija `smoke` y `quality.yml` fija `full`.
4. **T3.3 — Checks por tipo de rama**: tabla “Checks obligatorios por tipo de rama” en `docs/tooling.md`, derivada de los workflows versionados.

### Comandos y resultados
| Comando | Resultado |
| --- | --- |
| `python -m pytest tests/test_public_api_entrypoints.py tests/test_domain_isolation_contract.py -q` | 12 passed, 1 failed (ambiental) |
| `python -m pytest -q tests/test_all.py tests/test_domain_isolation_contract.py tests/test_public_api_entrypoints.py tests/test_workflow_validation_contract.py` (selección del scope `smoke`) | 27 passed, 1 failed (ambiental) |
| `python tools/check_github_workflows.py` | OK: 5 workflows validados |
| `python tools/check_bandit_command_sync.py` | OK: Bandit alineado y reusable delega en `tools/qa.sh` |
| `python tools/check_ci_workflow_contract.py` | OK: contrato CI/docs validado |

### Deuda ambiental detectada (preexistente, no atribuible a esta iteración)
- El intérprete local tiene `flet==0.28.3` mientras el baseline contractual del proyecto es `>=0.80`. Esto provoca `AttributeError: type object 'BorderRadius' has no attribute 'all'` en `fletplus/core_legacy.py:326` y fallos equivalentes en `tests/test_padding_migration_contract.py`.
- `mkdocs build --strict` no es ejecutable en local por falta del plugin `include-markdown`; la validación de documentación queda cubierta por CI (`cross-platform-lightweight` y `docs.yml`).

---

## Iteración 2026-11-01 (continuación) — Cierre de Bloque 5 (T5.2, T5.3)

### Cambios aplicados
1. **T5.2 — Política de excepciones defensivas**: sección “Política de manejo de excepciones defensivas” en `docs/tooling.md`, con criterio de decisión, tabla de categorías (fallback de extensión nativa, frontera de UI, transacción del router, arranque de la app, normalización de atributos, comparación tolerante) e inventario verificado de sitios reales en `fletplus/`.
2. **T5.3 — Checklist de release**: sección “Checklist de release de FletPlus” en `docs/tooling.md` (pruebas mínimas, build de documentación, seguridad/estática y consistencia/cierre), con comandos reales de `tools/qa.sh`, `mkdocs build --strict` y el scope `static-security`.

### Comandos y resultados
| Comando | Resultado |
| --- | --- |
| `python tools/check_ci_workflow_contract.py` | OK: contrato CI/docs validado (workflow reusable por jobs, tools/qa.sh, nox y docs sincronizados) |
| `python tools/check_github_workflows.py` | OK: 5 workflows validados (YAML + reglas GitHub Actions) |

### Notas
- Ambas secciones documentan contratos ya existentes en el código (no introducen cambios de runtime); su validación funcional corresponde a CI.
- `mkdocs build --strict` sigue sin poder ejecutarse en local por la deuda ambiental del plugin `include-markdown`; los enlaces internos nuevos usan anchors de la misma página, cubiertos por CI.

---

## Iteración 2026-11-01 (continuación) — Cierre de Bloque B (B2), Bloque C (C2) y Bloque D (D1)

### Cambios aplicados
1. **B2 — Endurecimiento de errores silenciosos**: clasificados y endurecidos ~25 sitios según la política de `docs/tooling.md`. `except Exception` → `except ImportError` en cargas de extensiones nativas opcionales (`router/router_pr.py`, `storage/session.py`, `storage/local.py`); `except Exception` → `except (AttributeError, TypeError)` en normalización de atributos dependiente de la versión de Flet (`icons/__init__.py` ×2, `styles/style.py`, `utils/accessibility.py`); comentarios justificativos con `# pragma: no cover` en los sitios que conservan captura amplia (shims `*_rs`, `smart_table.py`, `responsive_grid.py`, `command_palette.py`, `http/client.py`, `http/disk_cache*.py`, `devtools/server.py`, `core_legacy.py`, `themes/theme_manager.py`, `utils/responsive_manager.py`, `state/state.py`, `state/_native.py`).
2. **C2 — Política Bandit**: anotaciones justificadas `# nosec B404` (`utils/safe_subprocess.py:5`, `cli/build.py:9`, `cli/main.py:11`, `desktop/notifications.py:7`) y `# nosec B603` (`utils/safe_subprocess.py:76`/`:98`), todas con motivo verificable. Documentada la política en `docs/tooling.md` §“Política de excepciones Bandit (`# nosec`)” con umbral cero Medium/High y tabla de anotaciones vigentes.
3. **D1 — Pipeline mínimo de auditoría local**: cableado `python tools/check_flet_target_drift.py` en el scope `tests-matrix` de `tools/qa.sh` (+ orden documentado en `docs/tooling.md` y lista de comandos estándar de `README.md`). `bandit` y `pip-audit` ya formaban parte del scope `static-security`; los tests de contrato Flet corren vía `pytest`.
4. **F85-C3 — Dependencias locales de validación**: la suite `unit` del preflight `tools/check_test_dependencies.py` (primer paso del gate `tests-matrix`) ahora valida `yaml`, de modo que un entorno sin `requirements-dev.txt` falla de forma temprana con la instrucción de instalación antes de alcanzar los checks que importan `yaml`. Documentado en `docs/tooling.md` (lista de suites) y `README.md`.
5. **F85-D3 — Contrato CI completo**: `python tools/check_ci_workflow_contract.py` ejecutado con `PyYAML` disponible (vía `requirements-dev.txt`) → OK.

### Comandos y resultados
| Comando | Resultado |
| --- | --- |
| `python -m bandit -c pyproject.toml -r fletplus` | No issues identified (0 hallazgos; antes 6 `Low` no accionables) |
| `python tools/check_bandit_command_sync.py` | OK: Bandit alineado y reusable delega en `tools/qa.sh` |
| `python tools/check_flet_target_drift.py` | OK: workflow/config/docs ya están sincronizados |
| `python tools/check_github_workflows.py` | OK: 5 workflows validados (YAML + reglas GitHub Actions) |
| `python tools/check_ci_workflow_contract.py` | OK: contrato CI/docs validado (workflow reusable por jobs, tools/qa.sh, nox y docs sincronizados) |
| `python -m pytest -q tests/test_optional_backend_import_fallbacks.py tests/test_icons.py tests/test_style.py tests/test_state.py` | 32 passed, 1 failed (ambiental) |
| `python -m pytest -q tests/test_command_palette.py tests/test_command_palette_rs_backend.py tests/test_responsive_manager.py tests/test_responsive_grid.py tests/test_smart_table.py tests/test_router.py tests/test_router_pr_rs_import.py tests/test_public_api_entrypoints.py` | 50 passed, 6 skipped, 8 failed (ambiental) |
| `python tools/check_test_dependencies.py --suite unit --suite cli --suite websocket` | OK: dependencias críticas disponibles (yaml, watchdog, websockets) |
| `python -m pytest -q tests/test_workflow_validation_contract.py tests/test_check_ci_workflow_contract.py tests/test_check_bandit_command_sync.py` | 54 passed |

### Notas
- `pip-audit` no es ejecutable en el entorno local por falta de acceso a red para consultar la base de vulnerabilidades; queda cubierto por CI (scope `static-security`).
- Todos los fallos observados son ambientales (`ft.Border.all`, `ft.Padding.all/symmetric`, `ft.BorderRadius.all` no existen en el `flet` 0.28.3 instalado; baseline exige ≥0.80) y no están relacionados con los cambios aplicados. El test de T1.3 pasa y emite los `DeprecationWarning` esperados.

## Iteración 2026-11-01 (continuación) — Cierre de Bloque 1 del roadmap frontend (T1.1–T1.4)

### Cambios aplicados
1. **T1.1 — Conservación de tokens base en `palette_for_target()`**: contrato verificado y cubierto con `test_frontend_config_palette_for_target_without_overrides_keeps_base_palette` (un target sin overrides devuelve la paleta base y los overrides no se filtran entre targets). El código de `FrontEndConfig.palette_for_target()` ya cumplía el contrato; no se modificó.
2. **T1.2 — Paletas recomendadas por tipo de producto**: matriz producto→preset→paleta→densidad (`landing→solstice/spacious`, `dashboard→fjord/compact`, `admin→metropolis/compact`, `saas→zenith/comfortable`, `ecommerce→citrus/comfortable`, `mobile_app→aurora/comfortable`) documentada en `docs/frontend-projects.md` §“Paletas recomendadas por tipo de producto” y cubierta con `test_frontend_config_product_preset_recommendations_are_registered`.
3. **T1.3 — Tokens semánticos en plantillas CLI**: las 5 plantillas (`app`, `web`, `desktop`, `mobile`, `fullstack`) declaran `brand`, `surface_soft`, `focus_ring`, `success` y `error` en `DEFAULT_CUSTOM_TOKENS["colors"]`; `_frontend_preset_context` de `fletplus/cli/main.py` inyecta los mismos valores vía `custom_tokens_repr`. Añadido `test_frontend_templates_expose_semantic_color_tokens` (contrato por plantilla). Ejemplo de `docs/frontend-projects.md` actualizado.
4. **T1.4 — Auditoría de contraste WCAG**: nuevo módulo `fletplus/themes/contrast.py` (`parse_hex_color`, `relative_luminance`, `contrast_ratio` + umbrales `WCAG_AA_TEXT`/`WCAG_AA_UI`), exportado desde `fletplus.themes`. `tests/test_theme_contrast.py` audita las 19 paletas en ambos modos; es **informativa** (reporta vía `UserWarning`, no bloquea CI). Deuda registrada en `docs/frontend-roadmap.md`; sección “Auditoría de contraste (WCAG)” añadida a `docs/themes.md`.

### Comandos y resultados
| Comando | Resultado |
| --- | --- |
| `python -m pytest tests/test_cli_template_contracts.py -q -k "semantic or structure or layout_helpers"` | 19 passed |
| `python -m pytest tests/test_frontend_config.py::test_frontend_config_palette_for_target_without_overrides_keeps_base_palette tests/test_frontend_config.py::test_frontend_config_product_preset_recommendations_are_registered tests/test_cli_template_contracts.py::test_frontend_templates_expose_semantic_color_tokens tests/test_theme_contrast.py -q` | 11 passed, 1 warning |
| `python -m pytest tests/test_theme_manager.py tests/test_theme_tokens.py tests/test_all.py -q` | 22 passed |
| `python -c "import fletplus.themes as t; ..."` | exports lazy resueltos (`contrast_ratio`, `relative_luminance`, `parse_hex_color`) |

### Notas
- Auditoría de contraste: 21 pares por debajo del umbral AA en 14 paletas; el mínimo es `on_primary`/`primary` = 2.74 (`sunset`/light). Patrón dominante: `outline` sobre `surface` (1.84–2.70) y `on_primary` sobre `primary` en paletas claras. Registrado como deuda en el roadmap, sin modificar paletas.
- Persisten 4 fallos ambientales en `tests/test_frontend_config.py` (`module 'flet' has no attribute 'Gradient'`), atribuibles a `flet` 0.28.3 instalado vs baseline ≥0.80; no relacionados con los cambios de este bloque.

## Iteración 2026-11-01 (continuación) — Cierre de Bloque 2 del roadmap frontend (T2.1–T2.4)

**Entorno canónico:** `.\.venv\Scripts\python.exe` (`flet` 0.80.5, dentro del contrato `>=0.80,<0.86`). El intérprete global tenía `flet` 0.28.3 (fuera de contrato) y provocaba los fallos ambientales anteriores; se revirtió el global y se adoptó `.venv` para todos los checks.

### Cambios aplicados
1. **T2.1 — Fallback de dimensiones**: `fletplus/frontend/config.py` lee ahora ancho/alto vía `safe_page_width`/`safe_page_height` (que priorizan `page.window.width/height` → `page.window_width` → `page.width`), con `max_content_width` como fallback. Afecta a `screen_tokens_for_page`, `content_width_for_page`, `orientation_for_page` y `apply_to_page`. Tests en `tests/test_frontend_config.py` (`WindowStub`/`WindowedPage`): prioridad `page.window` sobre `page.width`, fallback legacy `window_width/height`, fallback a configuración y precedencia de `page.width`.
2. **T2.2 — Regresión de orientación y perfiles**: `tests/test_viewport.py` amplía con tests parametrizados de orientación (`portrait`/`landscape`, incluido el cuadrado `600×600`) y de los cuatro perfiles (`mobile`/`tablet`/`desktop` en `DEFAULT_DEVICE_PROFILES`; `large_desktop` con `EXTENDED_DEVICE_PROFILES`), verificando `columns` (4/8/12/16) y el snapshot completo (`viewport_info`: perfil, orientación, densidad).
3. **T2.3 — Patrones por target**: nueva sección "Patrones por target: SafeArea, padding seguro y ancho máximo" en `docs/responsive.md` (detección por capacidades de `ft.SafeArea` con fallback a `safe_mobile_padding`, padding desde `viewport_info`, tabla de presets `page_padding`/`max_content_width`/`spacing`/`layout_density` por destino y uso de `content_width_for_page`/`PageShell`).
4. **T2.4 — Guía de revisión manual**: nueva sección "Revisión manual de breakpoints críticos" en `docs/responsive.md` con tabla de fronteras (`599/600`, `1023/1024`, `1439/1440`, altura `<520`, cuadrado) y checklist de aceptación previo a publicar.
5. **Ejemplo funcional**: `examples/responsive_demo/viewport_density_demo.py` usa ahora `EXTENDED_DEVICE_PROFILES` y observa los cuatro perfiles (`mobile`→`large_desktop`); `examples/responsive_demo/README.md` actualizado.

### Comandos y resultados
| Comando | Resultado |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest tests/test_viewport.py -q` | 24 passed |
| `.\.venv\Scripts\python.exe -m pytest tests/test_viewport.py tests/test_frontend_config.py tests/test_flet_compat.py -q` | 100 passed, 1 warning |
| `.\.venv\Scripts\python.exe -m ruff check tests/test_viewport.py` | All checks passed |

### Notas
- El único warning es informativo (`Fuente local no encontrada para 'Inter'`) y proviene de un fixture de `test_frontend_config.py`, no de los cambios de este bloque.
- El bloque queda cerrado: tests de viewport, docs responsive actualizadas y ejemplo funcional redimensionable para web/escritorio.

## Iteración 2026-11-01 (continuación) — Cierre de Bloque 3 del roadmap frontend (T3.1–T3.4)

### Cambios aplicados
1. **T3.3 — Alineación de spacing/padding con `FrontEndConfig`**: nuevo método `Section.resolve_tokens(page)` en `fletplus/components/frontend_layouts.py`; `Section.build` lo reutiliza y `HeroSection`, `ToolbarSection` y `FooterSection` resuelven su spacing desde `resolve_layout_tokens` (tokens de pantalla, `*_by_device` o `FrontEndConfig`) en lugar de valores hardcodeados (`12`/`24` y `self.spacing or config.spacing`). Padding y ancho máximo ya se resolvían por tokens.
2. **T3.1 — Auditoría de helpers**: tabla helper→responsabilidad→módulo en `docs/frontend-projects.md` §"Auditoría de helpers de layout", cubriendo `resolve_layout_tokens`/`LayoutTokens`, `PageShell`, `Section`, `CardGrid`, `HeroSection`, `ToolbarSection`, `FooterSection`, `content_width_for_page`, `build_content_shell` y `UniversalAdaptiveScaffold`; se documenta la separación contenido (`frontend_layouts.py`) vs navegación (`universal_scaffold.py`).
3. **T3.2 — Patrones oficiales por target**: §"Patrones oficiales por target" en `docs/frontend-projects.md` con los tres patrones y código real (sidebar escritorio con `UniversalAdaptiveScaffold`, nav inferior móvil con `NavigationBar` + `make_navigation_bar_destination`, contenido centrado web con `build_content_shell`/`PageShell`).
4. **T3.4 — Ejemplos de composición**: `examples/frontend_layout_examples.py` añade un estado vacío (`HeroSection` con acción primaria) al `PageShell` junto a hero, toolbar, `CardGrid` y footer.
5. **Tests**: `tests/test_frontend_layouts.py` incorpora 4 pruebas de regresión (spacing interno del hero, spacing de toolbar, spacing+padding de footer y `Section.resolve_tokens`). Total del archivo: 10 tests.

### Comandos y resultados
| Comando | Resultado |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest tests/test_frontend_layouts.py tests/test_layouts.py tests/test_adaptive_layout.py -q` | 24 passed |
| `.\.venv\Scripts\python.exe -m pytest tests/test_frontend_layouts.py -q` | 10 passed |
| `.\.venv\Scripts\python.exe -m pytest tests/test_frontend_layouts.py tests/test_frontend_config.py tests/test_viewport.py tests/test_theme_contrast.py tests/test_cli_template_contracts.py -q` | 104 passed, 2 warnings |
| `.\.venv\Scripts\python.exe -m ruff check tests/test_frontend_layouts.py fletplus/components/frontend_layouts.py examples/frontend_layout_examples.py` | All checks passed |
| `.\.venv\Scripts\python.exe -m py_compile examples/frontend_layout_examples.py` | OK |

### Notas
- Cambio de comportamiento **intencional**: el spacing interno de `HeroSection` por defecto pasa de `12`/`24` fijos a derivarse de `LayoutTokens.spacing` (`spacing` y `spacing × 2`); las apps que fijaban `spacing` explícito mantienen el control mediante `spacing=` o `spacing_by_device=`.
- Los 2 warnings son informativos (fuente `Inter` en un fixture y auditoría de contraste WCAG), sin relación con los cambios.
- El bloque queda cerrado: tests de helpers de layout, docs con patrones por target y layout completo renderizable (plantilla web + `examples/frontend_layout_examples.py`).

## Iteración 2026-11-01 (continuación) — Cierre de Bloque 4 del roadmap frontend (T4.1–T4.4) y corrección de incompatibilidad de `Tooltip`

### Cambios aplicados
1. **T4.1 — Roles tipográficos**: nueva sección "Roles y degradación" en `docs/frontend-projects.md` (tabla rol→uso típico para `display`/`headline`/`title`/`body`/`label`/`caption`, soporte de roles personalizados y orden de degradación).
2. **T4.2 — Carga de fuentes locales**: nueva sección "Carga local, fallbacks y metadatos" en `docs/frontend-projects.md` (registro en `page.fonts`, resolución relativa a `font_assets_base_path`, composición de `fallback_families`, URLs `http(s)`/`data:`, `weights`/`styles` como metadatos, alias `[tool.fletplus.frontend.fonts]` y `UserWarning` si falta un asset).
3. **T4.3 — Degradación de `text_style()`**: `fletplus/frontend/config.py` añade `_TYPOGRAPHY_DEVICE_FALLBACKS` y `_select_typography_variant()`; `resolve_typography()` degrada a la variante de dispositivo más cercana (`large_desktop → desktop → tablet → mobile`) y, en último término, al rol `body`. 3 tests nuevos en `tests/test_frontend_config.py`.
4. **T4.4 — Ejemplo con roles semánticos**: `examples/responsive_typography_example.py` demuestra navegación (`nav_item`), badges (`badge`) y ayudas contextuales (`helper`, rol plano) con una `FontDeclaration` personalizada (`Inter` + fallbacks) y `NavigationBar`.
5. **Corrección de incompatibilidad (crítica)**: `ft.Tooltip(content=..., message=...)` **no es válido en `flet 0.80.5`** — `Tooltip.__init__` solo acepta `message`/`decoration` y `Tooltip` es un objeto de configuración que se asigna a `control.tooltip`, no un contenedor con `content`. Se sustituyó el patrón roto en `fletplus/components/adaptive_app_header.py` (`_wrap_badge`, línea 281) y `fletplus/components/responsive_grid.py` (`_create_tag_control`, línea 1374) por la asignación nativa `control.tooltip = ...`. 3 tests de regresión añadidos (`tests/test_adaptive_app_header.py`, `tests/test_responsive_grid.py`).

### Comandos y resultados
| Comando | Resultado |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest tests/test_frontend_config.py -q` | 38 passed, 1 warning |
| `.\.venv\Scripts\python.exe -m pytest tests/test_adaptive_app_header.py tests/test_responsive_grid.py -q` | 15 passed |
| `.\.venv\Scripts\python.exe -m ruff check tests/test_adaptive_app_header.py tests/test_responsive_grid.py fletplus/components/adaptive_app_header.py fletplus/components/responsive_grid.py examples/responsive_typography_example.py` | All checks passed |
| smoke `main(page)` de `examples/responsive_typography_example.py` | OK (perfiles `mobile` y `large_desktop`) |
| `.\.venv\Scripts\python.exe -m pytest tests/test_theme_palettes.py tests/test_frontend_config.py tests/test_theme_contrast.py tests/test_theme_manager.py tests/test_theme_tokens.py tests/test_theme_manager_signals.py -q` | 67 passed, 2 warnings |
| `.\.venv\Scripts\python.exe -m ruff check fletplus/themes/palettes.py tests/test_theme_palettes.py tests/test_frontend_config.py` | All checks passed |

### Notas
- El warning es informativo (fuente local `Inter` en un fixture).
- **Hallazgo secundario (preexistente) — CORREGIDO:** `FrontEndConfig.palette` por defecto es `"material"`, que **no** estaba en `_PRESET_PALETTES` (19 paletas, ninguna llamada `material`); `apply_to_page()` registraba `ERROR … Failed to apply palette 'material': Palette 'material' is not registered` y no aplicaba ninguna paleta. Afectaba a cualquier configuración que no declare `palette=` (incluidos los ejemplos de Bloques 2–3). No era fatal (degradaba a los tokens por defecto de `ThemeManager`). **Resuelto** registrando la paleta `material` en `fletplus/themes/palettes.py` con equivalentes hexadecimales de los tokens base de `ThemeManager` (misma apariencia; se usa hex y no nombres Material porque `parse_hex_color` de la auditoría WCAG exige hex). 2 tests de regresión añadidos (`tests/test_theme_palettes.py`, `tests/test_frontend_config.py`). La auditoría de contraste añade 2 líneas informativas nuevas (`material/light` y `material/dark`: `success` sobre `surface` = 2.78 < 3) que **no** bloquean el CI.
- El bloque queda cerrado: tests de resolución tipográfica, docs de roles/fuentes y ejemplo funcional con familia personalizada.

## Iteración 2026-11-01 (continuación) — Verificación de la suite completa y diagnóstico del "cuelgue" de pytest

**Entorno canónico:** `.\.venv\Scripts\python.exe` (`flet` 0.80.5, dentro del contrato `[0.80, 0.86)`).

### Diagnóstico: por qué la suite completa parecía colgarse
- Síntoma: `pytest` (suite completa o el subconjunto `tests/devtools tests/examples`) se detenía en `tests/examples/test_minimal_app_smoke.py::test_minimal_app_smoke` sin avanzar; con `-k "not test_minimal_app_smoke"` volvía a estancarse más adelante.
- Causa raíz (confirmada): `DummyPage` de ese test no define `client_storage`, así que `PreferenceStorage` recurre a `_FileBackend` y escribe en `C:\Users\Adolfo\.fletplus\preferences.json`, **fuera del workspace**. El sandbox de ejecución deniega esa escritura; `tempfile.mkstemp()` (`tempfile.py:257`, `except FileExistsError: continue`) recorre entonces sus ~10000 nombres candidatos, cada intento se registra como acceso restringido y el test queda aparentemente colgado durante minutos (el proceso terminó reportando `TRAE Sandbox Error: hit restricted`).
- El mismo test, ejecutado de forma aislada y sin esa ruta denegada, se completa en ~0,75 s → **no es un defecto de FletPlus ni del test**.
- Confirmación de la hipótesis: redirigiendo el backend de fichero dentro del workspace (`FLETPLUS_PREFS_TRUSTED_ROOT` + `FLETPLUS_PREFS_FILE`, ambos bajo el workspace), el subconjunto que se colgaba pasa en 2,50 s.

### Comandos y resultados
| Comando | Resultado |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest tests/devtools tests/examples -q` (prefs redirigidas bajo el workspace) | 28 passed in 2.50s |
| `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short -rf` (suite completa, prefs redirigidas bajo el workspace) | **798 passed, 4 failed, 17 skipped, 4 deselected** in 27.50s |

### Fallos observados (ninguno atribuible a los cambios de esta iteración)
1. `tests/test_dragdrop.py::test_file_drop_zone_rejects_traversal_and_symlinks` — ambiental: `Path.symlink_to` no puede crear symlinks en este entorno (`WinError 87` / `WinError 2`).
2. `tests/test_preferences.py::test_file_backend_rejects_when_target_file_is_symlink` — ambiental (mismo motivo).
3. `tests/test_preferences.py::test_file_backend_rejects_when_parent_is_symlink` — ambiental (mismo motivo).
4. `tests/test_cli_build.py::test_build_uses_tool_fletplus_defaults_and_paths` — **preexistente y reproducible** incluso con `TEMP`/`TMP` redirigidos dentro del workspace: el CLI busca `src/main.py` en lugar de `app/main.py` pese a `[tool.fletplus] app = 'app/main.py'`. `git status` confirma que no hay ningún archivo de `fletplus/cli/` ni de `tests/test_cli_build.py` modificado en esta iteración.

### Notas
- Los 3 fallos de symlink y el de `test_cli_build` son ajenos a los cambios de los Bloques 1–4; el de `test_cli_build` queda registrado como deuda preexistente para análisis fuera de estos bloques.
- La suite completa termina en ~27,5 s cuando el backend de preferencias es escribible; el "cuelgue" era exclusivamente el bucle de `tempfile.mkstemp` contra una ruta denegada por el entorno de ejecución.
- No se modificó `fletplus/utils/preferences.py` ni los tests de preferencias: el comportamiento observado en `test_minimal_app_smoke` es del entorno, no del producto. (El fallo de `test_cli_build` sí era real y se corrigió después; ver la sección siguiente.)

## Iteración 2026-11-01 (continuación) — Corrección del fallo real `test_cli_build`

**Entorno canónico:** `.\.venv\Scripts\python.exe` (`flet` 0.80.5, dentro del contrato `[0.80, 0.86)`).

### Causa raíz
`FullStackBuildContext.from_project` ([fletplus/cli/build.py](file:///c:/Users/Adolfo/PycharmProjects/FletPlus/fletplus/cli/build.py)) aplicaba `[tool.fletplus].app` **solo si** `--app` seguía en su valor por defecto, mediante una comparación textual:

```python
if str(app_path) == "src/main.py" and project_config.app_path is not None:
```

En Windows, `str(Path("src/main.py"))` es `'src\\main.py'` (separador nativo), por lo que la comparación contra el literal POSIX `"src/main.py"` daba `False`. El guardián no reconocía el default, se ignoraba la configuración del proyecto y el CLI buscaba `src/main.py` en vez de la ruta declarada (`app/main.py`). Verificado empíricamente:

```
project_config.app_path = WindowsPath('app/main.py')
str(Path('src/main.py')) = 'src\\main.py'
condición previa (str == 'src/main.py')      -> False
comparación con Path('src/main.py')          -> True
```

### Corrección
Se sustituye la comparación textual por una comparación con semántica de `Path` (normaliza el separador en ambas plataformas):

```python
project_config = _load_fletplus_config(project_dir)
# Comparación con semántica de `Path`: `str(Path("src/main.py"))` usa el
# separador nativo (en Windows, ``src\\main.py``), por lo que una comparación
# textual contra ``"src/main.py"`` no reconocía el default y se ignoraba
# `[tool.fletplus].app`.
if app_path == Path("src/main.py") and project_config.app_path is not None:
    app_path = project_config.app_path
```

### Test de regresión
Añadido `test_project_config_app_overrides_default_entrypoint` en [tests/test_cli_build.py](file:///c:/Users/Adolfo/PycharmProjects/FletPlus/tests/test_cli_build.py): con `[tool.fletplus] app = 'app/main.py'` y `--app` en su valor por defecto, `FullStackBuildContext.from_project` debe resolver `app/main.py`. Cubre específicamente el caso de separador de Windows.

### Comandos y resultados
| Comando | Resultado |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest tests/test_cli_build.py -q` | 29 passed in 2.15s |
| `.\.venv\Scripts\python.exe -m ruff check fletplus/cli/build.py tests/test_cli_build.py` | All checks passed |
| `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short -rf` (suite completa, prefs redirigidas bajo el workspace) | **800 passed, 3 failed, 17 skipped, 4 deselected** in 18.61s |

### Notas
- Los 3 fallos restantes son los ambientales de symlink (no creables en este entorno); ver la lista de la sección anterior. El cuarto fallo anterior (`test_cli_build`) queda resuelto.
- El test preexistente `test_build_uses_tool_fletplus_defaults_and_paths` pasa tras la corrección.
- Los Bloques 1–4 del `frontend-roadmap.md` quedan verificados en verde.

## Iteración 2026-11-01 (continuación) — Bloque 5: Assets e iconografía

**Entorno canónico:** `.\.venv\Scripts\python.exe` (`flet` 0.80.5, contrato `[0.80, 0.86)`).

### Alcance ejecutado (T5.1–T5.6)

| Tarea | Entregable |
| --- | --- |
| T5.1 | Estructura normalizada `assets/{fonts,icons,images}/README.md` en las 5 plantillas CLI (15 marcadores). |
| T5.2 | Constantes `FONTS_DIR`/`ICONS_DIR`/`IMAGES_DIR` en `src/frontend/assets.py` de cada plantilla. |
| T5.3 | Validación liviana pre-build `_warn_missing_critical_assets` en [fletplus/cli/build.py](file:///c:/Users/Adolfo/PycharmProjects/FletPlus/fletplus/cli/build.py). |
| T5.4 | §Assets de [docs/frontend-projects.md](file:///c:/Users/Adolfo/PycharmProjects/FletPlus/docs/frontend-projects.md) (estructura, PWA, escritorio, móvil). |
| T5.5 | Ejemplo funcional [examples/assets_example.py](file:///c:/Users/Adolfo/PycharmProjects/FletPlus/examples/assets_example.py) + [docs/demo.md](file:///c:/Users/Adolfo/PycharmProjects/FletPlus/docs/demo.md). |
| T5.6 | Tests de contrato de plantillas + tests de la validación de assets. |

### Desviación aprobada respecto al plan
El plan inicial proponía `.gitkeep` como marcador de subdirectorio. Verificado empíricamente que `glob('**')` (usado por `[tool.setuptools.package-data] "templates/**"`) **excluye archivos ocultos**, por lo que `.gitkeep` no se empaquetaría. Se usa `README.md` como marcador (documenta además la estructura normalizada).

### Validación liviana de assets (T5.3)
`_warn_missing_critical_assets` se invoca dentro de `FullStackBuildContext.from_project` y emite `UserWarning` **no bloqueante** únicamente cuando el proyecto declara explícitamente la ruta en `[tool.fletplus]` (`icon`, `assets_dir`) y el recurso no existe. Un proyecto que no las declare nunca recibe ruido.

### Tests añadidos (T5.6)
- [tests/test_cli_template_contracts.py](file:///c:/Users/Adolfo/PycharmProjects/FletPlus/tests/test_cli_template_contracts.py): helper `_module_constants` (constantes de módulo vía AST) + `test_frontend_templates_normalize_asset_directories` y `test_frontend_templates_expose_asset_directory_constants` (parametrizados sobre las 5 plantillas).
- [tests/test_cli_build.py](file:///c:/Users/Adolfo/PycharmProjects/FletPlus/tests/test_cli_build.py): `test_build_warns_about_declared_but_missing_icon`, `test_build_warns_about_declared_but_missing_assets_dir`, `test_build_does_not_warn_when_declared_assets_exist` (+ helper `_write_assets_project`).

### Comandos y resultados
| Comando | Resultado |
| --- | --- |
| `.\.venv\Scripts\python.exe -m ruff check tests/test_cli_template_contracts.py tests/test_cli_build.py fletplus/cli/build.py` | All checks passed |
| `.\.venv\Scripts\python.exe -m pytest tests/test_cli_template_contracts.py tests/test_cli_build.py -q` | 73 passed in 2.83s |
| `.\.venv\Scripts\python.exe -m pytest -q` (suite completa, prefs redirigidas bajo el workspace) | **813 passed, 3 failed, 17 skipped, 4 deselected** in 17.88s |

### Notas
- Los 3 fallos restantes son los ambientales de symlink (`tests/test_dragdrop.py`, `tests/test_preferences.py`), no creables en este entorno Windows sin privilegios; permanecen idénticos y ajenos a los cambios del Bloque 5.
- Delta respecto a la iteración anterior: +13 tests (10 de contrato de assets + 3 de validación), coherente con los tests añadidos.
