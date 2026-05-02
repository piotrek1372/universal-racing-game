"""Splash screen flow for the Universal Racing Game."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, List, Optional

from direct.gui.OnscreenImage import OnscreenImage
from direct.interval.IntervalGlobal import Func, Parallel, Sequence, Wait
from direct.showbase.DirectObject import DirectObject
from panda3d.core import AudioSound, TransparencyAttrib

from core.path_manager import PathManager
from ui.base_screen import GameUIBase


LOGGER: logging.Logger = logging.getLogger(__name__)

# Native aspect ratio of the splash artwork.  Splash images are assumed to be
# produced at 16:9; update this constant if a different master is supplied.
_ASSET_ASPECT_RATIO: float = 16.0 / 9.0

_BACKGROUND_BIN_SORT: int = -100


class SplashScreen(GameUIBase, DirectObject):
    """
    Create and run the splash sequence with optional background audio.

    Splash images are displayed as ``OnscreenImage`` nodes parented to
    ``render2d``.  A "cover" scaling strategy ensures the artwork always
    fills the window without distortion:

    * **Wider than artwork** (``win_ar > asset_ar``): scale by the width
      axis so the image reaches the horizontal edges; the image is taller
      than the screen and crops top/bottom.
    * **Narrower than artwork** (``win_ar <= asset_ar``): scale by the
      height axis so the image reaches the vertical edges; the image is
      wider than the screen and crops left/right.

    The ``render2d`` coordinate system spans ``[-win_ar, +win_ar]`` on X and
    ``[-1, +1]`` on Z (up).  An ``OnscreenImage`` with ``setScale(sx, 1, sz)``
    occupies ``[-sx, +sx]`` × ``[-sz, +sz]``.  Cover requires ``sx >= win_ar``
    *and* ``sz >= 1`` while maintaining ``sx / sz == asset_ar``.
    """

    def __init__(
        self,
        game_base,
        on_complete: Callable[[], None],
        soundtrack_name: str = "Tarmac_Predator.mp3",
    ) -> None:
        GameUIBase.__init__(self, game_base)
        DirectObject.__init__(self)
        self.on_complete = on_complete
        self.sequence: Optional[Sequence] = None
        self.bg_music: Optional[AudioSound] = self._load_background_music(soundtrack_name)
        self._splash_images: List[OnscreenImage] = []

    # ---------------------------------------------------------------------- #
    # Public interface                                                          #
    # ---------------------------------------------------------------------- #

    def start(self) -> None:
        """Start splash sequence and register viewport change listeners."""
        self._splash_images.clear()
        self.accept("window-event", self._on_splash_viewport_changed)
        self.accept("aspectRatioChanged", self._on_splash_viewport_changed)
        self.sequence = self._build_sequence()
        self.sequence.start()

    def cleanup(self) -> None:
        """Stop sequence and release audio resources."""
        self.ignoreAll()
        if self.sequence is not None:
            self.sequence.finish()
            self.sequence = None
        if self.bg_music is not None:
            self.bg_music.stop()
        self._splash_images.clear()

    # ---------------------------------------------------------------------- #
    # Viewport / scaling                                                        #
    # ---------------------------------------------------------------------- #

    def _on_splash_viewport_changed(self, *_args: object) -> None:
        """Re-apply cover scale whenever the window is resized or aspect changes."""
        for img in self._splash_images:
            if img is None or img.isEmpty():
                continue
            self._apply_cover_scale(img)

    @staticmethod
    def _apply_cover_scale(image: OnscreenImage) -> None:
        """
        Scale ``image`` (parented to ``render2d``) to cover the full window.

        ``render2d`` coordinate system:
            X ∈ [-win_ar, +win_ar],  Z ∈ [-1, +1]

        An ``OnscreenImage`` with ``setScale(sx, 1, sz)`` occupies:
            X: [-sx, +sx],  Z: [-sz, +sz]

        Cover condition: ``sx >= win_ar`` AND ``sz >= 1`` with ``sx/sz == asset_ar``.

        Case A — window wider than artwork (win_ar > asset_ar):
            Anchor on width  →  sx = win_ar  →  sz = win_ar / asset_ar  (≥1 ✓)

        Case B — window same width or narrower (win_ar <= asset_ar):
            Anchor on height →  sz = 1       →  sx = asset_ar           (≥win_ar ✓)
        """
        gb = image.getPythonTag("splash_game_base")
        if gb is None:
            return

        win_ar = float(gb.getAspectRatio())
        if win_ar <= 0.0:
            win_ar = _ASSET_ASPECT_RATIO

        if win_ar > _ASSET_ASPECT_RATIO:
            # Window is wider than the 16:9 artwork.  Anchor to width.
            sx = win_ar
            sz = win_ar / _ASSET_ASPECT_RATIO
        else:
            # Window is narrower than (or equal to) 16:9.  Anchor to height.
            sz = 1.0
            sx = _ASSET_ASPECT_RATIO

        image.setScale(sx, 1.0, sz)
        image.setPos(0.0, 0.0, 0.0)

    # ---------------------------------------------------------------------- #
    # Asset loading                                                             #
    # ---------------------------------------------------------------------- #

    def _create_splash(self, image_name: str) -> Optional[OnscreenImage]:
        """
        Create a fullscreen splash ``OnscreenImage`` under ``render2d``.

        The image path is resolved through ``PathManager`` and normalized via
        ``to_panda_path`` for Windows/Linux compatibility.
        """
        image_path: Optional[Path] = PathManager.resolve_image_file(image_name)
        if image_path is None:
            LOGGER.warning("Splash image missing: %s", image_name)
            return None

        panda_path = PathManager.to_panda_path(image_path)
        try:
            img = OnscreenImage(
                image=panda_path,
                parent=self.game_base.render2d,
                pos=(0.0, 0.0, 0.0),
            )
        except OSError as exc:
            LOGGER.warning("Could not load splash image %s: %s", image_path, exc)
            return None

        img.setTransparency(TransparencyAttrib.MAlpha)
        img.setColorScale(1, 1, 1, 0)           # start fully transparent
        img.setBin("background", _BACKGROUND_BIN_SORT)
        img.setDepthWrite(False)
        img.setDepthTest(False)

        # Store a reference to game_base so the static helper can query AR.
        img.setPythonTag("splash_game_base", self.game_base)

        # Apply initial cover scale immediately.
        self._apply_cover_scale(img)
        self._splash_images.append(img)
        return img

    def _load_background_music(self, filename: str) -> Optional[AudioSound]:
        """Load soundtrack from ``assets/audio`` via ``PathManager``."""
        resolved: Optional[Path] = PathManager.resolve_audio_file(filename)
        if resolved is None:
            LOGGER.warning("Background music not found: %s", filename)
            return None

        panda_path = PathManager.to_panda_path(resolved)
        try:
            music: Optional[AudioSound] = self.game_base.loader.loadMusic(panda_path)
        except OSError as error:
            LOGGER.warning("Failed to load background music %s: %s", resolved, error)
            return None

        if music is None:
            LOGGER.warning("No music object returned for %s", resolved)
            return None

        music.setLoop(False)
        return music

    # ---------------------------------------------------------------------- #
    # Sequence construction                                                     #
    # ---------------------------------------------------------------------- #

    def _build_sequence(self) -> Sequence:
        """Build and return the full splash interval sequence."""
        splash_nodes: list[OnscreenImage] = []
        for image_name in ("splash1.png", "splash2.png", "splash3.png"):
            splash = self._create_splash(image_name)
            if splash is not None and not splash.isEmpty():
                splash_nodes.append(splash)

        if not splash_nodes:
            LOGGER.warning("No splash images available — proceeding directly to main menu.")
            return Sequence(Func(self.ignoreAll), Func(self.on_complete))

        sequence: Sequence = Sequence()
        first_splash: OnscreenImage = splash_nodes[0]
        music_start = (
            Func(self.bg_music.play) if self.bg_music is not None else Wait(0.0)
        )

        # Short initial hold so the window finishes drawing before fade-in.
        sequence.append(Wait(0.75))
        sequence.append(
            Parallel(
                music_start,
                first_splash.colorScaleInterval(
                    1.5,
                    (1, 1, 1, 1),
                    startColorScale=(1, 1, 1, 0),
                ),
            )
        )
        sequence.append(Wait(3.0))
        sequence.append(
            first_splash.colorScaleInterval(
                1.5,
                (1, 1, 1, 0),
                startColorScale=(1, 1, 1, 1),
            )
        )
        sequence.append(Func(first_splash.destroy))

        for splash in splash_nodes[1:]:
            sequence.append(
                splash.colorScaleInterval(
                    1.5,
                    (1, 1, 1, 1),
                    startColorScale=(1, 1, 1, 0),
                )
            )
            sequence.append(Wait(3.0))
            sequence.append(
                splash.colorScaleInterval(
                    1.5,
                    (1, 1, 1, 0),
                    startColorScale=(1, 1, 1, 1),
                )
            )
            sequence.append(Func(splash.destroy))

        sequence.append(Func(self.ignoreAll))
        sequence.append(Func(self.on_complete))
        return sequence