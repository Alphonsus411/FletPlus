import gc
import weakref

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

    with ctx.provide({"lang": "es", "theme": "light"}):
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


def test_context_reuse_with_compatible_configuration():
    ctx = Context("reuse-compatible", default={"theme": "light"})

    reused = Context("reuse-compatible")
    reused_with_same_default = Context("reuse-compatible", default={"theme": "light"})

    assert reused is ctx
    assert reused_with_same_default is ctx


def test_context_reuse_conflict_on_default():
    existing = Context("reuse-default-conflict", default="es")

    with pytest.raises(ValueError, match="reuse-default-conflict"):
        Context("reuse-default-conflict", default="en")

    assert Context("reuse-default-conflict") is existing


def test_context_reuse_conflict_on_comparer():
    def eq_lower(left, right):
        return str(left).lower() == str(right).lower()

    def eq_upper(left, right):
        return str(left).upper() == str(right).upper()

    existing = Context("reuse-comparer-conflict", comparer=eq_lower)

    with pytest.raises(ValueError, match="reuse-comparer-conflict"):
        Context("reuse-comparer-conflict", comparer=eq_upper)

    assert Context("reuse-comparer-conflict") is existing


def test_context_registry_releases_temporary_contexts():
    name = "temporary-context-gc"

    temporary = Context(name)
    temporary_ref = weakref.ref(temporary)

    del temporary
    gc.collect()

    assert temporary_ref() is None
    assert name not in Context._registry


def test_context_registry_keeps_compatibility_validation_for_live_instances():
    name = "temporary-context-compatible-validation"
    live = Context(name, default="es")

    with pytest.raises(ValueError, match=name):
        Context(name, default="en")

    assert Context(name) is live
