"""Main menu UI module."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Tuple, Union
from typing import Sequence as TypingSequence

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectGui import DGG
from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import NodePath, TextNode, TransparencyAttrib

from core.path_manager import PathManager

from ui.base_screen import GameUIBase, solid_color_menu_fallback_card


LOGGER: logging.Logger = logging.getLogger(__name__)

# Aspect2d layout (local units; scaled by _CYBER_PARENT_SCALE).
_CYBER_BTN_HALF_W: float = 5.35
_CYBER_BTN_HALF_H: float = 0.66
_CYBER_OUTER_GLOW_PAD: float = 0.16
_CYBER_INNER_GLOW_PAD: float = 0.07
_CYBER_PARENT_SCALE: float = 0.078
_CYBER_LEFT_MARGIN: float = 0.54
_CYBER_VERTICAL_STEP: float = 0.168
_CYBER_ROW_TOP_Z: float = 0.13

_BASE_FRAME_RGBA: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.6)
_ROLL_FRAME_RGBA: Tuple[float, float, float, float] = (0.02, 0.12, 0.14, 0.72)


def _gui_rgba4(
    color: Union[
        Tuple[float, float, float, float],
        TypingSequence[float],
        Mapping[str, float],
    ],
) -> Tuple[float, float, float, float]:
    """Normalize GUI colors to a flat (R, G, B, A) tuple of real floats for DirectGui."""
    if isinstance(color, Mapping):
        r = float(color.get("r", color.get("red", 0.0)))
        g = float(color.get("g", color.get("green", 0.0)))
        b = float(color.get("b", color.get("blue", 0.0)))
        a = float(color.get("a", color.get("alpha", color.get("opacity", 1.0))))
        return (r, g, b, a)
    return (
        float(color[0]),
        float(color[1]),
        float(color[2]),
        float(color[3]),
    )


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
        self._cyber_rows: List[Tuple[NodePath, DirectFrame, DirectFrame, DirectButton]] = []
        self._cyber_font_node = None
        self._hover_sfx = None
        self._hover_sfx_absent: bool = False

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

        for _parent, outer, inner, btn in self._cyber_rows:
            btn.destroy()
            inner.destroy()
            outer.destroy()
            _parent.removeNode()
        self._cyber_rows.clear()

        self.buttons.clear()

    def _resolve_cyber_font(self):
        """Prefer Orbitron / Rajdhani; fallback to built-in sans (caller uppercases text)."""
        if self._cyber_font_node is not None:
            return self._cyber_font_node

        for candidate in (
            "Orbitron-Bold.ttf",
            "Orbitron-Regular.ttf",
            "Rajdhani-Bold.ttf",
            "Rajdhani-Regular.ttf",
            "DejaVuSans.ttf",
            "NotoSans-Regular.ttf",
        ):
            font_path: Optional[Path] = PathManager.resolve_font_file(candidate)
            if font_path is None:
                continue
            try:
                self._cyber_font_node = self.game_base.loader.loadFont(str(font_path))
                return self._cyber_font_node
            except OSError:
                continue

        LOGGER.info("No sci-fi font under assets/fonts; using default with uppercase labels.")
        self._cyber_font_node = None
        return None

    def _ensure_hover_sound(self):
        """Lazy-load UI hover SFX when assets/audio/UI_hover.wav exists."""
        if self._hover_sfx is not None:
            return self._hover_sfx
        if self._hover_sfx_absent:
            return None

        path = PathManager.resolve_audio_file("UI_hover.wav")
        if path is None:
            self._hover_sfx_absent = True
            return None
        try:
            self._hover_sfx = self.game_base.loader.loadSfx(str(path))
            self._hover_sfx.setVolume(0.35)
        except OSError as exc:
            LOGGER.warning("Could not load UI_hover.wav: %s", exc)
            self._hover_sfx_absent = True
            self._hover_sfx = None
        return self._hover_sfx

    def _glow_alpha_boost(self) -> float:
        """Slightly stronger halo when a simplepbr-style pipeline is present (optional bloom)."""
        if getattr(self.game_base, "simplepbr", None) is not None:
            return 0.06
        return 0.0

    def _cyber_hover_enter(self, parent: NodePath) -> None:
        base_scale = float(parent.getPythonTag("cyber_base_scale"))
        parent.setScale(base_scale * 1.05)
        sfx = self._ensure_hover_sound()
        if sfx is not None:
            sfx.play()

    def _cyber_hover_exit(self, parent: NodePath) -> None:
        base_scale = float(parent.getPythonTag("cyber_base_scale"))
        parent.setScale(base_scale)

    def create_cyber_button(
        self,
        button_key: str,
        text: str,
        command: Callable[[], None],
        pos: Tuple[float, float, float],
        *,
        accent: str = "cyan",
    ) -> DirectButton:
        """
        Build a neon-outlined cyber button under aspect2d with layered glow and hover feedback.

        Visuals use DirectGui four-way frameColor / text_fg for normal, pressed, rollover, disabled.
        """
        display_text = text.upper()
        font = self._resolve_cyber_font()

        accent_key = accent.lower()
        if accent_key == "magenta":
            neon = _gui_rgba4((1.0, 0.0, 1.0, 1.0))
            neon_bright = _gui_rgba4((1.0, 0.35, 1.0, 1.0))
            glow_rgb = (float(neon[0]), float(neon[1]), float(neon[2]))
        else:
            neon = _gui_rgba4((0.0, 1.0, 1.0, 1.0))
            neon_bright = _gui_rgba4((0.35, 1.0, 1.0, 1.0))
            glow_rgb = (float(neon[0]), float(neon[1]), float(neon[2]))

        boost = self._glow_alpha_boost()
        outer_alpha = min(0.22 + boost, 0.38)
        inner_alpha = min(0.14 + boost, 0.28)

        root = self.game_base.aspect2d.attachNewNode(f"cyber_btn_{button_key}")
        root.setPos(pos[0], pos[1], pos[2])
        root.setPythonTag("cyber_base_scale", _CYBER_PARENT_SCALE)
        root.setScale(_CYBER_PARENT_SCALE)

        hw = _CYBER_BTN_HALF_W
        hh = _CYBER_BTN_HALF_H

        outer_glow = DirectFrame(
            frameSize=(
                -hw - _CYBER_OUTER_GLOW_PAD,
                hw + _CYBER_OUTER_GLOW_PAD,
                -hh - _CYBER_OUTER_GLOW_PAD,
                hh + _CYBER_OUTER_GLOW_PAD,
            ),
            frameColor=(
                float(glow_rgb[0]),
                float(glow_rgb[1]),
                float(glow_rgb[2]),
                float(outer_alpha * 0.35),
            ),
            relief=DGG.FLAT,
            parent=root,
        )
        outer_glow.setBin("gui-popup", -2)
        outer_glow.setTransparency(TransparencyAttrib.MAlpha)

        inner_glow = DirectFrame(
            frameSize=(
                -hw - _CYBER_INNER_GLOW_PAD,
                hw + _CYBER_INNER_GLOW_PAD,
                -hh - _CYBER_INNER_GLOW_PAD,
                hh + _CYBER_INNER_GLOW_PAD,
            ),
            frameColor=(
                float(glow_rgb[0]),
                float(glow_rgb[1]),
                float(glow_rgb[2]),
                float(inner_alpha),
            ),
            relief=DGG.FLAT,
            parent=root,
        )
        inner_glow.setBin("gui-popup", -1)
        inner_glow.setTransparency(TransparencyAttrib.MAlpha)

        solid_press = _gui_rgba4((neon[0], neon[1], neon[2], 0.96))

        # DirectGui expects either one (R,G,B,A) or exactly four state tuples; use tuple not list.
        frame_colors: Tuple[Tuple[float, float, float, float], ...] = (
            _gui_rgba4(_BASE_FRAME_RGBA),
            solid_press,
            _gui_rgba4(_ROLL_FRAME_RGBA),
            _gui_rgba4((0.12, 0.12, 0.12, 0.45)),
        )
        text_fg: Tuple[Tuple[float, float, float, float], ...] = (
            neon,
            neon_bright,
            _gui_rgba4((1.0, 1.0, 1.0, 1.0)),
            _gui_rgba4((0.35, 0.35, 0.35, 0.65)),
        )

        btn = DirectButton(
            text=display_text,
            text_align=TextNode.ACenter,
            text_scale=0.62,
            text_font=font,
            text_fg=text_fg,
            frameSize=(-hw, hw, -hh, hh),
            frameColor=frame_colors,
            relief=DGG.RIDGE,
            borderWidth=(0.012, 0.012),
            pad=(0.28, 0.14),
            pressEffect=False,
            command=command,
            parent=root,
        )
        btn.setBin("gui-popup", 0)
        btn.setTransparency(TransparencyAttrib.MAlpha)

        btn.bind(DGG.ENTER, lambda _e, p=root: self._cyber_hover_enter(p))
        btn.bind(DGG.EXIT, lambda _e, p=root: self._cyber_hover_exit(p))

        self._cyber_rows.append((root, outer_glow, inner_glow, btn))
        self.buttons[button_key] = btn
        btn.show()
        return btn

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
        """Create cyber-styled DirectButtons in aspect2d along the left column."""
        mouse_watcher = self.game_base.mouseWatcherNode
        is_active: bool = bool(
            mouse_watcher
            and hasattr(mouse_watcher, "isActive")
            and mouse_watcher.isActive()
        )
        if not is_active:
            LOGGER.warning("mouseWatcherNode is not active. Menu input may not work.")

        menu_aspect: float = self.aspect_ratio()
        left_x: float = -menu_aspect + _CYBER_LEFT_MARGIN
        z_top: float = _CYBER_ROW_TOP_Z

        self.create_cyber_button(
            "settings",
            self.labels.get("ui_settings", "Settings"),
            lambda: messenger.send("menu-settings"),
            (left_x, 0.0, z_top),
            accent="cyan",
        )
        self.create_cyber_button(
            "exit",
            self.labels.get("ui_exit", "Exit"),
            lambda: messenger.send("menu-exit"),
            (left_x, 0.0, z_top - _CYBER_VERTICAL_STEP),
            accent="magenta",
        )
