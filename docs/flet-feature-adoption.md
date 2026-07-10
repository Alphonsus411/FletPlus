# Matriz de adopción de funcionalidades de Flet

Esta matriz traduce los cambios publicados por Flet en acciones concretas para
FletPlus. Debe revisarse cada vez que cambie `FLET_MATRIX_MINORS` en
`tools/flet_version_matrix_config.py`, porque ese valor define el rango que CI
valida y, por tanto, el conjunto de APIs que FletPlus debe soportar o aislar.

**Estado contractual actual**: `FLET_MATRIX_MINORS = ("0.80", "0.85")`.

Fuentes primarias revisadas:

- Flet 0.83.0: <https://flet.dev/blog/flet-v-0-83-release-announcement/>
- Flet 0.84.0: <https://flet.dev/blog/flet-v-0-84-release-announcement/>
- Flet 0.85.0: <https://flet.dev/blog/flet-v-0-85-release-announcement/>

## Cómo mantener esta matriz

1. Cuando se modifique `FLET_MATRIX_MINORS`, añadir una sección para cada minor
   nuevo dentro del rango objetivo o documentar explícitamente por qué no aplica.
2. Para cada versión de Flet, clasificar los cambios en APIs nuevas, APIs
   deprecadas, cambios de comportamiento y acciones requeridas en FletPlus.
3. Vincular cada acción con un módulo concreto (`fletplus/utils/flet_compat.py`,
   `fletplus/frontend/config.py`, `fletplus/components/*`,
   `fletplus/cli/templates/*`) o con tests de contrato.
4. Ejecutar `python tools/check_ci_workflow_contract.py`; este chequeo falla si
   el rango contractual de `FLET_MATRIX_MINORS` deja de estar reflejado aquí.

## Flet 0.83.x

### APIs nuevas

- `flet.core.validation.V` y validación declarativa con `typing.Annotated` para
  campos de controles declarativos.
- Mejoras de `SharedPreferences` para almacenar `int`, `float`, `bool` y
  `list[str]` además de cadenas.
- Nuevas capacidades en controles existentes: scrollbars configurables y
  `ExpansionPanelList` desplazable.

### APIs deprecadas

- No se identifican deprecaciones públicas nuevas que obliguen a cambiar wrappers
  de FletPlus. La novedad relevante es que las deprecaciones de campos en Flet
  pasan a generar avisos documentales automáticamente.

### Cambios de comportamiento

- El diff de controles usa descriptores `Prop` y comparaciones por contenido para
  value objects; esto reduce trabajo en actualizaciones imperativas y
  declarativas.
- La actualización automática al final de handlers se omite si el handler ya
  llamó explícitamente a `.update()`.
- Los binarios de escritorio y plantillas de build dejan de venir empaquetados en
  wheels de PyPI y se descargan desde GitHub Releases en primer uso.
- Flet alinea valores por defecto de Python con Dart en varios paquetes.

### Acciones requeridas en FletPlus

- `fletplus/utils/flet_compat.py`: añadir helpers solo si FletPlus empieza a
  exponer validación declarativa propia; por ahora documentar la API y evitar
  duplicar `V`.
- `fletplus/frontend/config.py`: revisar cualquier llamada manual a
  `page.update()` durante handlers de configuración para evitar depender de un
  doble render implícito.
- `fletplus/components/*`: revisar componentes con scroll o listas expansibles
  antes de crear wrappers propios para scrollbars o `ExpansionPanelList`.
- `fletplus/cli/templates/*`: mantener la dependencia `flet>=0.80,<0.86` y evitar
  asumir que `flet-desktop` incluye binarios locales en la instalación inicial.
- Tests de contrato: conservar validación de rango en
  `tools/check_ci_workflow_contract.py` y añadir pruebas específicas si se
  introduce un wrapper sobre `SharedPreferences` tipado.

## Flet 0.84.x

### APIs nuevas

- No introduce APIs runtime relevantes para aplicaciones FletPlus; el cambio se
  concentra en documentación y ejemplos.
- Nuevo pipeline documental de Flet basado en CrocoDocs para generar datos API y
  parciales MDX desde docstrings.
- Ejemplos oficiales migrados a proyectos independientes con metadatos para
  galería y descubrimiento por IA.

### APIs deprecadas

- No se reportan deprecaciones públicas que afecten a módulos de FletPlus.

### Cambios de comportamiento

- La documentación oficial de Flet cambia de MkDocs a Docusaurus/CrocoDocs.
- Los ejemplos oficiales dejan de ser snippets sueltos y pasan a proyectos
  autónomos con estructura y metadatos enriquecidos.

### Acciones requeridas en FletPlus

- `fletplus/cli/templates/*`: comparar periódicamente la estructura de las
  plantillas de FletPlus con los ejemplos-proyecto oficiales para mantener una
  experiencia inicial moderna sin copiar metadatos que no use FletPlus.
- Tests de contrato/documentación: mantener enlaces a documentación oficial de
  Flet como URLs estables y preferir referencias de release notes cuando se
  documenten decisiones de compatibilidad.
- `fletplus/components/*`: sin acción runtime; no envolver APIs documentales.
- `fletplus/frontend/config.py`: sin acción runtime; la configuración de app no
  cambia por el nuevo sitio de documentación.

## Flet 0.85.x

### APIs nuevas

- `ft.Router`, `ft.Route` y `ft.use_route_outlet()` para navegación declarativa
  en apps `@ft.component`, incluyendo rutas anidadas, layouts, segmentos
  dinámicos, loaders y `manage_views=True`.
- `ft.use_dialog()` para manejar diálogos como estado reactivo en apps
  declarativas.
- Mejoras de `flet-video`: controles configurables, `Video.take_screenshot()` y
  eventos `on_position_change` / `on_duration_change`.
- `AudioRecorder` añade streaming PCM16 mediante `on_stream` y subida directa con
  `AudioRecorderUploadSettings`.

### APIs deprecadas

- No se identifican deprecaciones públicas nuevas en las release notes de 0.85.x
  que requieran cambios inmediatos en FletPlus.

### Cambios de comportamiento

- El modelo declarativo de Flet se vuelve más completo para navegación y diálogos,
  reduciendo la necesidad de glue code alrededor de `Page.route`, `Page.views` y
  `page.show_dialog()` en apps nuevas.
- Varias correcciones afectan charts, assets web, packaging, orientación móvil y
  otros controles; deben revisarse si un wrapper de FletPlus reproduce workarounds
  antiguos.

### Acciones requeridas en FletPlus

- `fletplus/utils/flet_compat.py`: centralizar detección de disponibilidad de
  `ft.Router`, `ft.Route`, `ft.use_route_outlet()` y `ft.use_dialog()` antes de
  exponer adaptadores compatibles con 0.80.x.
- `fletplus/frontend/config.py`: evaluar si la configuración inicial debe ofrecer
  un modo declarativo que delegue navegación en `ft.Router` cuando esté
  disponible, manteniendo fallback al router actual de FletPlus.
- `fletplus/components/*`: evitar wrappers prematuros para `Video` y
  `AudioRecorder`; añadirlos solo si FletPlus necesita una API transversal de
  media/recording o contratos de accesibilidad propios.
- `fletplus/cli/templates/*`: considerar una plantilla declarativa opcional con
  `ft.Router` una vez que el mínimo soportado suba por encima de 0.85, o incluir
  guards de compatibilidad si se ofrece antes.
- Tests de contrato: añadir casos que verifiquen que los imports condicionales de
  router/dialog no rompen en baseline y que el target de CI ejercita las APIs
  declarativas cuando estén presentes.

## No aplica: funcionalidades de Flet sin wrapper requerido

- Mejoras internas de diffing y comparación por contenido de 0.83.x: son
  optimizaciones del motor de Flet; FletPlus debe beneficiarse indirectamente sin
  añadir abstractions propias.
- Descarga de binarios y plantillas desde GitHub Releases en 0.83.x: afecta a la
  instalación/ejecución de Flet, no a una API pública que FletPlus deba envolver.
  La acción queda limitada a plantillas y documentación de dependencias.
- CrocoDocs, Docusaurus y migración de ejemplos de 0.84.x: son cambios de
  documentación/ecosistema; FletPlus solo necesita mantener enlaces y plantillas
  coherentes.
- Milestones, pre-releases y trazabilidad de releases: útiles para revisión de
  mantenimiento, pero no forman parte del runtime de FletPlus.
- Mejoras puntuales de video/audio de 0.85.x: no aplican hasta que FletPlus
  defina explícitamente componentes multimedia propios; envolverlas ahora
  duplicaría la API nativa de Flet sin valor adicional.

## Estrategias de renderizado FletPlus

FletPlus adopta el build multiplataforma de Flet mediante una capa propia en
`fletplus/rendering/` para no acoplar la API pública a detalles internos del
runtime ni del empaquetado de Flet.

| API/flujo Flet original | Estado en FletPlus | Envoltorio/adopción |
| --- | --- | --- |
| `flet.app()` y montaje de `ft.Page` | Adoptado | `fletplus.core.app.FletPlusApp` acepta una `RenderStrategy` opcional que configura la página antes de construir el layout. |
| Layouts responsive con controles `ft.Container`, `ft.Column` y tokens de pantalla | Envuelto | `WebRenderStrategy`, `DesktopRenderStrategy` y `MobileRenderStrategy` normalizan padding, ancho máximo, spacing y densidad visual para reutilizar los layouts de `fletplus/components/`. |
| `flet build web` | Adoptado con manifiesto FletPlus | `BuildManager` selecciona `WebRenderStrategy` para `BuildTarget.WEB` y el adaptador escribe `render_strategy.json` en staging. |
| `flet build linux/windows/macos` | Adoptado con manifiesto FletPlus | `BuildManager` selecciona `DesktopRenderStrategy` para `BuildTarget.DESKTOP` antes de delegar a Flet. |
| `flet build apk`, `aab` e `ipa` | Adoptado con manifiesto FletPlus | `BuildManager` selecciona `MobileRenderStrategy` para Android/iOS y mantiene las variables `FLETPLUS_METADATA`, `FLETPLUS_ICON` y `FLETPLUS_PACKAGE`. |
| Proyectos full-stack preparados por FletPlus | Extensión propia | `FullStackRenderStrategy` documenta el target `all`/full-stack y convive con la copia de backend, frontend, docs, config, deployment y paquetes compartidos. |

La API pública queda expuesta desde `fletplus.rendering.__init__` con
`RenderStrategy`, `WebRenderStrategy`, `DesktopRenderStrategy`,
`MobileRenderStrategy`, `FullStackRenderStrategy` y `strategy_for_target`.
