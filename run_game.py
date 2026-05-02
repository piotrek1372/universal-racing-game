"""Slim game entry point and high-level state orchestration.

Panda3D loaders (``loadTexture``, ``loadMusic``, ``loadModel``, ``loadFont``) expect
paths normalized via ``PathManager.to_panda_path`` / ``Filename.fromOsSpecific``; the
splash flow and menus apply that in ``ui/splash_screen`` and ``ui/base_screen``.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Display / render configuration MUST run before ShowBase constructs the window.
# ---------------------------------------------------------------------------
from panda3d.core import (
    GraphicsPipe,
    GraphicsPipeSelection,
    WindowProperties,
    loadPrcFileData,
)

loadPrcFileData("", "aspect-ratio 0")
loadPrcFileData("", "view-unused-space #f")

_ENGINE_PRC_INCLUDED_WIN_SIZE: bool = False
_ENGINE_PROBE_DIMENSIONS: Optional[tuple[int, int]] = None


def _probe_pipe_display_dimensions() -> Optional[tuple[int, int]]:
    """Return (width, height) from the default GraphicsPipe, or None if unknown."""
    pipe = None
    get_global = getattr(GraphicsPipe, "get_global_ptr", None)
    if callable(get_global):
        try:
            pipe = get_global()
        except Exception:
            pipe = None
    if pipe is None:
        try:
            pipe = GraphicsPipeSelection.get_global_ptr().get_default_pipe()
        except Exception:
            pipe = None
    if pipe is None:
        return None

    try:
        w = int(pipe.get_display_width())
        h = int(pipe.get_display_height())
    except Exception:
        return None

    if w <= 0 or h <= 0:
        return None
    return (w, h)


def _apply_engine_prc_before_showbase() -> None:
    """
    Borderless-friendly PRC: no exclusive fullscreen; optional win-size only when known.

    If the pipe reports 0×0, omit ``win-size`` so Panda picks safe defaults;
    resize after open.
    """
    global _ENGINE_PRC_INCLUDED_WIN_SIZE, _ENGINE_PROBE_DIMENSIONS

    dims = _probe_pipe_display_dimensions()
    _ENGINE_PROBE_DIMENSIONS = dims

    lines: list[str] = [
        "aspect-ratio 0",
        "view-unused-space #f",
        "window-title Universal Racing Game // Neural Link",
        "fullscreen #f",
        "undecorated #t",
        "win-fixed-size false",
        "framebuffer-software #f",
        "framebuffer-multisample 1",
        "multisamples 4",
        "textures-power-2 none",
        "sync-video #t",
        "want-high-dpi true",
    ]

    if dims is not None:
        w, h = dims
        lines.insert(0, f"win-size {int(w)} {int(h)}")
        _ENGINE_PRC_INCLUDED_WIN_SIZE = True
    else:
        _ENGINE_PRC_INCLUDED_WIN_SIZE = False

    loadPrcFileData("", "\n".join(lines))


_apply_engine_prc_before_showbase()

from direct.showbase.ShowBase import ShowBase  # noqa: E402
from direct.task import Task  # noqa: E402

from core.path_manager import PathManager
from ui.main_menu import MainMenu
from ui.splash_screen import SplashScreen


LOGGER: logging.Logger = logging.getLogger(__name__)

_POST_INIT_TASK = "post-init"
_UI_SETUP_TASK = "ui-setup"

# How long to wait (seconds) for the OS to finalise window geometry before
# querying the real framebuffer size in ``initial_ui_setup``.
_WINDOW_SETTLE_DELAY: float = 0.25


class RacingGame(ShowBase):
    """Initialize the engine and orchestrate splash/menu states."""

    def __init__(self) -> None:
        super().__init__()

        # ------------------------------------------------------------------ #
        # 1. Window setup — size, position, decorations                       #
        # ------------------------------------------------------------------ #
        wp = WindowProperties()
        wp.setUndecorated(True)
        wp.setFullscreen(False)
        wp.setFixedSize(False)
        wp.setTitle("Universal Racing Game // Neural Link")

        detected_width, detected_height = 1280, 720
        try:
            pipe = self.pipe
            if pipe is not None:
                w = int(pipe.get_display_width())
                h = int(pipe.get_display_height())
                if w > 0 and h > 0:
                    detected_width, detected_height = w, h
        except Exception:
            pass

        wp.setSize(detected_width, detected_height)
        wp.setOrigin(0, 0)
        if self.win is not None:
            self.win.requestProperties(wp)

        # ------------------------------------------------------------------ #
        # 2. Immediately sync 2D coordinate system to the requested size      #
        #    (requestProperties is asynchronous; this gives a best-first      #
        #    approximation that ``initial_ui_setup`` will correct later).     #
        # ------------------------------------------------------------------ #
        self._sync_2d_to_window()
        self.force_ui_remap()

        self.disableMouse()

        # ------------------------------------------------------------------ #
        # 3. Language + splash                                                #
        # ------------------------------------------------------------------ #
        self.lang: Dict[str, str] = self._load_language("en")
        self.main_menu: MainMenu | None = None
        self.splash_screen = SplashScreen(
            game_base=self,
            on_complete=self._on_splash_complete,
            soundtrack_name="Tarmac_Predator.mp3",
        )
        self.splash_screen.start()

        # ------------------------------------------------------------------ #
        # 4. Event hooks                                                       #
        # ------------------------------------------------------------------ #
        self.accept("aspectRatioChanged", self._on_aspect_ratio_changed)
        self.accept("window-event", self._on_window_event_for_ui)

        # Re-broadcast so listeners (splash cover scale, etc.) run now.
        if self.win is not None:
            self.messenger.send("window-event", [self.win])

        if sys.platform.startswith("linux"):
            os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

        # ------------------------------------------------------------------ #
        # 5. Deferred UI setup — waits for the OS to honour the resize       #
        # ------------------------------------------------------------------ #
        self.taskMgr.remove(_UI_SETUP_TASK)
        self.taskMgr.doMethodLater(_WINDOW_SETTLE_DELAY, self.initial_ui_setup, _UI_SETUP_TASK)

    # ---------------------------------------------------------------------- #
    # Deferred initialisation                                                  #
    # ---------------------------------------------------------------------- #

    def initial_ui_setup(self, task: Task) -> object:
        """
        Runs after the OS has (likely) applied the resize request.

        Steps:
          1. Re-sync 2D nodes from the actual framebuffer.
          2. Re-map aspect2d anchor nodes.
          3. Re-bind mouseWatcher to the primary DisplayRegion.
          4. Enable mouse picking.
          5. Rebuild the main menu if already mounted.
        """
        # --- 1 & 2: sync coordinate system to real window size ---
        self._sync_2d_to_window()
        self.force_ui_remap()

        # --- 3: broadcast so all listeners recalculate layout ---
        self.updateAspectRatio()
        self.messenger.send("aspectRatioChanged")

        # --- 4: fix mouseWatcher → DisplayRegion link ---
        self._bind_mouse_watcher_to_display_region()
        self.enableMouse()

        # --- 5: rebuild menu if it was already created (rare path) ---
        if self.main_menu is not None:
            LOGGER.debug("initial_ui_setup: rebuilding menu at native resolution.")
            self.main_menu.apply_responsive_scale()
            self.main_menu.rebuild_ui()
            self.main_menu.show()

        self.global_ui_refresh()
        return Task.done

    # ---------------------------------------------------------------------- #
    # Core helpers                                                             #
    # ---------------------------------------------------------------------- #

    def force_ui_remap(self) -> None:
        """
        Recalculate ``a2dLeftCenter`` / ``a2dRightCenter`` / ``a2dTopCenter`` /
        ``a2dBottomCenter`` from the *current* aspect ratio.

        Called after every resize so anchor-parented menus move to the correct
        screen edge without rebuilding the widget tree.
        """
        ar = self.getAspectRatio()
        if ar <= 0.0:
            return
        self.a2dTopCenter.setPos(0, 0, 1)
        self.a2dBottomCenter.setPos(0, 0, -1)
        self.a2dLeftCenter.setPos(-ar, 0, 0)
        self.a2dRightCenter.setPos(ar, 0, 0)
        self.a2dTopLeft.setPos(-ar, 0, 1)
        self.a2dTopRight.setPos(ar, 0, 1)
        self.a2dBottomLeft.setPos(-ar, 0, -1)
        self.a2dBottomRight.setPos(ar, 0, -1)

    def global_ui_refresh(self) -> None:
        """Broadcast aspect change so splash, menus and listeners stay in sync."""
        self.force_ui_remap()
        self.messenger.send("aspectRatioChanged")

    def _sync_2d_to_window(self) -> None:
        """
        Apply ``adjustWindowAspectRatio`` and ``pixel2d`` scale from the real
        (or requested) framebuffer dimensions.

        This mirrors what ShowBase.windowEvent does, but can be called at any
        time rather than waiting for the next Panda event loop tick.
        """
        if self.win is None:
            return

        ar = self.getAspectRatio()
        if ar and ar > 0:
            self.adjustWindowAspectRatio(ar)

        # pixel2d scale: 2 pixels per unit in each axis.
        xsize, ysize = self.getSize()
        if xsize > 0 and ysize > 0:
            self.pixel2d.setScale(2.0 / xsize, 1.0, 2.0 / ysize)

    def _bind_mouse_watcher_to_display_region(self) -> None:
        """
        Explicitly associate the MouseWatcher node with the primary window
        DisplayRegion.  Without this, after a resolution shift the watcher
        can report ``isActive() == False`` and mouse clicks miss buttons.
        """
        if self.win is None or self.mouseWatcher is None:
            return
        dr = self.win.getDisplayRegion(0)
        if dr is not None:
            self.mouseWatcher.node().setDisplayRegion(dr)

    # ---------------------------------------------------------------------- #
    # Window / aspect event handlers                                           #
    # ---------------------------------------------------------------------- #

    def windowEvent(self, win) -> None:  # type: ignore[override]
        """Preserve ShowBase bookkeeping; refresh UI after framebuffer changes."""
        super().windowEvent(win)
        self._sync_2d_to_window()
        self.force_ui_remap()
        self._bind_mouse_watcher_to_display_region()
        self.global_ui_refresh()

    def _on_aspect_ratio_changed(self, *_args: object) -> None:
        if self.main_menu is not None:
            self.main_menu.refresh_display_layout()

    def _on_window_event_for_ui(self, *_args: object) -> None:
        self.global_ui_refresh()

    # ---------------------------------------------------------------------- #
    # Language                                                                 #
    # ---------------------------------------------------------------------- #

    def _load_language(self, lang_code: str) -> Dict[str, str]:
        """Load language dictionary from assets/lang with fallback."""
        fallback_lang: Dict[str, str] = {
            "ui_start": "Start",
            "ui_exit": "Exit",
            "ui_settings": "Settings",
            "ui_back": "Back",
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

    # ---------------------------------------------------------------------- #
    # State transitions                                                        #
    # ---------------------------------------------------------------------- #

    def _on_splash_complete(self) -> None:
        """
        Transition from splash to main menu.

        Deferred by one short task so the splash teardown finishes fully
        before the menu widget tree is constructed.
        """
        self.main_menu = MainMenu(
            game_base=self,
            labels=self.lang,
            on_settings=self._on_settings,
            on_exit=self._on_exit,
        )
        self.taskMgr.remove(_POST_INIT_TASK)
        self.taskMgr.doMethodLater(0.1, self._post_splash_build, _POST_INIT_TASK)

    def _post_splash_build(self, task: Task) -> object:
        """
        After the splash teardown frame, rebuild the menu at the real
        aspect ratio (the window may have been resized during splash).
        """
        if self.main_menu is None:
            return Task.done

        # Ensure coordinate system is up-to-date before building widgets.
        self._sync_2d_to_window()
        self.force_ui_remap()
        self.updateAspectRatio()

        self.main_menu.apply_responsive_scale()
        self.main_menu.rebuild_ui()
        self.force_ui_remap()
        return Task.done

    def _on_settings(self) -> None:
        LOGGER.debug("Settings opened from main menu.")

    def _on_exit(self) -> None:
        self.cleanup()
        self.userExit()

    def cleanup(self) -> None:
        """Release state managers and UI."""
        self.taskMgr.remove(_POST_INIT_TASK)
        self.taskMgr.remove(_UI_SETUP_TASK)
        self.ignoreAll()
        if self.splash_screen is not None:
            self.splash_screen.cleanup()
        if self.main_menu is not None:
            self.main_menu.cleanup()
            self.main_menu = None


if __name__ == "__main__":
    game = RacingGame()
    game.run()