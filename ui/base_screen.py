"""Shared ShowBase-bound UI helpers for screens and overlays."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional, Union

from panda3d.core import CardMaker, NodePath, TransparencyAttrib

LOGGER = logging.getLogger(__name__)

# Draw order within the "background" bin (NodePath has no setSort; use setBin(..., sort)).
_DEFAULT_BACKGROUND_BIN_SORT: int = -100


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


def solid_color_menu_fallback_card(
    game_base: Any,
    aspect: float,
    *,
    parent: Optional[NodePath] = None,
    background_sort: int = _DEFAULT_BACKGROUND_BIN_SORT,
) -> NodePath:
    """Fullscreen gray card when no background image is available."""
    root = parent if parent is not None else game_base.render2d
    card_maker = CardMaker("menu_bg_fallback")
    card_maker.setFrame(-aspect, aspect, -1.0, 1.0)
    card: NodePath = root.attachNewNode(card_maker.generate())
    card.setColor(0.15, 0.15, 0.15, 1.0)
    card.setTransparency(TransparencyAttrib.MAlpha)
    card.setBin("background", background_sort)
    card.setDepthWrite(False)
    card.setDepthTest(False)
    return card


def textured_cover_background_card(
    game_base: Any,
    image_path: Union[str, Path],
    *,
    card_name: str = "menu_bg_cover",
    parent: Optional[NodePath] = None,
    background_sort: int = _DEFAULT_BACKGROUND_BIN_SORT,
) -> Optional[NodePath]:
    """
    Full-window backdrop on render2d that preserves texture aspect ratio (cover crop).

    Card geometry matches the usual Panda menu convention [-aspect, aspect] × [-1, 1]
    for the visible render2d framing; half extents are expanded uniformly so both axes
    fully cover that region (texture aspect preserved — cropped at edges).

    Layering uses ``setBin`` only (``NodePath`` has no ``setSort`` in all Panda builds).
    """
    path_str = str(image_path)
    try:
        tex = game_base.loader.loadTexture(path_str)
    except OSError as exc:
        LOGGER.warning("Could not load menu background texture %s: %s", path_str, exc)
        return None

    if tex is None:
        return None

    tw = max(float(tex.get_x_size()), 1.0)
    th = max(float(tex.get_y_size()), 1.0)
    tex_ar = tw / th

    win_ar = float(game_base.getAspectRatio())
    cover_k = max(1.0, win_ar / tex_ar)

    half_w = cover_k * tex_ar
    half_h = cover_k

    root = parent if parent is not None else game_base.render2d

    cm = CardMaker(card_name)
    cm.setFrame(-half_w, half_w, -half_h, half_h)
    card: NodePath = root.attachNewNode(cm.generate())
    card.setTexture(tex)
    card.setTransparency(TransparencyAttrib.MAlpha)
    card.setBin("background", background_sort)
    card.setDepthWrite(False)
    card.setDepthTest(False)
    return card
