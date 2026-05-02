"""Main menu shell: shared backdrop plus UIManager-driven Neural Link hierarchy."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Dict, Optional

from direct.interval.IntervalGlobal import Sequence
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from panda3d.core import NodePath, TransparencyAttrib

from core.path_manager import PathManager
from ui.base_screen import (
    GameUIBase,
    solid_color_menu_fallback_card,
    textured_cover_background_card,
)
from ui.player_profile import PlayerProfile
from ui.ui_manager import UIManager

LOGGER: logging.Logger = logging.getLogger(__name__)

_LAYOUT_REFRESH_TASK = "urg-main-menu-display-refresh"


class MainMenu(DirectObject, GameUIBase):
    """Fullscreen backdrop under ``aspect2d``; routes navigation via `UIManager`."""

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
        self.ui_manager = UIManager(
            game_base,
            self.profile,
            labels,
            on_settings=on_settings,
            on_exit=on_exit,
        )

        self.background: Optional[NodePath] = None
        self.background_fade: Optional[Sequence] = None
        self._menu_bg_anchor: Optional[NodePath] = None

    def show(self) -> None:
        """Mount backdrop and enter Neural Link root."""
        self._release_background_only()
        self._create_background()
        self.ui_manager.switch_to("neural_link")

    def cleanup(self) -> None:
        """Tear down menus, Esc bindings, and backdrop."""
        self.game_base.taskMgr.remove(_LAYOUT_REFRESH_TASK)
        self.ignoreAll()
        self.ui_manager.shutdown()
        self._release_background_only()

    def refresh_display_layout(self, *_args: object) -> None:
        """
        Debounced refresh after resize / DPI / framebuffer changes.

        Recalibrates aspect ratio from the live window, rescales the aspect2d backdrop,
        and re-anchors the active menu column to ``a2dLeftCenter`` with fixed padding.
        """
        self.game_base.taskMgr.remove(_LAYOUT_REFRESH_TASK)
        self.game_base.taskMgr.doMethodLater(
            0.03,
            self._run_display_layout_refresh,
            _LAYOUT_REFRESH_TASK,
        )

    def _run_display_layout_refresh(self, task: Task) -> object:
        self._apply_display_layout_refresh()
        return Task.done

    def _apply_display_layout_refresh(self) -> None:
        if self._menu_bg_anchor is None or self._menu_bg_anchor.isEmpty():
            return
        aspect_ratio = float(self.game_base.getAspectRatio())
        if aspect_ratio <= 0.0:
            return
        self._release_background_card_only()
        self._mount_background_card_into(self._menu_bg_anchor, play_fade=False)
        self.ui_manager.refresh_active_menu()

    def _sync_background_card_to_viewport(self) -> None:
        """Scale the backdrop so a [-1, 1]² card under ``aspect2d`` tracks window aspect."""
        if self.background is None or self.background.isEmpty():
            return
        gb = self.game_base
        ar = float(gb.getAspectRatio())
        if ar <= 0.0:
            return
        parent = self.background.getParent()
        if parent is None:
            return
        # Main-menu card is under ``aspect2d`` (anchor); stretch X by aspect.
        if parent == gb.render2d:
            self.background.setScale(1.0, 1.0, 1.0)
            return
        self.background.setScale(ar, 1.0, 1.0)

    def _release_background_only(self) -> None:
        self._release_background_card_only()
        if self._menu_bg_anchor is not None and not self._menu_bg_anchor.isEmpty():
            self._menu_bg_anchor.removeNode()
        self._menu_bg_anchor = None

    def _release_background_card_only(self) -> None:
        if self.background_fade is not None:
            self.background_fade.finish()
            self.background_fade = None
        if self.background is not None and not self.background.isEmpty():
            self.background.removeNode()
        self.background = None

    def _ensure_menu_background_anchor(self) -> NodePath:
        """Parent under ``aspect2d`` so the backdrop shares DirectGui's normalized coordinates."""
        anchor = self.game_base.aspect2d.attachNewNode("main_menu_bg_anchor")
        anchor.setPos(0.0, 0.0, 0.0)
        anchor.setScale(1.0, 1.0, 1.0)
        self._menu_bg_anchor = anchor
        return anchor

    def _create_background(self) -> None:
        anchor = self._ensure_menu_background_anchor()
        self._mount_background_card_into(anchor, play_fade=True)

    def _mount_background_card_into(self, anchor: NodePath, *, play_fade: bool) -> None:
        menu_aspect: float = float(self.game_base.getAspectRatio())
        background_path: Optional[Path] = PathManager.resolve_image_file(
            "menu_bg.png",
            "main_menu.png",
        )

        if background_path is not None and background_path.exists():
            card = textured_cover_background_card(
                self.game_base,
                background_path,
                parent=anchor,
                under_aspect2d=True,
            )
            if card is not None:
                card.setPos(0.0, 0.0, 0.0)
                self.background = card
            else:
                LOGGER.warning("Menu background texture failed; using solid fallback.")
                self.background = solid_color_menu_fallback_card(
                    self.game_base,
                    menu_aspect,
                    parent=anchor,
                    under_aspect2d=True,
                )
                self.background.setPos(0.0, 0.0, 0.0)
        else:
            LOGGER.warning("Menu background image not found, using color fallback.")
            self.background = solid_color_menu_fallback_card(
                self.game_base,
                menu_aspect,
                parent=anchor,
                under_aspect2d=True,
            )
            self.background.setPos(0.0, 0.0, 0.0)

        self.background.setTransparency(TransparencyAttrib.MAlpha)
        if play_fade:
            self.background.setColorScale(1, 1, 1, 0)
            self.background_fade = self.background.colorScaleInterval(
                1.0,
                (1, 1, 1, 1),
                startColorScale=(1, 1, 1, 0),
            )
            self.background_fade.start()
        else:
            self.background.setColorScale(1, 1, 1, 1)
        self._sync_background_card_to_viewport()
