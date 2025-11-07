"""Utilidades para generar capturas y grabaciones de la demo."""
from __future__ import annotations

import asyncio
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
                _activate_route(app, route.path)
                await asyncio.sleep(delay)
                target_dir = screenshot_path or tmp_base
                image_path = target_dir / f"{route.slug}.png"
                await _take_screenshot(page, image_path)
                if screenshot_path:
                    summary.screenshots[route.path] = image_path
                if recording_path:
                    video_path = recording_path / f"{route.slug}.mp4"
                    _build_recording(image_path, video_path, fps=record_fps, duration=record_duration)
                    summary.recordings[route.path] = video_path

        page.window.destroy()
        page.window.close()

    try:
        asyncio.run(ft.app_async(target=_session, view=ft.AppView.FLET_APP_HIDDEN))
    except ModuleNotFoundError as exc:
        raise CaptureError("No fue posible iniciar Flet: revisa la instalación.") from exc

    return summary


async def _prepare_page(page: ft.Page, viewport: tuple[int, int]) -> None:
    width, height = viewport
    page.window.width = float(width)
    page.window.height = float(height)
    page.window.resizable = False
    page.bgcolor = ft.Colors.SURFACE
    page.update()
    await asyncio.sleep(0.1)


def _activate_route(app, path: str) -> None:
    app.router.go(path)
    app.page.update()


async def _take_screenshot(page: ft.Page, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
