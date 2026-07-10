"""API pública de estrategias de renderizado de FletPlus."""

from fletplus.rendering.strategies import (
    DesktopRenderStrategy,
    FullStackRenderStrategy,
    MobileRenderStrategy,
    RenderStrategy,
    WebRenderStrategy,
    strategy_for_target,
)

__all__ = [
    "RenderStrategy",
    "WebRenderStrategy",
    "DesktopRenderStrategy",
    "MobileRenderStrategy",
    "FullStackRenderStrategy",
    "strategy_for_target",
]
