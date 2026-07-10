from __future__ import annotations

import json
from pathlib import Path

import flet as ft

from fletplus.cli.build import (
    BuildManager,
    BuildTarget,
    FullStackBuildContext,
    WebAdapter,
)
from fletplus.core import FletPlusApp
from fletplus.frontend import FrontEndConfig
from fletplus.rendering import (
    DesktopRenderStrategy,
    FullStackRenderStrategy,
    MobileRenderStrategy,
    WebRenderStrategy,
    strategy_for_target,
)


class DummyPage:
    def __init__(self, width=1024, height=768):
        self.width = width
        self.height = height
        self.controls = []
        self.theme = None
        self.padding = None
        self.title = ""
        self.update_calls = 0

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        self.update_calls += 1


def test_strategy_for_target_maps_public_platforms():
    assert isinstance(strategy_for_target("web"), WebRenderStrategy)
    assert isinstance(strategy_for_target("desktop"), DesktopRenderStrategy)
    assert isinstance(strategy_for_target("android-apk"), MobileRenderStrategy)
    assert isinstance(strategy_for_target("all"), FullStackRenderStrategy)


def test_frontend_config_exposes_render_strategy_and_target_presets():
    config = FrontEndConfig(target="web")

    strategy = config.render_strategy()

    assert isinstance(strategy, WebRenderStrategy)
    assert config.preset_for_target()["page_padding"] == strategy.page_padding


def test_fletplus_app_applies_render_strategy_to_root_controls():
    page = DummyPage()
    app = FletPlusApp(
        lambda state: [ft.Text("Hola")], render_strategy=WebRenderStrategy()
    )

    app.start(page)  # type: ignore[arg-type]

    assert page.padding == 32
    assert len(page.controls) == 1
    assert isinstance(page.controls[0], ft.Container)
    assert page.controls[0].width == 1280


def test_build_manager_selects_strategy_for_build_target(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\nversion='1'\n", encoding="utf-8"
    )
    context = FullStackBuildContext.from_project(tmp_path, Path("src/main.py"))
    manager = BuildManager(context)

    strategy = manager.select_render_strategy(BuildTarget.DESKTOP)

    assert isinstance(strategy, DesktopRenderStrategy)
    assert context.render_strategy is strategy


def test_adapter_writes_render_strategy_manifest(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\nversion='1'\n", encoding="utf-8"
    )
    context = FullStackBuildContext.from_project(tmp_path, Path("src/main.py"))

    prepared = WebAdapter(context).prepare()

    manifest = prepared["render_strategy"]
    assert manifest == tmp_path / "build" / "web" / "render_strategy.json"
    assert json.loads(manifest.read_text(encoding="utf-8"))["target"] == "web"
