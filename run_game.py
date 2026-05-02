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

# Populated by _apply_engine_prc_before_showbase for post-init borderless sizing.
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

    If the pipe reports 0×0, omit ``win-size`` so Panda picks safe defaults; resize after open.
    """
    global _ENGINE_PRC_INCLUDED_WIN_SIZE, _ENGINE_PROBE_DIMENSIONS

    dims = _probe_pipe_display_dimensions()
    _ENGINE_PROBE_DIMENSIONS = dims

    # aspect-ratio 0: do not lock to a fixed framebuffer aspect (prevents letterboxing).
    lines: list[str] = [
        "aspect-ratio 0",
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

_DEFERRED_MAIN_MENU_TASK = "urg-deferred-main-menu-show"


class RacingGame(ShowBase):
    """Initialize the engine and orchestrate splash/menu states."""

    def __init__(self) -> None:
        super().__init__()
        self.disableMouse()

        # Shell UI first so ``main_menu`` exists before any ``window-event`` / 2-D sync side effects.
        self.lang: Dict[str, str] = self._load_language("en")
        self.main_menu: MainMenu | None = None
        self.splash_screen = SplashScreen(
            game_base=self,
            on_complete=self._on_splash_complete,
            soundtrack_name="Tarmac_Predator.mp3",
        )
        self.splash_screen.start()

        self.accept("aspectRatioChanged", self._on_viewport_topology_changed)
        self.accept("window-event", self._on_viewport_topology_changed)

        self._configure_window_after_open()
        self._sync_2d_after_window_props()

        if self.win is not None:
            self.messenger.send("window-event", [self.win])

    def windowEvent(self, win) -> None:  # type: ignore[override]
        """Preserve ShowBase window bookkeeping; refresh UI after framebuffer changes."""
        super().windowEvent(win)
        if hasattr(self, "main_menu") and self.main_menu:
            self.main_menu.refresh_display_layout()

    def _sync_2d_after_window_props(self) -> None:
        """
        Match ShowBase.windowEvent: apply aspect2d / pixel2d from the real window size.

        requestProperties alone may not run windowEvent immediately; without this,
        aspect2d stays at the default (~800×600) while the framebuffer is larger.

        Does not emit ``window-event``; callers (e.g. ``__init__``) send once after setup.
        """
        if self.win is None:
            return
        ar = self.getAspectRatio()
        if ar and ar > 0:
            self.adjustWindowAspectRatio(ar)
        if self.win.hasSize() and self.win.getSbsLeftYSize() != 0:
            self.pixel2d.setScale(
                2.0 / self.win.getSbsLeftXSize(),
                1.0,
                2.0 / self.win.getSbsLeftYSize(),
            )
        else:
            xsize, ysize = self.getSize()
            if xsize > 0 and ysize > 0:
                self.pixel2d.setScale(2.0 / xsize, 1.0, 2.0 / ysize)

    def _on_viewport_topology_changed(self, *_args: object) -> None:
        if hasattr(self, "main_menu") and self.main_menu:
            self.main_menu.refresh_display_layout()

    def _resolve_borderless_dimensions(self) -> Optional[tuple[int, int]]:
        """Prefer boot probe; retry pipe; finally use current framebuffer size."""
        if _ENGINE_PROBE_DIMENSIONS is not None:
            return _ENGINE_PROBE_DIMENSIONS
        retry = _probe_pipe_display_dimensions()
        if retry is not None:
            return retry
        if self.win is not None:
            try:
                fb = self.win.getFbProperties()
                tw = int(fb.get_x_size())
                th = int(fb.get_y_size())
                if tw > 0 and th > 0:
                    return (tw, th)
            except Exception:
                pass
        return None

    def _configure_window_after_open(self) -> None:
        """Borderless windowed (not exclusive fullscreen) for X11/Mesa compatibility."""
        props = WindowProperties()
        props.setFullscreen(False)
        props.setUndecorated(True)
        props.setFixedSize(False)
        props.setTitle("Universal Racing Game // Neural Link")

        dims = self._resolve_borderless_dimensions()
        if dims is not None:
            w, h = int(dims[0]), int(dims[1])
            props.setSize(w, h)
            props.setOrigin(0, 0)

        if self.win is not None:
            self.win.requestProperties(props)

        if sys.platform.startswith("linux"):
            LOGGER.debug(
                "Linux HiDPI: GDK_SCALE / GDK_DPI_SCALE affect toolkit scaling when set before launch; "
                "want-high-dpi is enabled in engine PRC."
            )
            os.environ.setdefault(
                "QT_AUTO_SCREEN_SCALE_FACTOR", "1"
            )  # harmless if Qt tools run alongside

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

    def _on_splash_complete(self) -> None:
        """Transition from splash flow to main menu (UI shown next frame — window/input ready)."""
        self.main_menu = MainMenu(
            game_base=self,
            labels=self.lang,
            on_settings=self._on_settings,
            on_exit=self._on_exit,
        )
        self.taskMgr.remove(_DEFERRED_MAIN_MENU_TASK)
        self.taskMgr.doMethodLater(
            0.0,
            self._deferred_main_menu_show_task,
            _DEFERRED_MAIN_MENU_TASK,
        )

    def _deferred_main_menu_show_task(self, task: Task) -> object:
        if self.main_menu is not None:
            self.main_menu.show()
        return Task.done

    def _on_settings(self) -> None:
        """Handle settings action."""
        print("Settings clicked")

    def _on_exit(self) -> None:
        """Handle exit action."""
        self.cleanup()
        self.userExit()

    def cleanup(self) -> None:
        """Release state managers and UI."""
        self.taskMgr.remove(_DEFERRED_MAIN_MENU_TASK)
        self.ignoreAll()
        if self.splash_screen is not None:
            self.splash_screen.cleanup()
        if self.main_menu is not None:
            self.main_menu.cleanup()
            self.main_menu = None


if __name__ == "__main__":
    game = RacingGame()
    game.run()
