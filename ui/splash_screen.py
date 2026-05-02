"""Splash screen flow for the Universal Racing Game."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

from direct.interval.IntervalGlobal import Func, Parallel, Sequence, Wait
from panda3d.core import AudioSound, CardMaker, NodePath, TransparencyAttrib

from core.path_manager import PathManager


LOGGER: logging.Logger = logging.getLogger(__name__)


class SplashScreen:
    """Create and run the splash sequence with optional background audio."""

    def __init__(
        self,
        game_base,
        on_complete: Callable[[], None],
        soundtrack_name: str = "Tarmac_Predator.mp3",
    ) -> None:
        self.game_base = game_base
        self.on_complete = on_complete
        self.sequence: Optional[Sequence] = None
        self.bg_music: Optional[AudioSound] = self._load_background_music(soundtrack_name)

    def start(self) -> None:
        """Start splash sequence."""
        self.sequence = self._build_sequence()
        self.sequence.start()

    def cleanup(self) -> None:
        """Stop sequence and audio resources."""
        if self.sequence is not None:
            self.sequence.finish()
            self.sequence = None
        if self.bg_music is not None:
            self.bg_music.stop()

    def _load_background_music(self, filename: str) -> Optional[AudioSound]:
        """Load soundtrack from assets/audio or assets/soundtracks."""
        resolved_audio_path: Optional[Path] = PathManager.resolve_audio_file(filename)
        if resolved_audio_path is None:
            LOGGER.warning("Background music not found: %s", filename)
            return None

        try:
            music: Optional[AudioSound] = self.game_base.loader.loadMusic(
                str(resolved_audio_path)
            )
        except OSError as error:
            LOGGER.warning("Failed to load background music %s: %s", resolved_audio_path, error)
            return None

        if music is None:
            LOGGER.warning("No music object returned for %s", resolved_audio_path)
            return None

        music.setLoop(False)
        return music

    def _create_splash(self, image_name: str) -> Optional[NodePath]:
        """Create one full-screen splash card with alpha enabled."""
        image_path: Optional[Path] = PathManager.resolve_image_file(image_name)
        if image_path is None:
            LOGGER.warning("Splash image missing: %s", image_name)
            return None

        cm: CardMaker = CardMaker(f"splash_{image_name}")
        cm.setFrameFullscreenQuad()
        card: NodePath = self.game_base.render2d.attachNewNode(cm.generate())
        texture = self.game_base.loader.loadTexture(str(image_path))
        card.setTexture(texture)
        card.setTransparency(TransparencyAttrib.MAlpha)
        card.setColorScale(1, 1, 1, 0)
        return card

    def _build_sequence(self) -> Sequence:
        """Build the splash sequence and transition to menu."""
        splash_nodes: list[NodePath] = []
        for image_name in ("splash1.png", "splash2.png", "splash3.png"):
            splash = self._create_splash(image_name)
            if splash is not None and not splash.isEmpty():
                splash_nodes.append(splash)

        if not splash_nodes:
            LOGGER.warning("No splash images available, proceeding to main menu.")
            return Sequence(Func(self.on_complete))

        sequence: Sequence = Sequence()
        first_splash: NodePath = splash_nodes[0]
        music_start = Func(self.bg_music.play) if self.bg_music is not None else Wait(0.0)

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
        sequence.append(Func(first_splash.removeNode))

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
            sequence.append(Func(splash.removeNode))

        sequence.append(Func(self.on_complete))
        return sequence
