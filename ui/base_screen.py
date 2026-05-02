"""Shared ShowBase-bound UI helpers for screens and overlays."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional, Union

from panda3d.core import CardMaker, Filename, NodePath, TransparencyAttrib

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
    """
    Fullscreen splash card under ``aspect2d`` (same normalized space as DirectGui).

    Uses a uniform ``[-1, 1] × [-1, 1]`` frame so the quad tracks ``aspect2d`` scaling
    and fills the window after ``adjustWindowAspectRatio`` / ``window-event``.
    """
    cm = CardMaker(card_name)
    cm.setFrame(-1.0, 1.0, -1.0, 1.0)
    card: NodePath = game_base.aspect2d.attachNewNode(cm.generate())
    panda_path = Filename.fromOsSpecific(str(image_path)).getFullpath()
    texture = game_base.loader.loadTexture(panda_path)
    card.setTexture(texture)
    card.setTransparency(TransparencyAttrib.MAlpha)
    card.setColorScale(1, 1, 1, 0)
    card.setBin("background", _DEFAULT_BACKGROUND_BIN_SORT)
    card.setDepthWrite(False)
    card.setDepthTest(False)
    return card


def solid_color_menu_fallback_card(
    game_base: Any,
    aspect: float,
    *,
    parent: Optional[NodePath] = None,
    background_sort: int = _DEFAULT_BACKGROUND_BIN_SORT,
    under_aspect2d: bool = False,
) -> NodePath:
    """Fullscreen gray card when no background image is available."""
    root = parent if parent is not None else game_base.render2d
    card_maker = CardMaker("menu_bg_fallback")
    if under_aspect2d:
        card_maker.setFrame(-1.0, 1.0, -1.0, 1.0)
    else:
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
    under_aspect2d: bool = False,
) -> Optional[NodePath]:
    """
    Full-window backdrop that preserves texture aspect ratio (cover crop).

    When ``under_aspect2d`` is True, the card uses a uniform ``[-1, 1] × [-1, 1]`` frame
    under ``aspect2d`` (matches DirectGui). Otherwise it uses render2d-style extents
    ``[-aspectRatio, aspectRatio] × [-1, 1]``.

    Layering uses ``setBin`` only (``NodePath`` has no ``setSort`` in all Panda builds).
    """
    path_str = Filename.fromOsSpecific(str(image_path)).getFullpath()
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

    # Under aspect2d, menu space is a square [-1, 1]²; "window" aspect for cover is 1:1.
    win_ar = 1.0 if under_aspect2d else float(game_base.getAspectRatio())
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
