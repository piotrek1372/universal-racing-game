"""Base menu with shared cyberpunk DirectGui styling and teardown."""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectGui import DGG
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from panda3d.core import NodePath, TextNode, TransparencyAttrib

from core.path_manager import PathManager
from ui.base_screen import GameUIBase
from ui.player_profile import PlayerProfile

if TYPE_CHECKING:
    from ui.ui_manager import UIManager

LOGGER: logging.Logger = logging.getLogger(__name__)

# Button geometry (DirectGui local units); overall footprint scaled via `_cyber_ui_scale()`.
_CYBER_BTN_HALF_W: float = 5.35
_CYBER_BTN_HALF_H: float = 0.66
_CYBER_OUTER_GLOW_PAD: float = 0.16
_CYBER_INNER_GLOW_PAD: float = 0.07
_CYBER_PARENT_SCALE: float = 0.078
_CYBER_SCALE_REF_ASPECT: float = 16.0 / 9.0

# Anchor layout under `base.a2dLeftCenter` + optional `base.a2dBottomLeft`.
_LIST_ANCHOR_OFFSET_X: float = 0.1
_LIST_ROW_START_Z: float = 0.5
_LIST_ROW_STEP: float = 0.15
_SECTION_TITLE_GAP_Z: float = 0.14

_FOOTER_LOCAL_X: float = 0.2
_FOOTER_LOCAL_Z: float = 0.1

_BACK_BUTTON_ROW_INDEX: int = 12

_BASE_FRAME_RGBA: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.6)
_ROLL_FRAME_RGBA: Tuple[float, float, float, float] = (0.02, 0.12, 0.14, 0.72)


def gui_rgba4(
    color: Union[
        Tuple[float, float, float, float],
        Sequence[float],
        Mapping[str, float],
    ],
) -> Tuple[float, float, float, float]:
    """Normalize GUI colors to a flat (R, G, B, A) tuple for DirectGui."""
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


class BaseMenu(DirectObject, GameUIBase):
    """Responsive aspect2d layout via Panda anchor nodes (`a2dLeftCenter`, `a2dBottomLeft`)."""

    menu_key: str = "base"

    def __init__(
        self,
        game_base: Any,
        profile: PlayerProfile,
        ui_manager: UIManager,
        labels: Dict[str, str],
    ) -> None:
        DirectObject.__init__(self)
        GameUIBase.__init__(self, game_base)
        self.profile = profile
        self.ui_manager = ui_manager
        self.labels = labels

        self.list_parent: NodePath = game_base.a2dLeftCenter.attachNewNode(
            f"menu_list_{self.menu_key}"
        )
        self.list_parent.setPos(_LIST_ANCHOR_OFFSET_X, 0.0, 0.0)

        self._footer_parent: Optional[NodePath] = None

        self._cyber_rows: List[Tuple[NodePath, DirectFrame, DirectFrame, DirectButton]] = []
        self._extra_nodes: List[NodePath] = []
        self._extra_widgets: List[Any] = []
        self._cyber_font_node = None
        self._hover_sfx = None
        self._hover_sfx_absent: bool = False
        self._glitch_tasks: List[str] = []

    def reanchor_to_aspect_markers(self) -> None:
        """Re-parent the list hub to ``a2dLeftCenter`` after ``aspect2d`` / window updates."""
        if self.list_parent is None or self.list_parent.isEmpty():
            return
        self.list_parent.reparentTo(self.game_base.a2dLeftCenter)
        self.list_parent.setPos(_LIST_ANCHOR_OFFSET_X, 0.0, 0.0)

    def aspect_ratio(self) -> float:
        return float(self.game_base.getAspectRatio())

    def list_row_z(self, index: int) -> float:
        """Vertical slot index under `list_parent` (positive Z is upward from anchor)."""
        return _LIST_ROW_START_Z - index * _LIST_ROW_STEP

    def section_title_z(self) -> float:
        """Place headings above the first list row."""
        return _LIST_ROW_START_Z + _SECTION_TITLE_GAP_Z

    def attach_footer_anchor(self) -> NodePath:
        """Pin widgets (e.g. Disconnect) to `base.a2dBottomLeft` with safe insets."""
        if self._footer_parent is None:
            fp = self.game_base.a2dBottomLeft.attachNewNode(f"menu_footer_{self.menu_key}")
            fp.setPos(_FOOTER_LOCAL_X, 0.0, _FOOTER_LOCAL_Z)
            self._footer_parent = fp
        return self._footer_parent

    def _cyber_ui_scale(self) -> float:
        """Slightly shrink UI on ultrawide / tall windows so buttons stay proportional."""
        ar = max(0.55, min(3.2, self.aspect_ratio()))
        ref = _CYBER_SCALE_REF_ASPECT
        blend = math.sqrt(min(ar / ref, ref / ar))
        return _CYBER_PARENT_SCALE * (0.84 + 0.32 * blend)

    def _layout_scale_ratio(self) -> float:
        return self._cyber_ui_scale() / _CYBER_PARENT_SCALE

    def destroy(self) -> None:
        """Release GUI nodes, tasks, and input bindings."""
        self.ignoreAll()
        for task_name in self._glitch_tasks:
            self.game_base.taskMgr.remove(task_name)
        self._glitch_tasks.clear()

        for _parent, outer, inner, btn in self._cyber_rows:
            btn.destroy()
            inner.destroy()
            outer.destroy()
            _parent.removeNode()
        self._cyber_rows.clear()

        for w in self._extra_widgets:
            if hasattr(w, "destroy"):
                w.destroy()
        self._extra_widgets.clear()

        for np in self._extra_nodes:
            if np is not None and not np.isEmpty():
                np.removeNode()
        self._extra_nodes.clear()

        if self._footer_parent is not None and not self._footer_parent.isEmpty():
            self._footer_parent.removeNode()
        self._footer_parent = None

        if self.list_parent is not None and not self.list_parent.isEmpty():
            self.list_parent.removeNode()

    def _resolve_cyber_font(self):
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
                self._cyber_font_node = self.game_base.loader.loadFont(
                PathManager.to_panda_path(font_path)
            )
                return self._cyber_font_node
            except OSError:
                continue

        LOGGER.info("No sci-fi font under assets/fonts; using default with uppercase labels.")
        self._cyber_font_node = None
        return None

    def _ensure_hover_sound(self):
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
        command: Optional[Callable[[], None]],
        pos: Tuple[float, float, float],
        *,
        accent: str = "cyan",
        enabled: bool = True,
        parent: Optional[NodePath] = None,
    ) -> DirectButton:
        """Neon cyber button parented to `list_parent` (or an anchor) using local coordinates."""
        display_text = text.upper()
        font = self._resolve_cyber_font()

        accent_key = accent.lower()
        if accent_key == "magenta":
            neon = gui_rgba4((1.0, 0.0, 1.0, 1.0))
            neon_bright = gui_rgba4((1.0, 0.35, 1.0, 1.0))
            glow_rgb = (float(neon[0]), float(neon[1]), float(neon[2]))
        else:
            neon = gui_rgba4((0.0, 1.0, 1.0, 1.0))
            neon_bright = gui_rgba4((0.35, 1.0, 1.0, 1.0))
            glow_rgb = (float(neon[0]), float(neon[1]), float(neon[2]))

        boost = self._glow_alpha_boost()
        outer_alpha = min(0.22 + boost, 0.38)
        inner_alpha = min(0.14 + boost, 0.28)

        scale_applied = self._cyber_ui_scale()
        lr = self._layout_scale_ratio()
        text_scale = 0.62 * max(0.88, min(1.12, lr))
        border_xy = 0.012 * max(0.92, min(1.08, lr))
        pad_xy = (0.28 * max(0.94, min(1.06, lr)), 0.14 * max(0.94, min(1.06, lr)))

        root_parent = parent if parent is not None else self.list_parent
        root = root_parent.attachNewNode(f"cyber_btn_{button_key}")
        root.setPos(pos[0], pos[1], pos[2])
        root.setPythonTag("cyber_base_scale", scale_applied)
        root.setScale(scale_applied)

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

        solid_press = gui_rgba4((neon[0], neon[1], neon[2], 0.96))

        frame_colors: Tuple[Tuple[float, float, float, float], ...] = (
            gui_rgba4(_BASE_FRAME_RGBA),
            solid_press,
            gui_rgba4(_ROLL_FRAME_RGBA),
            gui_rgba4((0.12, 0.12, 0.12, 0.45)),
        )

        text_ready = gui_rgba4(neon)
        text_pressed = gui_rgba4(neon_bright)
        text_rollover = gui_rgba4((1.0, 1.0, 1.0, 1.0))
        text_disabled = gui_rgba4((0.35, 0.35, 0.35, 0.65))

        btn = DirectButton(
            text=display_text,
            text_align=TextNode.ACenter,
            text_scale=text_scale,
            text_font=font,
            text0_fg=text_ready,
            text1_fg=text_pressed,
            text2_fg=text_rollover,
            text3_fg=text_disabled,
            frameSize=(-hw, hw, -hh, hh),
            frameColor=frame_colors,
            relief=DGG.RIDGE,
            borderWidth=(border_xy, border_xy),
            pad=pad_xy,
            pressEffect=False,
            command=command if enabled else None,
            parent=root,
        )
        btn.setBin("gui-popup", 0)
        btn.setTransparency(TransparencyAttrib.MAlpha)

        if not enabled:
            btn["state"] = DGG.DISABLED

        btn.bind(DGG.ENTER, lambda _e, p=root: self._cyber_hover_enter(p))
        btn.bind(DGG.EXIT, lambda _e, p=root: self._cyber_hover_exit(p))

        self._cyber_rows.append((root, outer_glow, inner_glow, btn))
        btn.show()
        return btn

    def create_glitch_offline_button(
        self,
        button_key: str,
        primary_text: str,
        pos: Tuple[float, float, float],
        *,
        accent: str = "cyan",
        parent: Optional[NodePath] = None,
    ) -> DirectButton:
        """Visually unstable disabled control showing OFFLINE status."""
        btn = self.create_cyber_button(
            button_key,
            primary_text,
            None,
            pos,
            accent=accent,
            enabled=False,
            parent=parent,
        )
        _root, _o, _i, inner_btn = self._cyber_rows[-1]

        status = OnscreenText(
            text="STATUS: OFFLINE // NO UPLINK",
            pos=(0.0, -0.95),
            scale=0.048 * max(0.9, min(1.1, self._layout_scale_ratio())),
            fg=(1.0, 0.2, 0.35, 0.85),
            align=TextNode.ACenter,
            parent=inner_btn,
            mayChange=True,
        )
        status.setBin("gui-popup", 1)
        self._extra_widgets.append(status)

        task_name = f"glitch_net_{button_key}_{id(self)}"

        glitch_root = inner_btn.getParent()
        bp = glitch_root.getPos()
        glitch_root.setPythonTag(
            "glitch_base_pos",
            (float(bp[0]), float(bp[1]), float(bp[2])),
        )

        def glitch(task: Task) -> int:
            t = task.time
            flick = 0.003 * (1.0 if int(t * 13) % 2 == 0 else -1.0)
            base_xyz = glitch_root.getPythonTag("glitch_base_pos")
            if base_xyz is not None:
                bx, by, bz = base_xyz
                glitch_root.setPos(bx + flick, by, bz)
            phase = int(t * 8) % 3
            if phase == 0:
                inner_btn.setColorScale(1.0, 0.85, 0.9, 1.0)
            elif phase == 1:
                inner_btn.setColorScale(0.75, 1.0, 1.0, 1.0)
            else:
                inner_btn.setColorScale(0.9, 0.9, 1.0, 1.0)
            return task.cont

        self.game_base.taskMgr.add(glitch, task_name)
        self._glitch_tasks.append(task_name)

        inner_btn.unbind(DGG.ENTER)
        inner_btn.unbind(DGG.EXIT)

        return btn

    def add_back_button(self, row_index: Optional[int] = None) -> DirectButton:
        idx = _BACK_BUTTON_ROW_INDEX if row_index is None else row_index
        z = self.list_row_z(idx)
        return self.create_cyber_button(
            "back",
            self.labels.get("ui_back", "Back"),
            lambda: self.ui_manager.pop_menu(),
            (0.0, 0.0, z),
            accent="magenta",
        )

    def add_section_title(self, title: str, pos_z: Optional[float] = None) -> None:
        font = self._resolve_cyber_font()
        z_val = self.section_title_z() if pos_z is None else pos_z
        lr = self._layout_scale_ratio()
        title_frame = DirectFrame(
            frameColor=(0, 0, 0, 0),
            text=title.upper(),
            text_align=TextNode.ALeft,
            text_scale=0.09 * max(0.88, min(1.12, lr)),
            text_fg=(0.4, 1.0, 1.0, 1.0),
            text_font=font,
            parent=self.list_parent,
            pos=(0.0, 0.0, z_val),
        )
        title_frame.setBin("gui-popup", 2)
        self._extra_widgets.append(title_frame)
