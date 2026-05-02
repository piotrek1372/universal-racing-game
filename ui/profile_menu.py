"""Operator profile — reputation, wallet, story progression."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from direct.gui.DirectFrame import DirectFrame
from panda3d.core import TextNode

from ui.base_menu import BaseMenu

if TYPE_CHECKING:
    from typing import Any

    from ui.player_profile import PlayerProfile
    from ui.ui_manager import UIManager


class OperatorProfileMenu(BaseMenu):
    menu_key = "operator_profile"

    def __init__(
        self,
        game_base: Any,
        profile: PlayerProfile,
        ui_manager: UIManager,
        labels: Dict[str, str],
    ) -> None:
        super().__init__(game_base, profile, ui_manager, labels)

    def show(self) -> None:
        self.add_section_title("OPERATOR PROFILE")
        font = self._resolve_cyber_font()
        p = self.profile

        lines = (
            f"STREET CRED ............ {p.reputation}",
            f"WALLET ................. {p.money:,.0f} CR",
            f"STORY LOG .............. CH.{p.story_chapter} — {p.story_mission.upper()}",
            f"VEHICLE ................ {p.active_vehicle_id.upper()}",
            f"PERF (COND×TUNE) ....... "
            f"{p.condition_performance_factor():.3f} × "
            f"{1.0 + p.tuning_performance_bonus():.3f} (PLACEHOLDER)",
        )
        lr = self._layout_scale_ratio()
        z = self.list_row_z(0)
        step = 0.11 * max(0.92, min(1.08, lr))
        for line in lines:
            row = DirectFrame(
                frameColor=(0, 0, 0, 0),
                text=line,
                text_align=TextNode.ALeft,
                text_scale=0.05 * max(0.88, min(1.12, lr)),
                text_fg=(0.65, 1.0, 0.95, 1.0),
                text_font=font,
                parent=self.list_parent,
                pos=(0.0, 0.0, z),
            )
            row.setBin("gui-popup", 2)
            self._extra_widgets.append(row)
            z -= step

        self.add_back_button(row_index=6)
