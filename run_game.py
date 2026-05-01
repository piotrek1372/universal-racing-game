from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable, Dict, Optional

from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.ShowBase import ShowBase
from direct.showbase import ShowBaseGlobal
from direct.interval.IntervalGlobal import Func, Parallel, Sequence, Wait
from panda3d.core import (
    AudioSound,
    BitMask32,
    CardMaker,
    CollisionHandlerQueue,
    CollisionNode,
    CollisionRay,
    CollisionTraverser,
    WindowProperties,
    NodePath,
    TransparencyAttrib,
)


LOGGER: logging.Logger = logging.getLogger(__name__)


class PathManager:
    BASE_DIR: Path = Path(__file__).resolve().parent
    ASSETS_DIR: Path = BASE_DIR / "assets"
    IMAGES_DIR: Path = ASSETS_DIR / "images"
    LANG_DIR: Path = ASSETS_DIR / "lang"
    AUDIO_DIR: Path = ASSETS_DIR / "audio"
    SOUNDTRACKS_DIR: Path = ASSETS_DIR / "soundtracks"

    @classmethod
    def resolve_language_candidates(cls, lang_code: str) -> tuple[Path, ...]:
        requested_file: Path = cls.LANG_DIR / f"{lang_code}.json"
        english_file: Path = cls.LANG_DIR / "en.json"
        return (requested_file, english_file)

    @classmethod
    def resolve_audio_file(cls, filename: str) -> Optional[Path]:
        search_directories: tuple[Path, ...] = (cls.AUDIO_DIR, cls.SOUNDTRACKS_DIR)
        requested_lower: str = filename.lower()

        for directory in search_directories:
            if not directory.exists() or not directory.is_dir():
                continue

            direct_match: Path = directory / filename
            if direct_match.exists() and direct_match.is_file():
                return direct_match.resolve()

            for candidate in directory.iterdir():
                if candidate.is_file() and candidate.name.lower() == requested_lower:
                    return candidate.resolve()

        return None

    @classmethod
    def resolve_image_file(cls, *filenames: str) -> Optional[Path]:
        if not cls.IMAGES_DIR.exists() or not cls.IMAGES_DIR.is_dir():
            return None

        available_files: tuple[Path, ...] = tuple(
            candidate for candidate in cls.IMAGES_DIR.iterdir() if candidate.is_file()
        )
        if not available_files:
            return None

        available_by_lower: dict[str, Path] = {
            candidate.name.lower(): candidate for candidate in available_files
        }

        for filename in filenames:
            if not filename:
                continue
            matched_file: Optional[Path] = available_by_lower.get(filename.lower())
            if matched_file is not None:
                return matched_file.resolve()

        return None


BASE_DIR: Path = PathManager.BASE_DIR
ASSETS_DIR: Path = PathManager.ASSETS_DIR
IMAGES_DIR: Path = PathManager.IMAGES_DIR
LANG_DIR: Path = PathManager.LANG_DIR
AUDIO_DIR: Path = PathManager.AUDIO_DIR


class RacingGame(ShowBase):
    def __init__(self) -> None:
        super().__init__()

        self.disableMouse()

        self._configure_window()
        self.lang: Dict[str, str] = self._load_language("en")

        self.buttons: Dict[str, NodePath] = {}
        self.button_actions: Dict[str, Callable[[], None]] = {}
        self.splash_sequence: Sequence | None = None
        self.main_menu_bg: Optional[NodePath] = None
        self.main_menu_bg_fade: Optional[Sequence] = None
        self.bg_music: Optional[AudioSound] = self._load_background_music(
            "Tarmac_Predator.mp3"
        )

        self._setup_collision()

        self.splash_sequence = self._run_splash_sequence()

    # ------------------------------------------------------------------
    # WINDOW CONFIG
    # ------------------------------------------------------------------
    def _configure_window(self) -> None:
        props: WindowProperties = WindowProperties()
        props.setFullscreen(True)
        props.setTitle("Universal Racing Game")

        self.win.requestProperties(props)

    # ------------------------------------------------------------------
    # I18N
    # ------------------------------------------------------------------
    def _load_language(self, lang_code: str) -> Dict[str, str]:
        """
        Load a language dictionary from `assets/lang`.

        If the requested language cannot be loaded, this method falls back to
        English and finally to a hardcoded UI dictionary.

        Args:
            lang_code: Locale code such as ``en`` or ``pl``.

        Returns:
            Dict[str, str]: Localized UI strings for the active language.
        """
        fallback_lang: Dict[str, str] = {
            "ui_start": "Start",
            "ui_exit": "Exit",
            "ui_settings": "Settings",
            "ui_title": "Universal Racing Game",
        }

        if not LANG_DIR.exists() or not LANG_DIR.is_dir():
            LOGGER.warning(
                "Language directory missing or invalid: %s. Using fallback language. "
                "Expected assets root: %s. Suggested fix: mkdir -p \"%s\" "
                "and create at least \"%s\".",
                LANG_DIR.resolve(),
                ASSETS_DIR.resolve(),
                LANG_DIR.resolve(),
                (LANG_DIR / "en.json").resolve(),
            )
            return fallback_lang.copy()

        candidate_files: tuple[Path, ...] = PathManager.resolve_language_candidates(
            lang_code
        )
        requested_file: Path = candidate_files[0]
        english_file: Path = candidate_files[1]

        for lang_file in candidate_files:
            absolute_lang_path: Path = lang_file.resolve()
            LOGGER.info("Language lookup: checking absolute path %s", absolute_lang_path)
            print(f"[i18n-debug] checking language file: {absolute_lang_path}")

            if not lang_file.exists():
                continue

            try:
                with lang_file.open("r", encoding="utf-8") as file_obj:
                    loaded_data: object = json.load(file_obj)
            except json.JSONDecodeError as error:
                LOGGER.warning("Invalid JSON in language file %s: %s", lang_file, error)
                continue
            except OSError as error:
                LOGGER.warning("Failed to load language file %s: %s", lang_file, error)
                continue

            if isinstance(loaded_data, dict):
                return {str(key): str(value) for key, value in loaded_data.items()}

            LOGGER.warning(
                "Language file %s has invalid format. Expected JSON object.",
                lang_file,
            )

        LOGGER.warning(
            "No valid language file found for '%s' (checked %s and %s). "
            "Using fallback language.",
            lang_code,
            requested_file,
            english_file,
        )
        return fallback_lang.copy()

    # ------------------------------------------------------------------
    # SPLASH SCREEN
    # ------------------------------------------------------------------
    def _load_background_music(self, filename: str) -> Optional[AudioSound]:
        """
        Load background music from the assets audio directory.

        Args:
            filename: Audio filename located under ``assets/audio``.

        Returns:
            Optional[AudioSound]: Loaded sound object, or ``None`` if unavailable.
        """

        if not AUDIO_DIR.exists() and not PathManager.SOUNDTRACKS_DIR.exists():
            LOGGER.warning(
                "Audio directory missing. Checked %s and %s. Suggested fix: "
                "mkdir -p \"%s\" and move music with: mv \"%s\" \"%s/\"",
                AUDIO_DIR.resolve(),
                PathManager.SOUNDTRACKS_DIR.resolve(),
                AUDIO_DIR.resolve(),
                (PathManager.SOUNDTRACKS_DIR / filename).resolve(),
                AUDIO_DIR.resolve(),
            )
            return None

        resolved_audio_path: Optional[Path] = PathManager.resolve_audio_file(filename)
        if resolved_audio_path is None:
            LOGGER.warning(
                "Background music file not found for '%s'. Checked %s and %s "
                "(case-insensitive filename match enabled). Suggested fix: "
                "mv \"%s\" \"%s/%s\"",
                filename,
                AUDIO_DIR.resolve(),
                PathManager.SOUNDTRACKS_DIR.resolve(),
                (PathManager.SOUNDTRACKS_DIR / filename).resolve(),
                AUDIO_DIR.resolve(),
                filename,
            )
            return None

        LOGGER.info(
            "Background music lookup resolved absolute path: %s", resolved_audio_path
        )
        print(f"[audio-debug] loading music from: {resolved_audio_path}")

        base_instance = ShowBaseGlobal.base
        if base_instance is None:
            LOGGER.warning("ShowBase is not initialized. Cannot load background music.")
            return None

        try:
            music: Optional[AudioSound] = base_instance.loader.loadMusic(
                str(resolved_audio_path)
            )
        except OSError as error:
            LOGGER.warning(
                "Failed to load background music %s: %s", resolved_audio_path, error
            )
            return None

        if music is None:
            LOGGER.warning(
                "Loader returned no music object for: %s", resolved_audio_path
            )
            return None

        music.setLoop(False)
        return music

    def _create_splash(self, image_name: str) -> NodePath:
        cm: CardMaker = CardMaker("splash")
        cm.setFrameFullscreenQuad()

        card: NodePath = self.render2d.attachNewNode(cm.generate())
        tex = self.loader.loadTexture(str(IMAGES_DIR / image_name))
        card.setTexture(tex)
        card.setTransparency(TransparencyAttrib.MAlpha)
        card.setColorScale(1, 1, 1, 0)

        return card

    def _run_splash_sequence(self) -> Sequence:
        """
        Build and run the synchronized splash and audio sequence.

        Returns:
            Sequence: Started sequence that owns splash intervals.
        """
        splash_nodes: list[NodePath] = []
        for image_name in ["splash1.png", "splash2.png", "splash3.png"]:
            splash: NodePath = self._create_splash(image_name)
            if splash.isEmpty():
                LOGGER.warning(
                    "Skipping splash '%s' because NodePath is invalid.", image_name
                )
                continue

            splash.setTransparency(TransparencyAttrib.MAlpha)
            splash_nodes.append(splash)

        if not splash_nodes:
            LOGGER.warning("No valid splash images available. Opening main menu.")
            self.start_main_menu()
            fallback_sequence: Sequence = Sequence()
            fallback_sequence.start()
            return fallback_sequence

        main_sequence: Sequence = Sequence()
        first_splash: NodePath = splash_nodes[0]
        music_start: Func | Wait = (
            Func(self.bg_music.play) if self.bg_music is not None else Wait(0.0)
        )

        main_sequence.append(Wait(0.75))
        main_sequence.append(
            Parallel(
                music_start,
                first_splash.colorScaleInterval(
                    1.5,
                    (1, 1, 1, 1),
                    startColorScale=(1, 1, 1, 0),
                ),
            )
        )
        main_sequence.append(Wait(3.0))
        main_sequence.append(
            first_splash.colorScaleInterval(
                1.5,
                (1, 1, 1, 0),
                startColorScale=(1, 1, 1, 1),
            )
        )
        main_sequence.append(Func(first_splash.removeNode))

        for splash in splash_nodes[1:]:
            main_sequence.append(
                splash.colorScaleInterval(
                    1.5,
                    (1, 1, 1, 1),
                    startColorScale=(1, 1, 1, 0),
                )
            )
            main_sequence.append(Wait(3.0))
            main_sequence.append(
                splash.colorScaleInterval(
                    1.5,
                    (1, 1, 1, 0),
                    startColorScale=(1, 1, 1, 1),
                )
            )
            main_sequence.append(Func(splash.removeNode))

        main_sequence.append(Func(self.start_main_menu))
        main_sequence.start()
        return main_sequence

    def start_main_menu(self) -> None:
        """
        Transition from splash flow into the main menu.
        """

        self._load_main_menu()

    # ------------------------------------------------------------------
    # MAIN MENU (3D)
    # ------------------------------------------------------------------
    def _create_button(self, name: str, x: float, z: float) -> NodePath:
        cm: CardMaker = CardMaker(name)
        cm.setFrame(-0.5, 0.5, -0.2, 0.2)

        card: NodePath = self.render.attachNewNode(cm.generate())
        card.setPos(x, 5, z)

        card.setTag("button", name)

        return card

    def _load_main_menu(self) -> None:
        self._create_main_menu_background()

        self.buttons["settings"] = self._create_button("settings", -1.0, 0.5)
        self.buttons["exit"] = self._create_button("exit", 1.0, 0.5)

        self.button_actions = {
            "settings": self._on_settings,
            "exit": self._on_exit,
        }

        self.taskMgr.add(self._mouse_click_task, "mouse_click_task")

    def _create_main_menu_background(self) -> None:
        if self.main_menu_bg is not None and not self.main_menu_bg.isEmpty():
            self.main_menu_bg.removeNode()
            self.main_menu_bg = None

        if self.main_menu_bg_fade is not None:
            self.main_menu_bg_fade.finish()
            self.main_menu_bg_fade = None

        background_path: Optional[Path] = PathManager.resolve_image_file(
            "menu_bg.png", "main_menu.png"
        )
        menu_aspect: float = base.getAspectRatio()
        bg_scale: tuple[float, float, float] = (menu_aspect, 1.0, 1.0)

        if background_path is not None and background_path.exists():
            try:
                self.main_menu_bg = OnscreenImage(
                    image=str(background_path),
                    parent=self.render2d,
                    scale=bg_scale,
                    sort=-1,
                )
                self.main_menu_bg.setTransparency(TransparencyAttrib.MAlpha)
            except Exception as error:
                LOGGER.warning(
                    "Failed to load menu background image %s: %s. Using fallback.",
                    background_path,
                    error,
                )
                self.main_menu_bg = None

        if self.main_menu_bg is None:
            cm: CardMaker = CardMaker("menu_bg_fallback")
            cm.setFrame(-menu_aspect, menu_aspect, -1, 1)
            fallback_card: NodePath = self.render2d.attachNewNode(cm.generate())
            fallback_card.setColor(0.15, 0.15, 0.15, 1.0)
            fallback_card.setBin("background", 0)
            fallback_card.setDepthWrite(False)
            fallback_card.setDepthTest(False)
            self.main_menu_bg = fallback_card

        self.main_menu_bg.setColorScale(1, 1, 1, 0)
        self.main_menu_bg_fade = self.main_menu_bg.colorScaleInterval(
            1.0,
            (1, 1, 1, 1),
            startColorScale=(1, 1, 1, 0),
        )
        self.main_menu_bg_fade.start()

    # ------------------------------------------------------------------
    # COLLISION / PICKING
    # ------------------------------------------------------------------
    def _setup_collision(self) -> None:
        self.picker = CollisionTraverser()
        self.handler = CollisionHandlerQueue()

        self.pickerNode = CollisionNode("mouseRay")
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)

        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)

        self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.pickerNode.setIntoCollideMask(BitMask32.allOff())

        self.picker.addCollider(self.pickerNP, self.handler)

    def _mouse_click_task(self, task) -> int:
        if self.mouseWatcherNode.hasMouse():
            if self.mouseWatcherNode.isButtonDown("mouse1"):
                mpos = self.mouseWatcherNode.getMouse()

                self.pickerRay.setFromLens(
                    self.camNode, mpos.getX(), mpos.getY()
                )

                self.picker.traverse(self.render)

                if self.handler.getNumEntries() > 0:
                    self.handler.sortEntries()
                    picked = self.handler.getEntry(0).getIntoNodePath()

                    button = picked.findNetTag("button")
                    if not button.isEmpty():
                        name = button.getTag("button")
                        if name in self.button_actions:
                            self.button_actions[name]()

        return task.cont

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------
    def _on_settings(self) -> None:
        print("Settings clicked")

    def _on_exit(self) -> None:
        self.cleanup()
        self.userExit()

    # ------------------------------------------------------------------
    # CLEANUP
    # ------------------------------------------------------------------
    def cleanup(self) -> None:
        self.taskMgr.remove("mouse_click_task")
        if self.main_menu_bg_fade is not None:
            self.main_menu_bg_fade.finish()
            self.main_menu_bg_fade = None
        if self.main_menu_bg is not None and not self.main_menu_bg.isEmpty():
            self.main_menu_bg.removeNode()
            self.main_menu_bg = None
        for btn in self.buttons.values():
            btn.removeNode()
        self.buttons.clear()


if __name__ == "__main__":
    game: RacingGame = RacingGame()
    game.run()