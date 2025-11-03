import pytest

from fletplus.state import Signal, Store


class DummyControl:
    def __init__(self):
        self.value = None
        self.updated = 0

    def update(self):
        self.updated += 1


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
