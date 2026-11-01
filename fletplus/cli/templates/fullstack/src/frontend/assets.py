"""Referencias centralizadas a assets seguros del proyecto."""

from __future__ import annotations

from .config import ASSETS_DIR, PLACEHOLDER_README

FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"

__all__ = [
    "ASSETS_DIR",
    "PLACEHOLDER_README",
    "FONTS_DIR",
    "ICONS_DIR",
    "IMAGES_DIR",
]
