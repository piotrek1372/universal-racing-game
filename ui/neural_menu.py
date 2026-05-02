"""Neural Link — primary hub navigation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict

from ui.base_menu import BaseMenu

if TYPE_CHECKING:
    from typing import Any

    from ui.player_profile import PlayerProfile
    from ui.ui_manager import UIManager

LOGGER: logging.Logger = logging.getLogger(__name__)


class NeuralLinkMenu(BaseMenu):
    """Main entry: neural uplink routing table."""

    menu_key = "neural_link"

    def __init__(
        self,
        game_base: Any,
        profile: PlayerProfile,
        ui_manager: UIManager,
        labels: Dict[str, str],
    ) -> None:
        super().__init__(game_base, profile, ui_manager, labels)

    def show(self) -> None:
        mouse_watcher = self.game_base.mouseWatcherNode
        is_active: bool = bool(
            mouse_watcher
            and hasattr(mouse_watcher, "isActive")
            and mouse_watcher.isActive()
        )
        if not is_active:
            LOGGER.warning("mouseWatcherNode is not active. Menu input may not work.")

        self.add_section_title("NEURAL LINK // MAIN ENTRY")

        rows = (
            ("hub_city", "CITY GRID", lambda: self.ui_manager.push_menu("city_grid")),
            ("hub_fixer", "FIXER CONTRACTS", lambda: self.ui_manager.push_menu("fixer_contracts")),
            ("hub_events", "ACTIVE EVENTS", lambda: self.ui_manager.push_menu("active_events")),
            ("hub_dock", "DOCKING STATION", lambda: self.ui_manager.push_menu("docking_station")),
            ("hub_profile", "OPERATOR PROFILE", lambda: self.ui_manager.push_menu("operator_profile")),
        )
        for i, (key, label, cmd) in enumerate(rows):
            self.create_cyber_button(
                key,
                label,
                cmd,
                (0.0, 0.0, self.list_row_z(i)),
                accent="cyan",
            )

        self.create_glitch_offline_button(
            "hub_network",
            "NETWORK",
            (0.0, 0.0, self.list_row_z(len(rows))),
            accent="cyan",
        )

        cal_row = len(rows) + 1
        self.create_cyber_button(
            "hub_calibration",
            "SYSTEM CALIBRATION",
            lambda: self.ui_manager.push_menu("system_calibration"),
            (0.0, 0.0, self.list_row_z(cal_row)),
            accent="cyan",
        )

        exit_parent = self.attach_footer_anchor()
        self.create_cyber_button(
            "hub_disconnect",
            "DISCONNECT",
            lambda: self.ui_manager.request_disconnect(),
            (0.0, 0.0, 0.0),
            accent="magenta",
            parent=exit_parent,
        )
