"""Utilidades para generar capturas y grabaciones de la demo."""
from __future__ import annotations

import asyncio
import contextlib
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

import flet as ft

from .app import DEMO_ROUTES, create_app

DEFAULT_VIEWPORT = (1280, 720)
DEFAULT_DELAY = 0.8
DEFAULT_RECORD_DURATION = 3.0
DEFAULT_RECORD_FPS = 30


@dataclass(slots=True)
class CaptureSummary:
    """Resultado de la generación de activos."""

    screenshots: Dict[str, Path] = field(default_factory=dict)
    recordings: Dict[str, Path] = field(default_factory=dict)


class CaptureError(RuntimeError):
    """Error personalizado para fallos al generar activos."""


def capture_assets(
    *,
    screenshot_dir: Path | str | None,
    recording_dir: Path | str | None = None,
    viewport: tuple[int, int] = DEFAULT_VIEWPORT,
    delay: float = DEFAULT_DELAY,
    record_duration: float = DEFAULT_RECORD_DURATION,
    record_fps: int = DEFAULT_RECORD_FPS,
) -> CaptureSummary:
    """Genera capturas PNG y clips MP4 para las rutas de la demo.

    Parameters
    ----------
    screenshot_dir:
        Carpeta donde almacenar las capturas. Si es ``None`` no se generan
        imágenes.
    recording_dir:
        Carpeta destino de los clips MP4. Se creará automáticamente si no
        existe. Requiere ``imageio`` e ``imageio-ffmpeg`` instalados.
    viewport:
        Tupla ``(ancho, alto)`` usada para dimensionar la ventana oculta.
    delay:
        Tiempo de espera (en segundos) tras navegar antes de capturar.
    record_duration:
        Duración (en segundos) de cada clip MP4.
    record_fps:
        Cuadros por segundo que se usarán al sintetizar los clips.
    """

    if not screenshot_dir and not recording_dir:
        raise ValueError("Debes indicar --capture, --record o ambos.")

    screenshot_path = Path(screenshot_dir).expanduser().resolve() if screenshot_dir else None
    recording_path = Path(recording_dir).expanduser().resolve() if recording_dir else None

    if screenshot_path:
        screenshot_path.mkdir(parents=True, exist_ok=True)
    if recording_path:
        recording_path.mkdir(parents=True, exist_ok=True)

    summary = CaptureSummary()

    async def _session(page: ft.Page) -> None:
        await _prepare_page(page, viewport)
        app = create_app(page)
        await asyncio.sleep(delay)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_base = Path(tmp_dir)
            for route in DEMO_ROUTES:
                await _activate_route(app, route.path)
                await asyncio.sleep(delay)
                target_dir = screenshot_path or tmp_base
                image_path = target_dir / f"{route.slug}.png"
                await _take_screenshot(page, image_path)
                if screenshot_path:
                    summary.screenshots[route.path] = image_path
                if recording_path:
                    video_path = recording_path / f"{route.slug}.mp4"
                    _build_recording(
                        image_path,
                        video_path,
                        fps=record_fps,
                        duration=record_duration,
                    )
                    summary.recordings[route.path] = video_path

        _close_hidden_window(page)

    async def _run_app() -> None:
        await ft.app_async(target=_session, view=ft.AppView.FLET_APP_HIDDEN)

    try:
        asyncio.run(_run_app())
    except ModuleNotFoundError as exc:
        raise CaptureError("No fue posible iniciar Flet: revisa la instalación.") from exc

    return summary


async def _prepare_page(page: ft.Page, viewport: tuple[int, int]) -> None:
    width, height = viewport
    _set_window_attr(page, "width", float(width))
    _set_window_attr(page, "height", float(height))
    _set_window_attr(page, "resizable", False)
    _set_window_attr(page, "left", -float(width) * 2)
    _set_window_attr(page, "top", -float(height) * 2)
    _set_window_attr(page, "visible", False)
    _set_window_attr(page, "skip_taskbar", True)
    page.bgcolor = ft.Colors.SURFACE
    await _update_page(page)
    await asyncio.sleep(0.1)


async def _activate_route(app, path: str) -> None:
    app.router.go(path)
    await _update_page(app.page)


async def _take_screenshot(page: ft.Page, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    screenshot_async = getattr(page, "screenshot_async", None)
    if callable(screenshot_async):
        await screenshot_async(path=str(path))
        return
    screenshot = getattr(page, "screenshot", None)
    if callable(screenshot):
        result = screenshot(path=str(path))
        if asyncio.iscoroutine(result):
            await result
        return
    await page._invoke_method_async(
        "screenshot",
        {"path": str(path)},
        wait_for_result=True,
        wait_timeout=30,
    )


def _build_recording(image_path: Path, video_path: Path, *, fps: int, duration: float) -> None:
    try:
        import imageio.v2 as iio
    except ModuleNotFoundError as exc:
        raise CaptureError(
            "Para usar --record instala las dependencias opcionales:"
            " pip install imageio imageio-ffmpeg"
        ) from exc

    frame = iio.imread(image_path)
    total_frames = max(int(duration * fps), 1)
    video_path.parent.mkdir(parents=True, exist_ok=True)
    with iio.get_writer(video_path, fps=fps) as writer:
        for _ in range(total_frames):
            writer.append_data(frame)


__all__ = [
    "CaptureError",
    "CaptureSummary",
    "capture_assets",
]


def _set_window_attr(page: ft.Page, attr: str, value) -> None:
    window = getattr(page, "window", None)
    if window and hasattr(window, attr):
        setattr(window, attr, value)


def _close_hidden_window(page: ft.Page) -> None:
    window = getattr(page, "window", None)
    if not window:
        return
    for attr in ("destroy", "close"):
        method = getattr(window, attr, None)
        if callable(method):
            with contextlib.suppress(Exception):
                method()


async def _update_page(page: ft.Page) -> None:
    update_async = getattr(page, "update_async", None)
    if callable(update_async):
        await update_async()
        return
    page.update()
