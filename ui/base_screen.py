"""Shared ShowBase-bound UI helpers for screens and overlays."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from panda3d.core import CardMaker, NodePath, TransparencyAttrib


class GameUIBase:
    """Minimal base for UI tied to a Panda3D ShowBase instance."""

    __slots__ = ("game_base",)

    def __init__(self, game_base: Any) -> None:
        self.game_base = game_base

    def aspect_ratio(self) -> float:
        """Horizontal aspect ratio used for 2D menu layouts."""
        return float(self.game_base.getAspectRatio())


def fullscreen_textured_card(
    game_base: Any,
    image_path: Path,
    card_name: str,
) -> Optional[NodePath]:
    """Attach a fullscreen render2d quad with the given texture; alpha enabled."""
    cm = CardMaker(card_name)
    cm.setFrameFullscreenQuad()
    card: NodePath = game_base.render2d.attachNewNode(cm.generate())
    texture = game_base.loader.loadTexture(str(image_path))
    card.setTexture(texture)
    card.setTransparency(TransparencyAttrib.MAlpha)
    card.setColorScale(1, 1, 1, 0)
    return card


def solid_color_menu_fallback_card(game_base: Any, aspect: float) -> NodePath:
    """Fullscreen gray card when no background image is available."""
    card_maker = CardMaker("menu_bg_fallback")
    card_maker.setFrame(-aspect, aspect, -1.0, 1.0)
    card: NodePath = game_base.render2d.attachNewNode(card_maker.generate())
    card.setColor(0.15, 0.15, 0.15, 1.0)
    card.setBin("background", 0)
    card.setDepthWrite(False)
    card.setDepthTest(False)
    return card
