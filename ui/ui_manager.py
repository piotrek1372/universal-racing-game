"""Central menu stack: push, pop, and hard switch routes."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from direct.showbase.DirectObject import DirectObject

from ui.base_menu import BaseMenu
from ui.garage import (
    DockingStationMenu,
    MaintenanceMenu,
    PerformanceModsMenu,
    VehicleStorageMenu,
    VisualOverrideMenu,
)
from ui.neural_menu import NeuralLinkMenu
from ui.placeholders import PlaceholderPanelMenu
from ui.profile_menu import OperatorProfileMenu
from ui.settings_menu import SystemCalibrationMenu

if TYPE_CHECKING:
    from ui.player_profile import PlayerProfile

LOGGER: logging.Logger = logging.getLogger(__name__)


class UIManager(DirectObject):
    """Owns menu stack, factories, Esc-to-pop, and exit routing."""

    def __init__(
        self,
        game_base: Any,
        profile: PlayerProfile,
        labels: Dict[str, str],
        *,
        on_settings: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self.game_base = game_base
        self.profile = profile
        self.labels = labels
        self.on_settings = on_settings
        self.on_exit = on_exit

        self._stack: List[str] = []
        self._current: Optional[BaseMenu] = None
        self._registry: Dict[str, Callable[..., BaseMenu]] = {}
        self._register_builtin()

        self.accept("escape", self._on_escape)

    def is_stack_empty(self) -> bool:
        return len(self._stack) == 0

    def teardown_active_menu(self) -> None:
        """Remove the current menu from the scene; stack keys are left unchanged for rebuild."""
        if self._current is not None:
            self._current.destroy()
            self._current = None

    def reanchor_active_menu(self) -> None:
        if self._current is not None:
            self._current.reanchor_to_aspect_markers()

    def refresh_active_menu(self) -> None:
        """Re-instantiate the top-of-stack menu (same key) after resolution / aspect changes."""
        if not self._stack:
            return
        name = self._stack[-1]
        if self._current is not None:
            self._current.destroy()
            self._current = None
        factory = self._registry[name]
        menu = factory(self.game_base, self.profile, self, self.labels)
        self._current = menu
        menu.show()
        menu.reanchor_to_aspect_markers()

    def _register_builtin(self) -> None:
        reg = self._registry

        reg["neural_link"] = lambda gb, p, um, l: NeuralLinkMenu(gb, p, um, l)

        reg["city_grid"] = lambda gb, p, um, l: PlaceholderPanelMenu(
            gb,
            p,
            um,
            l,
            panel_title="CITY GRID",
            subtitle="TOPOLOGY MAP // PLACEHOLDER — ROUTING TO OPEN WORLD",
        )
        reg["fixer_contracts"] = lambda gb, p, um, l: PlaceholderPanelMenu(
            gb,
            p,
            um,
            l,
            panel_title="FIXER CONTRACTS",
            subtitle="MISSION GRAPH // PLACEHOLDER NODE LIST",
        )
        reg["active_events"] = lambda gb, p, um, l: PlaceholderPanelMenu(
            gb,
            p,
            um,
            l,
            panel_title="ACTIVE EVENTS",
            subtitle="RACE QUEUE // QUICK ACCESS PLACEHOLDER",
        )

        reg["docking_station"] = lambda gb, p, um, l: DockingStationMenu(gb, p, um, l)
        reg["maintenance"] = lambda gb, p, um, l: MaintenanceMenu(gb, p, um, l)
        reg["performance_mods"] = lambda gb, p, um, l: PerformanceModsMenu(gb, p, um, l)
        reg["visual_override"] = lambda gb, p, um, l: VisualOverrideMenu(gb, p, um, l)
        reg["vehicle_storage"] = lambda gb, p, um, l: VehicleStorageMenu(gb, p, um, l)

        reg["operator_profile"] = lambda gb, p, um, l: OperatorProfileMenu(gb, p, um, l)

        um_self = self

        reg["system_calibration"] = lambda gb, p, um, l: SystemCalibrationMenu(
            gb,
            p,
            um,
            l,
            on_audio=um_self.on_settings,
            on_video=lambda: LOGGER.info("Video matrix calibration (placeholder)."),
            on_controls=lambda: LOGGER.info("Control schema calibration (placeholder)."),
        )

    def push_menu(self, menu_name: str) -> None:
        if menu_name not in self._registry:
            LOGGER.error("Unknown menu key: %s", menu_name)
            return
        self._stack.append(menu_name)
        self._activate_top()

    def pop_menu(self) -> None:
        if len(self._stack) <= 1:
            return
        self._stack.pop()
        self._activate_top()

    def switch_to(self, menu_name: str) -> None:
        if menu_name not in self._registry:
            LOGGER.error("Unknown menu key: %s", menu_name)
            return
        self._stack = [menu_name]
        self._activate_top()

    def request_disconnect(self) -> None:
        if self.on_exit is not None:
            self.on_exit()

    def shutdown(self) -> None:
        self.ignoreAll()
        if self._current is not None:
            self._current.destroy()
            self._current = None
        self._stack.clear()

    def _activate_top(self) -> None:
        name = self._stack[-1]
        if self._current is not None:
            self._current.destroy()
            self._current = None
        factory = self._registry[name]
        menu = factory(self.game_base, self.profile, self, self.labels)
        self._current = menu
        menu.show()
        menu.reanchor_to_aspect_markers()

    def _on_escape(self) -> None:
        if len(self._stack) > 1:
            self.pop_menu()
