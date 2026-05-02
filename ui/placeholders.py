"""Placeholder leaf screens for systems not yet implemented (map, missions, events)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from direct.gui.DirectFrame import DirectFrame
from panda3d.core import TextNode

from ui.base_menu import BaseMenu

if TYPE_CHECKING:
    from typing import Any

    from ui.player_profile import PlayerProfile
    from ui.ui_manager import UIManager


class PlaceholderPanelMenu(BaseMenu):
    """Simple titled panel with Back."""

    menu_key = "placeholder"

    def __init__(
        self,
        game_base: Any,
        profile: PlayerProfile,
        ui_manager: UIManager,
        labels: Dict[str, str],
        *,
        panel_title: str,
        subtitle: str = "PROTOCOL STUB // AWAITING UPLINK",
    ) -> None:
        self._panel_title = panel_title
        self._subtitle = subtitle
        slug = "".join(c if c.isalnum() else "_" for c in panel_title.lower()).strip("_")
        self.menu_key = f"ph_{slug[:32]}"
        super().__init__(game_base, profile, ui_manager, labels)

    def show(self) -> None:
        self.add_section_title(self._panel_title)
        font = self._resolve_cyber_font()
        lr = self._layout_scale_ratio()
        body = DirectFrame(
            frameColor=(0, 0, 0, 0),
            text=self._subtitle.upper(),
            text_align=TextNode.ALeft,
            text_scale=0.048 * max(0.88, min(1.12, lr)),
            text_fg=(0.55, 0.75, 0.82, 0.9),
            text_font=font,
            parent=self.list_parent,
            pos=(0.0, 0.0, self.list_row_z(0)),
        )
        body.setBin("gui-popup", 2)
        self._extra_widgets.append(body)
        self.add_back_button(row_index=6)
