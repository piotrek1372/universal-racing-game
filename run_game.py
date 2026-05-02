"""Slim game entry point and high-level state orchestration."""

from __future__ import annotations

import json
import logging
from typing import Dict

from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties

from core.path_manager import PathManager
from ui.main_menu import MainMenu
from ui.splash_screen import SplashScreen


LOGGER: logging.Logger = logging.getLogger(__name__)


class RacingGame(ShowBase):
    """Initialize the engine and orchestrate splash/menu states."""

    def __init__(self) -> None:
        super().__init__()
        self.disableMouse()

        self._configure_window()
        self.lang: Dict[str, str] = self._load_language("en")

        self.main_menu: MainMenu | None = None
        self.splash_screen = SplashScreen(
            game_base=self,
            on_complete=self._on_splash_complete,
            soundtrack_name="Tarmac_Predator.mp3",
        )
        self.splash_screen.start()

    def _configure_window(self) -> None:
        """Apply initial window properties."""
        props: WindowProperties = WindowProperties()
        props.setFullscreen(True)
        props.setTitle("Universal Racing Game")
        self.win.requestProperties(props)

    def _load_language(self, lang_code: str) -> Dict[str, str]:
        """Load language dictionary from assets/lang with fallback."""
        fallback_lang: Dict[str, str] = {
            "ui_start": "Start",
            "ui_exit": "Exit",
            "ui_settings": "Settings",
            "ui_title": "Universal Racing Game",
        }

        requested_file, english_file = PathManager.resolve_language_candidates(lang_code)
        for candidate in (requested_file, english_file):
            if not candidate.exists():
                continue
            try:
                with candidate.open("r", encoding="utf-8") as file_obj:
                    loaded_data: object = json.load(file_obj)
            except (OSError, json.JSONDecodeError) as error:
                LOGGER.warning("Could not load language file %s: %s", candidate, error)
                continue

            if isinstance(loaded_data, dict):
                return {str(key): str(value) for key, value in loaded_data.items()}

        LOGGER.warning(
            "No valid language file found under %s. Falling back to built-in labels.",
            PathManager.LANG_DIR,
        )
        return fallback_lang.copy()

    def _on_splash_complete(self) -> None:
        """Transition from splash flow to main menu."""
        self.main_menu = MainMenu(
            game_base=self,
            labels=self.lang,
            on_settings=self._on_settings,
            on_exit=self._on_exit,
        )
        self.main_menu.show()

    def _on_settings(self) -> None:
        """Handle settings action."""
        print("Settings clicked")

    def _on_exit(self) -> None:
        """Handle exit action."""
        self.cleanup()
        self.userExit()

    def cleanup(self) -> None:
        """Release state managers and UI."""
        if self.splash_screen is not None:
            self.splash_screen.cleanup()
        if self.main_menu is not None:
            self.main_menu.cleanup()
            self.main_menu = None


if __name__ == "__main__":
    game = RacingGame()
    game.run()