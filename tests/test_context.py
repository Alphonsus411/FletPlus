import pytest

from fletplus.context import Context, locale_context, theme_context


class DummyControl:
    def __init__(self):
        self.value = None
        self.updated = False

    def update(self):
        self.updated = True


def test_context_as_context_manager_and_hierarchy():
    ctx = Context("demo-context", default="root")
    assert ctx.get() == "root"

    with ctx as provider:
        assert ctx.get() == "root"
        provider.set("parent")
        assert ctx.get() == "parent"

        with ctx as child:
            # Hereda el valor del proveedor padre hasta que se modifique
            assert ctx.get() == "parent"
            child.set("child")
            assert ctx.get() == "child"

        # Al salir del contexto interno se recupera el valor previo
        assert ctx.get() == "parent"

    # Fuera de cualquier proveedor vuelve el valor por defecto
    assert ctx.get() == "root"


def test_context_binding_updates_controls():
    ctx = Context("binding-context", default="initial")
    control = DummyControl()

    with ctx as provider:
        unsubscribe = ctx.bind_control(control)
        try:
            assert control.value == "initial"
            provider.set("updated")
            assert control.value == "updated"
            assert control.updated is True
        finally:
            unsubscribe()


def test_context_with_explicit_provider_inheritance():
    ctx = Context("explicit-provider", default={"lang": "es"})

    with ctx.provide({"lang": "es", "theme": "light"}) as base:
        assert ctx.get()["theme"] == "light"
        with ctx.provide(inherit=True) as nested:
            data = ctx.get()
            assert data["theme"] == "light"
            nested.set({"lang": "en", "theme": "dark"})
            assert ctx.get()["lang"] == "en"
        assert ctx.get()["theme"] == "light"


def test_locale_context_default_resolution():
    # Sin proveedor activo debe usarse el valor por defecto
    with pytest.raises(LookupError):
        theme_context.get()
    assert locale_context.get(default="es") == "es"
