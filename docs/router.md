# Router de FletPlus

El módulo [`fletplus.router`](../fletplus/router/__init__.py) incorpora un enrutador declarativo pensado para aplicaciones construidas con Flet. Sus piezas principales son:

- **`Route`**: describe un segmento de navegación. Define el `path`, la función `view` que construye el control asociado y, opcionalmente, un `layout` persistente y rutas hijas.
- **`Router`**: gestiona el árbol completo de rutas, resuelve coincidencias, mantiene el historial (`go`, `replace`, `back`) y notifica cambios a través de `observe`.
- **Coincidencias (`RouteMatch`)**: cada vez que una ruta es activa, el router construye un `RouteMatch` con el contexto (parámetros, ruta completa y padre) que llega a la `view` y a los `layout`.

Los segmentos dinámicos se definen envolviendo el nombre del parámetro entre `<>`. Por ejemplo, `Route(path="/projects/<id>", ...)` creará un nodo que acepta `/projects/123`. En la URL real navegas con el valor (`router.go("/projects/123")`). A lo largo de la guía se referencian parámetros como `:id` para explicar el significado del valor dinámico.

Los layouts persistentes se basan en `LayoutInstance`, una envoltura que conserva la jerarquía superior incluso cuando cambia la vista hoja. Puedes crearlos manualmente o con `layout_from_attribute`, que vincula el contenido de un control Flet a través de un atributo (por ejemplo `content` en un `NavigationView`).

## Declarar rutas básicas

```python
import flet as ft
from fletplus.router import Route, Router


router = Router(
    routes=[
        Route(path="/", name="home", view=lambda match: ft.Text("Inicio")),
        Route(path="/about", name="about", view=lambda match: ft.Text("Acerca de")),
    ]
)

router.go("/")  # activa la vista "Inicio"
```

Cada ruta puede definir `children` para crear jerarquías. El router añade automáticamente los nodos secundarios durante `register` y se encarga de combinar los parámetros provenientes del árbol padre.

## Coincidencias dinámicas

Los segmentos dinámicos permiten capturar valores arbitrarios sin registrar manualmente cada combinación. Los parámetros quedan disponibles en `match.params` o mediante el helper `match.param("id")`.

```python
def project_view(match):
    project_id = match.param("id")
    return ft.Text(f"Proyecto #{project_id}")


router.register(
    Route(
        path="/projects/<id>",
        name="project",
        view=project_view,
    )
)

router.go("/projects/42")
```

Si necesitas más de un parámetro, puedes encadenar segmentos dinámicos (`/users/<user_id>/reports/<report_id>`). Cada coincidencia crea una nueva entrada en `params`.

## Layouts persistentes

Un `layout` envuelve la vista hoja con controles que deberían mantenerse montados entre transiciones, preservando estado (por ejemplo, menús o barras de herramientas).

```python
from fletplus.router import LayoutInstance, layout_from_attribute


def dashboard_layout(match):
    rail = ft.NavigationRail(destinations=[...])
    body = ft.Container(expand=True)
    root = ft.Row([rail, body], expand=True)

    return LayoutInstance(
        root=root,
        _mount=lambda content: setattr(body, "content", content),
    )
```

En la práctica resulta más sencillo apoyarse en `layout_from_attribute` para vincular un contenedor existente:

```python
def main_layout(match):
    scaffold = ft.NavigationView()
    return layout_from_attribute(scaffold, "content")


router.register(
    Route(
        path="/dashboard",
        view=lambda match: ft.Text("Resumen"),
        layout=main_layout,
    )
)
```

Cuando el router activa `/dashboard`, creará (o reutilizará) el layout y montará la vista hoja en el atributo `content`. En cambios posteriores solo se reemplaza la hoja, conservando el estado del shell.

## Ejemplo paso a paso

El siguiente flujo ilustra cómo registrar rutas anidadas, utilizar parámetros estilo `:id` y reaccionar a los cambios mediante `Router.observe`.

1. **Crear el router y definir el layout principal**

    ```python
    from fletplus.router import LayoutInstance, Route, RouteMatch, Router


    page = ft.Page()
    router = Router()

    def app_layout(match: RouteMatch) -> LayoutInstance:
        rail = ft.NavigationRail(selected_index=0, destinations=[...])
        body = ft.Container(expand=True)
        root = ft.Row([rail, body], expand=True)

        return LayoutInstance(
            root=root,
            _mount=lambda content: setattr(body, "content", content),
        )

    router.register(
        Route(
            path="/",
            name="root",
            layout=app_layout,
            view=lambda match: ft.Text("Selecciona un proyecto"),
        )
    )
    ```

2. **Registrar rutas hijas con parámetros**

    ```python
    def project_overview(match: RouteMatch) -> ft.Control:
        project_id = match.param("id")
        return ft.Column([
            ft.Text(f"Proyecto :{project_id}"),
            ft.ElevatedButton("Ver tareas", on_click=lambda _: router.go(f"/projects/{project_id}/tasks")),
        ])

    def project_tasks(match: RouteMatch) -> ft.Control:
        project_id = match.param("id")
        return ft.Text(f"Listado de tareas para :{project_id}")

    router.register(
        Route(
            path="/projects",
            name="projects",
            view=lambda match: ft.Text("Listado de proyectos"),
            children=[
                Route(path="<id>", name="project", view=project_overview),
                Route(path="<id>/tasks", name="project_tasks", view=project_tasks),
            ],
        )
    )
    ```

    Aquí usamos `children` para añadir rutas relativas. Aunque el valor se navega como `/projects/123`, el identificador se consume mediante `match.param("id")`. En el texto del botón mostramos el placeholder `:id` para enfatizar qué parte de la URL es dinámica.

3. **Observar cambios de navegación**

    ```python
    def handle_navigation(match: RouteMatch, control: ft.Control) -> None:
        page.views.clear()
        page.views.append(control)
        page.update()

    unsubscribe = router.observe(handle_navigation)
    router.go("/projects/123")
    ```

    `Router.observe` recibe un callback que se ejecuta después de componer layouts y vistas. Recibes el `RouteMatch` final y el control raíz listo para montarse en la página. Guarda el resultado en `page.views` (o la estructura que prefieras) y renderiza con `page.update()`.

Cuando ya no necesites escuchar cambios, invoca `unsubscribe()`. El router seguirá gestionando el historial (`router.back()`, `router.replace()`) y notificará a los observadores registrados.

---

- [`Route` y `RouteMatch`](../fletplus/router/route.py)
- [`Router`](../fletplus/router/router.py)
- [Ejemplo completo del router](../examples/router_basic.py)
