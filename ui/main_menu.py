"""Main menu shell: ``render2d`` fullscreen backdrop plus UIManager-driven hierarchy."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Dict, Optional

from direct.interval.IntervalGlobal import Sequence
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from panda3d.core import BitMask32, CardMaker, NodePath, TransparencyAttrib

from core.path_manager import PathManager
from ui.base_screen import GameUIBase
from ui.player_profile import PlayerProfile
from ui.ui_manager import UIManager

LOGGER: logging.Logger = logging.getLogger(__name__)

_LAYOUT_REFRESH_TASK = "urg-main-menu-display-refresh"

# Keep far behind aspect2d DirectGui so picking / hover still works.
_BACKGROUND_BIN_SORT: int = -100

# Normalization constant: at 16:9 (ar ≈ 1.778) the factor gives scale 1.0,
# so buttons and panels keep the same physical screen size at every resolution.
_REFERENCE_ASPECT: float = 16.0 / 9.0
_SCALE_AT_REFERENCE: float = 1.0

# Horizontal offset of the menu list from the left-centre anchor (aspect2d units).
_MENU_CONTAINER_OFFSET_X: float = 0.18


class MainMenu(DirectObject, GameUIBase):
    """
    Fullscreen ``render2d`` backdrop with ``aspect2d``-anchored DirectGui menus.

    The container NodePath is parented to ``base.a2dLeftCenter`` so it
    automatically tracks the left edge of the screen.  A normalization factor
    derived from the current aspect ratio keeps buttons the same physical size
    regardless of resolution.
    """

    def __init__(
        self,
        game_base,
        labels: Dict[str, str],
        on_settings: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        DirectObject.__init__(self)
        GameUIBase.__init__(self, game_base)

        self.labels = labels
        self.profile = PlayerProfile()

        # ------------------------------------------------------------------ #
        # Container: parented to a2dLeftCenter so it rides the left edge.     #
        # X-position is a *positive* offset into screen space (away from edge).
        # ------------------------------------------------------------------ #
        self.container: NodePath = game_base.a2dLeftCenter.attachNewNode(
            "main_menu_container"
        )
        self.container.setPos(_MENU_CONTAINER_OFFSET_X, 0.0, 0.0)
        game_base.main_menu_container = self.container

        # Apply initial scale before UIManager / menus are constructed.
        self._apply_container_scale()

        self.ui_manager = UIManager(
            game_base,
            self.profile,
            labels,
            on_settings=on_settings,
            on_exit=on_exit,
        )

        self.background: Optional[NodePath] = None
        self.background_fade: Optional[Sequence] = None

    # ---------------------------------------------------------------------- #
    # Public interface                                                          #
    # ---------------------------------------------------------------------- #

    def apply_responsive_scale(self) -> None:
        """
        Recalculate and apply the container scale for the current aspect ratio.

        Formula: ``scale = (1.0 / ar) * _REFERENCE_ASPECT``

        At 16:9 this gives 1.0, at 21:9 it shrinks (≈ 0.76), at 4:3 it grows
        (≈ 1.33).  The X offset is left unchanged — it is expressed in *screen*
        units and is already aspect-corrected by ``a2dLeftCenter``'s position.
        """
        self._apply_container_scale()

    def hide(self) -> None:
        """Tear down DirectGui menus and the ``render2d`` backdrop."""
        self.ui_manager.teardown_active_menu()
        self._release_background_only()

    def show(self) -> None:
        """Show the menu; rebuild if the backdrop is missing."""
        if self.background is None:
            self.rebuild_ui()
            return
        self.game_base.force_ui_remap()
        self.ui_manager.reanchor_active_menu()

    def rebuild_ui(self) -> None:
        """
        Tear everything down, re-read the aspect ratio, and rebuild at the
        current resolution.  Called after ``requestProperties`` or DPI changes.
        """
        ar = float(self.game_base.getAspectRatio())
        if ar <= 0.0:
            LOGGER.warning("rebuild_ui: invalid aspect ratio (%.4f), skipping.", ar)
            return

        self.hide()
        self._apply_container_scale()
        self._create_background_render2d()

        if self.ui_manager.is_stack_empty():
            self.ui_manager.switch_to("neural_link")
        else:
            self.ui_manager.refresh_active_menu()

    def cleanup(self) -> None:
        """Tear down menus, Esc bindings, and backdrop."""
        self.game_base.taskMgr.remove(_LAYOUT_REFRESH_TASK)
        self.ignoreAll()
        self.ui_manager.shutdown()
        self._release_background_only()
        if getattr(self.game_base, "main_menu_container", None) is self.container:
            self.game_base.main_menu_container = None
        if self.container is not None and not self.container.isEmpty():
            self.container.removeNode()

    def refresh_display_layout(self, *_args: object) -> None:
        """Debounced refresh after resize / DPI / framebuffer changes."""
        self.game_base.taskMgr.remove(_LAYOUT_REFRESH_TASK)
        self.game_base.taskMgr.doMethodLater(
            0.05,
            self._run_display_layout_refresh,
            _LAYOUT_REFRESH_TASK,
        )

    # ---------------------------------------------------------------------- #
    # Private helpers                                                           #
    # ---------------------------------------------------------------------- #

    def _apply_container_scale(self) -> None:
        """
        Scale the container so menus occupy consistent physical screen space
        regardless of the window's aspect ratio.

        ``a2dLeftCenter`` moves with the screen edge as AR changes, but child
        scales are still in the *square* coordinate system of aspect2d.  This
        factor undoes the distortion introduced by extreme aspect ratios.
        """
        ar = float(self.game_base.getAspectRatio())
        if ar <= 0.0:
            return

        # (1 / ar) * ref normalises to 1.0 at 16:9, scales down for ultra-wide,
        # scales up for tall / narrow displays.
        normalised_scale = (1.0 / ar) * _REFERENCE_ASPECT * _SCALE_AT_REFERENCE
        self.container.setScale(normalised_scale)

        # Keep X offset expressed in screen units (positive = rightward from edge).
        self.container.setPos(_MENU_CONTAINER_OFFSET_X, 0.0, 0.0)

    def _run_display_layout_refresh(self, task: Task) -> object:
        self._apply_display_layout_refresh()
        return Task.done

    def _apply_display_layout_refresh(self) -> None:
        self._apply_container_scale()
        self.rebuild_ui()

    def _release_background_only(self) -> None:
        self._release_background_card_only()

    def _release_background_card_only(self) -> None:
        if self.background_fade is not None:
            self.background_fade.finish()
            self.background_fade = None
        if self.background is not None and not self.background.isEmpty():
            self.background.removeNode()
        self.background = None

    def _create_background_render2d(self) -> None:
        """
        Full-window NDC card on ``render2d``; ``setBin`` keeps it behind all GUI.

        The card uses a square ``[-1, 1] × [-1, 1]`` frame in ``render2d`` space.
        All asset paths go through ``PathManager.to_panda_path`` for Windows /
        Linux compatibility.
        """
        gb = self.game_base
        cm = CardMaker("main_menu_bg_render2d")
        cm.setFrame(-1.0, 1.0, -1.0, 1.0)
        card: NodePath = gb.render2d.attachNewNode(cm.generate())
        card.setDepthWrite(False)
        card.setDepthTest(False)
        card.setCollideMask(BitMask32.allOff())
        card.setBin("background", _BACKGROUND_BIN_SORT)

        background_path: Optional[Path] = PathManager.resolve_image_file(
            "menu_bg.png",
            "main_menu.png",
        )
        if background_path is not None and background_path.exists():
            panda_path = PathManager.to_panda_path(background_path)
            try:
                tex = gb.loader.loadTexture(panda_path)
            except OSError as exc:
                LOGGER.warning(
                    "Could not load menu background texture %s: %s", panda_path, exc
                )
                tex = None

            if tex is not None:
                card.setTexture(tex)
            else:
                card.setColor(0.15, 0.15, 0.15, 1.0)
        else:
            LOGGER.warning("Menu background image not found, using colour fallback.")
            card.setColor(0.15, 0.15, 0.15, 1.0)

        card.setTransparency(TransparencyAttrib.MAlpha)
        self.background = card

        # Fade in from transparent.
        self.background.setColorScale(1, 1, 1, 0)
        self.background_fade = self.background.colorScaleInterval(
            1.0,
            (1, 1, 1, 1),
            startColorScale=(1, 1, 1, 0),
        )
        self.background_fade.start()