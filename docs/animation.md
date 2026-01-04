# Animaciones coordinadas con FletPlus

FletPlus incluye un sistema ligero para orquestar animaciones entre varios
controles sin necesidad de pasar manualmente referencias entre ellos. La pieza
central es `AnimationController`, un gestor basado en eventos simbólicos que se
apoya en contextos para que cualquier control registrado pueda reaccionar a los
mismos disparadores.

> ℹ️ El contenedor de listeners intenta cargar primero la extensión
> `listeners_pr_rs` compilada con `pyrust-native` para acelerar las operaciones
> (`trigger_many`, filtrado de callbacks muertos y `replay_if_fired`). Si no se
> encuentra, utiliza `listeners_rs` o vuelve de forma transparente al backend
> puro en Python.

## AnimationController y contextos

`FletPlusApp` crea automáticamente una instancia de `AnimationController` y la
expone a través del contexto `animation_controller_context`. Gracias a esto,
cualquier vista o control renderizado dentro de la aplicación puede recuperar
el controlador sin recibirlo explícitamente por parámetros:

```python
from fletplus import animation_controller_context

controller = animation_controller_context.get()
controller.trigger("mostrar_banner")
```

El controlador permite registrar *listeners* asociados a cadenas arbitrarias. Al
invocar `trigger("nombre_del_evento")` se notifican todos los listeners
suscritos. La integración con `FletPlusApp` también dispara automáticamente dos
triggers especiales:

- `"mount"`: se lanza cuando la vista actual termina de montarse.
- `"unmount"`: se lanza justo antes de desmontar la vista activa.

Puedes utilizar estos eventos para iniciar animaciones cuando una pantalla se
muestra por primera vez o para revertir efectos antes de abandonarla. Si
necesitas reutilizar el controlador fuera del ciclo de vida de `FletPlusApp`,
es posible crearlo manualmente y registrar el contexto de forma puntual:

```python
import flet as ft
from fletplus import AnimationController, animation_controller_context

controller = AnimationController()
with animation_controller_context.provide(controller, inherit=False):
    # Dentro del bloque, FadeIn, SlideTransition, etc. pueden resolver el controlador.
    ...
```

## Envoltorios animados disponibles

El módulo `fletplus.animation.wrappers` ofrece varios contenedores que se
suscriben automáticamente al `AnimationController` encontrado en el contexto. En
caso de no localizarlo, puedes pasar una instancia explícita mediante el
parámetro `controller=`.

### FadeIn

`FadeIn` envuelve un control y anima la opacidad entre dos valores. El evento
por defecto es `"mount"`, de manera que al construir la vista el contenido va
apareciendo progresivamente.

```python
import flet as ft
from fletplus import FadeIn

hero = FadeIn(
    ft.Text("Animaciones con FletPlus", size=24, weight=ft.FontWeight.BOLD),
    duration=480,
    curve=ft.AnimationCurve.EASE_IN_OUT,
)
```

Puedes controlar el valor inicial (`start`) y final (`end`), además de cambiar
los triggers mediante los argumentos `trigger` y `reverse_trigger`.

### SlideTransition

`SlideTransition` desplaza el contenido desde un desplazamiento inicial hasta su
posición final. El desplazamiento se define con `ft.transform.Offset`.

```python
subtitle = SlideTransition(
    ft.Text("Coordinadas con AnimationController y contextos"),
    begin=ft.transform.Offset(0, 0.2),
    end=ft.transform.Offset(0, 0),
)
```

Al igual que `FadeIn`, puedes indicar triggers personalizados para iniciar o
revertir la transición.

### Scale

`Scale` aplica una transformación de escala al contenido, ideal para enfatizar
botones o tarjetas. El valor por defecto produce un ligero rebote al montarse la
vista.

```python
pulse_button = Scale(
    ft.ElevatedButton("Lanzar pulso", on_click=lambda _e: controller.trigger("pulse")),
    trigger="pulse",
    reverse_trigger=None,
    begin=ft.transform.Scale(1, 1),
    end=ft.transform.Scale(1.1, 1.1),
)
```

En este ejemplo se utiliza un trigger personalizado (`"pulse"`) que puedes
lanzar desde cualquier control con acceso al `AnimationController`.

### AnimatedContainer

`AnimatedContainer` permite interpolar propiedades arbitrarias de `ft.Container`
mediante diccionarios `begin` y `end`. Resulta útil para cambios de estado más
complejos, como modificar rellenos, colores o bordes simultáneamente.

```python
animated_card = AnimatedContainer(
    ft.Column(
        controls=[
            ft.Text("Panel informativo"),
            ft.Text("Cambia su tamaño con eventos personalizados."),
        ],
        tight=True,
    ),
    duration=360,
    curve=ft.AnimationCurve.EASE_IN_OUT,
    begin={"padding": ft.padding.all(12), "bgcolor": ft.Colors.with_opacity(0.05, ft.Colors.BLUE)},
    end={"padding": ft.padding.all(24), "bgcolor": ft.Colors.with_opacity(0.15, ft.Colors.BLUE)},
    trigger="card_expand",
    reverse_trigger="card_collapse",
)
```

El contenedor aplicará automáticamente los estilos definidos en `begin` al
instanciarse y cambiará a los de `end` cuando reciba el trigger configurado. Si
el trigger inverso es distinto de `None`, la animación revertirá al estilo
inicial.

## Ejemplo completo coordinado

El siguiente fragmento combina todos los envoltorios anteriores y demuestra cómo
activar animaciones desde cualquier parte de la vista utilizando el contexto:

```python
import flet as ft
from fletplus import (
    AnimatedContainer,
    FadeIn,
    FletPlusApp,
    Scale,
    SlideTransition,
    animation_controller_context,
)


def animated_dashboard() -> ft.Control:
    controller = animation_controller_context.get()
    expanded_state = {"expanded": False}

    def toggle_card(_e: ft.ControlEvent) -> None:
        expanded_state["expanded"] = not expanded_state["expanded"]
        if controller:
            controller.trigger("card_expand" if expanded_state["expanded"] else "card_collapse")

    hero = FadeIn(
        ft.Text("Animaciones con FletPlus", size=24, weight=ft.FontWeight.BOLD),
        duration=480,
        curve=ft.AnimationCurve.EASE_IN_OUT,
    )
    subtitle = SlideTransition(
        ft.Text("Coordinadas con AnimationController y contextos"),
        begin=ft.transform.Offset(0, 0.2),
        end=ft.transform.Offset(0, 0),
    )
    pulse_button = Scale(
        ft.ElevatedButton("Lanzar pulso", on_click=lambda _e: controller and controller.trigger("pulse")),
        trigger="pulse",
        reverse_trigger=None,
        begin=ft.transform.Scale(1, 1),
        end=ft.transform.Scale(1.1, 1.1),
    )
    animated_card = AnimatedContainer(
        ft.Column(
            controls=[
                ft.Text("Panel informativo"),
                ft.Text("Cambia su tamaño con eventos personalizados."),
            ],
            tight=True,
        ),
        duration=360,
        curve=ft.AnimationCurve.EASE_IN_OUT,
        begin={"padding": ft.padding.all(12), "bgcolor": ft.Colors.with_opacity(0.05, ft.Colors.BLUE)},
        end={"padding": ft.padding.all(24), "bgcolor": ft.Colors.with_opacity(0.15, ft.Colors.BLUE)},
        trigger="card_expand",
        reverse_trigger="card_collapse",
    )

    toggle = ft.OutlinedButton("Alternar tarjeta", on_click=toggle_card)

    return ft.Column(
        spacing=20,
        controls=[hero, subtitle, pulse_button, animated_card, toggle],
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )


def main(page: ft.Page) -> None:
    page.title = "Demo animaciones FletPlus"
    routes = {"/": animated_dashboard}
    FletPlusApp(page, routes, title="Animaciones FletPlus")


if __name__ == "__main__":
    ft.app(target=main)
```

Consulta el módulo `examples/animation_examples.py` para ejecutar la demo
completa.
