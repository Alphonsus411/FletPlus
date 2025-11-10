import pytest

from fletplus.state import Signal, Store, reactive, use_signal, use_state, watch


class DummyControl:
    def __init__(self):
        self.value = None
        self.updated = 0

    def update(self):
        self.updated += 1


class PageStub:
    def __init__(self):
        self.updated = 0

    def update(self):
        self.updated += 1


class ReactiveComponent:
    def __init__(self, external: Signal):
        self.page = PageStub()
        self.external = external
        self.internal: Signal | None = None
        self.render_calls = 0

    @reactive
    def render(self) -> int:
        self.render_calls += 1
        state = use_state(0)
        self.internal = state
        ext_signal = use_signal(self.external)
        return state.get() + ext_signal.get()


def test_signal_notifies_and_updates_control():
    control = DummyControl()
    signal = Signal(0)

    signal.bind_control(control)

    assert control.value == 0
    assert control.updated == 1

    signal.set(1)

    assert control.value == 1
    assert control.updated == 2


def test_signal_effect_decorator_collects_values():
    signal = Signal("hola")
    values: list[str] = []

    @signal.effect
    def _(value: str) -> None:
        values.append(value)

    signal.set("mundo")

    assert values == ["hola", "mundo"]


def test_store_exposes_signals_and_snapshot():
    store = Store({"count": 0})

    count_values: list[int] = []
    store.signal("count").effect(lambda value: count_values.append(value))

    snapshots: list[dict[str, int]] = []

    store.subscribe(lambda snapshot: snapshots.append(dict(snapshot)), immediate=True)

    store["count"] = 1
    store.update("count", lambda value: value + 1)
    store.signal("status", default="idle")
    store["status"] = "running"

    derived = store.derive(lambda snapshot: snapshot["count"] * 10)
    derived_values: list[int] = []
    derived.subscribe(lambda value: derived_values.append(value), immediate=True)

    store["count"] = 5

    assert count_values == [0, 1, 2, 5]
    assert snapshots[0]["count"] == 0
    assert snapshots[-1] == {"count": 5, "status": "running"}
    assert derived_values == [20, 50]


def test_store_signal_missing_key_raises():
    store = Store()
    with pytest.raises(KeyError):
        store.signal("unknown")


def test_reactive_use_state_triggers_page_update():
    external = Signal(5)
    component = ReactiveComponent(external)

    assert component.render() == 5
    assert component.render_calls == 1

    assert component.internal is not None
    component.internal.set(2)
    assert component.page.updated >= 1

    external.set(7)
    assert component.page.updated >= 2

    # El estado debe persistir entre renderizados explícitos
    assert component.render() == 9
    assert component.render_calls == 2


def test_watch_runs_callback_for_signal_changes():
    signal = Signal(0)
    observed: list[int] = []

    stop = watch(signal, lambda value: observed.append(value))
    signal.set(1)
    stop()
    signal.set(2)

    assert observed == [0, 1]
