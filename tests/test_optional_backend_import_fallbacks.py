from __future__ import annotations

import importlib
import importlib.util

def _force_import_failure(monkeypatch, *module_names: str) -> None:
    original_find_spec = importlib.util.find_spec
    original_import_module = importlib.import_module
    targets = set(module_names)

    def fake_find_spec(name: str, package: str | None = None):
        if name in targets:
            return object()
        return original_find_spec(name, package)

    def fake_import_module(name: str, package: str | None = None):
        if name in targets:
            raise RuntimeError(f"simulated failure importing {name}")
        return original_import_module(name, package)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
    monkeypatch.setattr(importlib, "import_module", fake_import_module)


def test_state_module_imports_when_native_backend_fails(monkeypatch):
    _force_import_failure(monkeypatch, "fletplus.state._native")

    state_module = importlib.import_module("fletplus.state.state")

    signal = state_module.Signal(1)
    signal.set(2)

    assert signal.get() == 2


def test_smart_table_module_keeps_python_fallback_when_rs_backend_fails(monkeypatch):
    _force_import_failure(monkeypatch, "fletplus.components.smart_table_rs")

    smart_table_module = importlib.import_module("fletplus.components.smart_table")

    table = smart_table_module.SmartTable(columns=["name"], rows=[{"name": "Ana"}, {"name": "Luis"}])
    records = table._apply_query(table._records)

    assert [record.values["name"] for record in records] == ["Ana", "Luis"]


def test_responsive_manager_imports_when_native_backend_fails(monkeypatch):
    _force_import_failure(monkeypatch, "fletplus.utils._native")

    responsive_manager_module = importlib.import_module("fletplus.utils.responsive_manager")

    class DummyPage:
        width = 500
        height = 800
        platform = "windows"
        on_resize = None

        def update(self):
            return None

    manager = responsive_manager_module.ResponsiveManager(DummyPage(), breakpoints={0: lambda _w: None})

    assert manager is not None


def test_theme_manager_imports_when_rs_backends_fail(monkeypatch, tmp_path):
    _force_import_failure(
        monkeypatch,
        "fletplus.themes.palette_flatten_rs",
        "fletplus.themes.theme_merge_rs",
    )

    theme_manager_module = importlib.import_module("fletplus.themes.theme_manager")

    palette_file = tmp_path / "palette.json"
    palette_file.write_text('{"light": {"info": {"100": "#fff"}}}', encoding="utf-8")
    flattened = theme_manager_module.load_palette_from_file(str(palette_file), mode="light")

    assert flattened["info_100"] == "#fff"
