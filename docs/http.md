# Cliente HTTP reactivo

El módulo `fletplus.http` proporciona un cliente asincrónico basado en
`httpx` que facilita la integración entre solicitudes remotas y la UI de
FletPlus. Las señales expuestas permiten mostrar estados de carga,
notificaciones o errores en tiempo real sin escribir *boilerplate*.

## Uso básico

```python
from fletplus import HttpClient

client = HttpClient()

async def cargar_datos():
    respuesta = await client.get("https://api.example.com/items")
    datos = respuesta.json()
    # Actualiza la UI con los datos recuperados
```

El cliente admite el contexto `async with` para garantizar el cierre de la
conexión subyacente:

```python
async with HttpClient() as client:
    respuesta = await client.post(
        "https://api.example.com/items",
        json_data={"nombre": "Elemento"},
    )
```

## Hooks y señales reactivas

Cada petición emite un `RequestEvent` antes de ejecutarse y un
`ResponseEvent` cuando finaliza. Ambos eventos se publican en señales
consultables desde los *hooks* de `fletplus.state`:

```python
from fletplus import HttpClient, use_signal, reactive

client = HttpClient()

@reactive
def render(self):
    peticion = use_signal(client.before_request)
    respuesta = use_signal(client.after_request)
    # `peticion()` y `respuesta()` devuelven el último evento recibido
```

También es posible suscribirse manualmente a los hooks:

```python
def mostrar_spinner(evento):
    print("Lanzando petición", evento.url)

def registrar_resultado(evento):
    if evento.error:
        print("Error", evento.error)
    else:
        print("Estado", evento.status_code)

client.add_before_hook(mostrar_spinner)
client.add_after_hook(registrar_resultado)
```

## Interceptores

Los interceptores permiten modificar solicitudes y respuestas antes de que
lleguen a la aplicación. Son útiles para añadir cabeceras, refrescar tokens o
unificar el manejo de errores.

```python
from fletplus import HttpInterceptor

async def inyectar_token(request):
    request.headers["Authorization"] = "Bearer ..."
    return request

async def validar_respuesta(response):
    response.raise_for_status()
    return response

cliente = HttpClient(interceptors=[
    HttpInterceptor(before_request=inyectar_token, after_response=validar_respuesta)
])
```

Los interceptores se ejecutan en orden de registro para las peticiones y en
orden inverso para las respuestas. Cuando se utiliza caché, las funciones
`after_response` se ejecutan igualmente sobre las respuestas recuperadas del
disco, por lo que pueden mantener la misma lógica de normalización para ambas
fuentes.

```python
from pathlib import Path
from fletplus import DiskCache, HttpClient, HttpInterceptor

cache = DiskCache(Path.home() / ".fletplus" / "http-cache")

def marcar(response):
    contador = int(response.headers.get("X-Intercepted", "0")) + 1
    response.headers["X-Intercepted"] = str(contador)
    return response

cliente = HttpClient(
    cache=cache,
    interceptors=[HttpInterceptor(after_response=marcar)],
)

primera = await cliente.get("https://api.example.com/items")
segunda = await cliente.get("https://api.example.com/items")

assert primera.headers["X-Intercepted"] == "1"
assert segunda.headers["X-Intercepted"] == "2"  # También pasa por el interceptor
```

## Caché local

Cuando se proporciona un `DiskCache`, las respuestas `GET` se almacenan de
forma persistente en disco. El contenido se recupera automáticamente en
solicitudes posteriores, evitando la llamada remota.

```python
from pathlib import Path
from fletplus import DiskCache, HttpClient

cache = DiskCache(Path.home() / ".fletplus" / "http-cache")
cliente = HttpClient(cache=cache)

# La segunda llamada devolverá el valor cacheado.
await cliente.get("https://api.example.com/items")
await cliente.get("https://api.example.com/items")
```

Puede deshabilitarse el almacenamiento por petición con `cache=False`.

## Relación con el almacenamiento reactivo

Cuando necesites recordar tokens de autenticación, cabeceras personalizadas o la
última respuesta consumida por la UI, combina el cliente con un
[`StorageProvider`](storage.md). Las señales expuestas por los proveedores permiten
persistir datos y reenviarlos a controles de Flet sin escribir lógica adicional.
