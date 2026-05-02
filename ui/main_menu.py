"""Main menu UI module."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Dict, Optional

from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import NodePath, TransparencyAttrib

from core.path_manager import PathManager

from ui.base_screen import GameUIBase, solid_color_menu_fallback_card


LOGGER: logging.Logger = logging.getLogger(__name__)


class MainMenu(DirectObject, GameUIBase):
    """Render and manage the main menu UI widgets."""

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
        self.on_settings = on_settings
        self.on_exit = on_exit

        self.background: Optional[OnscreenImage | NodePath] = None
        self.background_fade: Optional[Sequence] = None
        self.buttons: dict[str, DirectButton] = {}

    def show(self) -> None:
        """Create menu background and buttons and bind events."""
        self.cleanup()
        self._create_background()
        self._create_buttons()

        self.accept("menu-settings", self.on_settings)
        self.accept("menu-exit", self.on_exit)

    def cleanup(self) -> None:
        """Release UI nodes and events."""
        self.ignoreAll()
        if self.background_fade is not None:
            self.background_fade.finish()
            self.background_fade = None
        if isinstance(self.background, OnscreenImage):
            self.background.destroy()
            self.background = None
        elif isinstance(self.background, NodePath):
            self.background.removeNode()
            self.background = None
        for button in self.buttons.values():
            button.destroy()
        self.buttons.clear()

    def _create_background(self) -> None:
        """Create menu background under render2d with back sorting."""
        background_path: Optional[Path] = PathManager.resolve_image_file(
            "menu_bg.png",
            "main_menu.png",
        )
        menu_aspect: float = self.aspect_ratio()
        bg_scale: tuple[float, float, float] = (menu_aspect, 1.0, 1.0)

        if background_path is not None and background_path.exists():
            self.background = OnscreenImage(
                image=str(background_path),
                parent=self.game_base.render2d,
                scale=bg_scale,
                sort=-1,
            )
            self.background.setTransparency(TransparencyAttrib.MAlpha)
        else:
            LOGGER.warning("Menu background image not found, using color fallback.")
            self.background = solid_color_menu_fallback_card(self.game_base, menu_aspect)

        self.background.setColorScale(1, 1, 1, 0)
        self.background_fade = self.background.colorScaleInterval(
            1.0,
            (1, 1, 1, 1),
            startColorScale=(1, 1, 1, 0),
        )
        self.background_fade.start()

    def _create_buttons(self) -> None:
        """Create DirectButton widgets in aspect2d and ensure visibility."""
        mouse_watcher = self.game_base.mouseWatcherNode
        is_active: bool = bool(
            mouse_watcher
            and hasattr(mouse_watcher, "isActive")
            and mouse_watcher.isActive()
        )
        if not is_active:
            LOGGER.warning("mouseWatcherNode is not active. Menu input may not work.")

        self.buttons["settings"] = DirectButton(
            text=self.labels.get("ui_settings", "Settings"),
            parent=self.game_base.aspect2d,
            scale=0.08,
            pos=(0.0, 0.0, 0.15),
            command=lambda: messenger.send("menu-settings"),
        )
        self.buttons["exit"] = DirectButton(
            text=self.labels.get("ui_exit", "Exit"),
            parent=self.game_base.aspect2d,
            scale=0.08,
            pos=(0.0, 0.0, -0.05),
            command=lambda: messenger.send("menu-exit"),
        )

        for button in self.buttons.values():
            button.show()
