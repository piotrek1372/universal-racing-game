"""Main menu shell: ``render2d`` fullscreen backdrop plus UIManager-driven hierarchy."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Dict, Optional

from direct.interval.IntervalGlobal import Sequence
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from panda3d.core import CardMaker, Filename, NodePath, TransparencyAttrib

from core.path_manager import PathManager
from ui.base_screen import GameUIBase
from ui.player_profile import PlayerProfile
from ui.ui_manager import UIManager

LOGGER: logging.Logger = logging.getLogger(__name__)

_LAYOUT_REFRESH_TASK = "urg-main-menu-display-refresh"
_BACKGROUND_BIN_SORT: int = -10


class MainMenu(DirectObject, GameUIBase):
    """Fullscreen ``render2d`` backdrop; DirectGui under ``aspect2d`` via `UIManager`."""

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

    def show(self) -> None:
        """Mount backdrop on ``render2d`` and enter Neural Link root (same as full rebuild)."""
        self.rebuild_ui()

    def rebuild_ui(self) -> None:
        """
        Tear down the backdrop and menu widgets, re-read aspect ratio, and rebuild at the
        current window resolution (e.g. 16:9 after ``requestProperties``).
        """
        aspect_ratio = float(self.game_base.getAspectRatio())
        if aspect_ratio <= 0.0:
            LOGGER.warning("rebuild_ui: invalid aspect ratio, skipping.")
            return

        self.ui_manager.teardown_active_menu()
        self._release_background_only()

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

    def refresh_display_layout(self, *_args: object) -> None:
        """Debounced refresh after resize / DPI / framebuffer changes."""
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
        """Full-window NDC card on ``render2d``; ``setBin`` keeps it behind all GUI."""
        gb = self.game_base
        cm = CardMaker("main_menu_bg_render2d")
        cm.setFrame(-1.0, 1.0, -1.0, 1.0)
        card: NodePath = gb.render2d.attachNewNode(cm.generate())
        card.setDepthWrite(False)
        card.setDepthTest(False)
        card.setBin("background", _BACKGROUND_BIN_SORT)

        background_path: Optional[Path] = PathManager.resolve_image_file(
            "menu_bg.png",
            "main_menu.png",
        )
        if background_path is not None and background_path.exists():
            panda_path = Filename.fromOsSpecific(str(background_path)).getFullpath()
            try:
                tex = gb.loader.loadTexture(panda_path)
            except OSError as exc:
                LOGGER.warning("Could not load menu background texture %s: %s", panda_path, exc)
                tex = None
            if tex is not None:
                card.setTexture(tex)
            else:
                card.setColor(0.15, 0.15, 0.15, 1.0)
        else:
            LOGGER.warning("Menu background image not found, using color fallback.")
            card.setColor(0.15, 0.15, 0.15, 1.0)

        card.setTransparency(TransparencyAttrib.MAlpha)
        self.background = card
        self.background.setColorScale(1, 1, 1, 0)
        self.background_fade = self.background.colorScaleInterval(
            1.0,
            (1, 1, 1, 1),
            startColorScale=(1, 1, 1, 0),
        )
        self.background_fade.start()
