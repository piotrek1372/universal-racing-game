"""Docking station hierarchy — maintenance, tuning, visuals, fleet."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from direct.gui.DirectFrame import DirectFrame
from panda3d.core import TextNode

from ui.base_menu import BaseMenu

if TYPE_CHECKING:
    from typing import Any

    from ui.player_profile import PlayerProfile
    from ui.ui_manager import UIManager


class DockingStationMenu(BaseMenu):
    menu_key = "docking_station"

    def __init__(
        self,
        game_base: Any,
        profile: PlayerProfile,
        ui_manager: UIManager,
        labels: Dict[str, str],
    ) -> None:
        super().__init__(game_base, profile, ui_manager, labels)

    def show(self) -> None:
        self.add_section_title("DOCKING STATION")
        actions = (
            ("garage_maint", "MAINTENANCE", lambda: self.ui_manager.push_menu("maintenance")),
            ("garage_perf", "PERFORMANCE MODS", lambda: self.ui_manager.push_menu("performance_mods")),
            ("garage_visual", "VISUAL OVERRIDE", lambda: self.ui_manager.push_menu("visual_override")),
            ("garage_storage", "VEHICLE STORAGE", lambda: self.ui_manager.push_menu("vehicle_storage")),
        )
        for i, (key, label, cmd) in enumerate(actions):
            self.create_cyber_button(
                key,
                label,
                cmd,
                (0.0, 0.0, self.list_row_z(i)),
                accent="cyan",
            )
        self.add_back_button(row_index=6)


class MaintenanceMenu(BaseMenu):
    menu_key = "maintenance"

    def __init__(
        self,
        game_base: Any,
        profile: PlayerProfile,
        ui_manager: UIManager,
        labels: Dict[str, str],
    ) -> None:
        super().__init__(game_base, profile, ui_manager, labels)

    def show(self) -> None:
        self.add_section_title("MAINTENANCE // REPAIR BAY")
        font = self._resolve_cyber_font()
        lr = self._layout_scale_ratio()
        p = self.profile
        cost = p.repair_cost_to_full()
        can_pay = p.can_afford_repair_full() and cost > 0

        info_lines = (
            f"CAR CONDITION .......... {p.car_condition:.1f} %",
            f"FULL RESTORE COST ...... {cost:,.0f} CR",
            f"AVAILABLE CREDITS ....... {p.money:,.0f} CR",
        )
        z = self.list_row_z(0)
        for line in info_lines:
            row = DirectFrame(
                frameColor=(0, 0, 0, 0),
                text=line,
                text_align=TextNode.ALeft,
                text_scale=0.048 * max(0.88, min(1.12, lr)),
                text_fg=(0.7, 1.0, 0.92, 1.0),
                text_font=font,
                parent=self.list_parent,
                pos=(0.0, 0.0, z),
            )
            row.setBin("gui-popup", 2)
            self._extra_widgets.append(row)
            z -= 0.1 * max(0.92, min(1.08, lr))

        def do_repair() -> None:
            if p.apply_full_repair():
                self.ui_manager.pop_menu()
                self.ui_manager.push_menu("maintenance")

        label = "FULL SYSTEM RESTORE" if cost > 0 else "CONDITION OPTIMAL"
        self.create_cyber_button(
            "repair_full",
            label,
            do_repair if can_pay else lambda: None,
            (0.0, 0.0, self.list_row_z(4)),
            accent="magenta",
            enabled=bool(can_pay),
        )

        self.add_back_button(row_index=6)


class PerformanceModsMenu(BaseMenu):
    menu_key = "performance_mods"

    def __init__(
        self,
        game_base: Any,
        profile: PlayerProfile,
        ui_manager: UIManager,
        labels: Dict[str, str],
    ) -> None:
        super().__init__(game_base, profile, ui_manager, labels)

    def show(self) -> None:
        self.add_section_title("PERFORMANCE MODS")
        m = self.profile.mechanical

        def bump_engine() -> None:
            m.engine_level = min(10, m.engine_level + 1)
            self.ui_manager.pop_menu()
            self.ui_manager.push_menu("performance_mods")

        def bump_tires() -> None:
            m.tire_level = min(10, m.tire_level + 1)
            self.ui_manager.pop_menu()
            self.ui_manager.push_menu("performance_mods")

        def bump_susp() -> None:
            m.suspension_level = min(10, m.suspension_level + 1)
            self.ui_manager.pop_menu()
            self.ui_manager.push_menu("performance_mods")

        rows = (
            ("mod_engine", f"ENGINE CALIBRATION  LV {m.engine_level}", bump_engine),
            ("mod_tires", f"TIRE GRIP MATRIX   LV {m.tire_level}", bump_tires),
            ("mod_susp", f"SUSPENSION GEO      LV {m.suspension_level}", bump_susp),
        )
        for i, (key, label, cmd) in enumerate(rows):
            self.create_cyber_button(key, label, cmd, (0.0, 0.0, self.list_row_z(i)), accent="cyan")

        font = self._resolve_cyber_font()
        lr = self._layout_scale_ratio()
        hint = DirectFrame(
            frameColor=(0, 0, 0, 0),
            text=(
                "PLACEHOLDER: LEVELS STACK INTO tuning_performance_bonus() "
                "FOR FUTURE PHYSICS HOOKUP."
            ),
            text_align=TextNode.ALeft,
            text_scale=0.038 * max(0.88, min(1.12, lr)),
            text_fg=(0.5, 0.65, 0.7, 0.95),
            text_font=font,
            parent=self.list_parent,
            pos=(0.0, 0.0, self.list_row_z(4)),
        )
        hint.setBin("gui-popup", 2)
        self._extra_widgets.append(hint)

        self.add_back_button(row_index=6)


class VisualOverrideMenu(BaseMenu):
    menu_key = "visual_override"

    def __init__(
        self,
        game_base: Any,
        profile: PlayerProfile,
        ui_manager: UIManager,
        labels: Dict[str, str],
    ) -> None:
        super().__init__(game_base, profile, ui_manager, labels)

    def show(self) -> None:
        self.add_section_title("VISUAL OVERRIDE")
        v = self.profile.visual

        def cycle_neon() -> None:
            opts = ("cyan_arc", "magenta_pulse", "amber_grid")
            idx = opts.index(v.neon_style) if v.neon_style in opts else 0
            v.neon_style = opts[(idx + 1) % len(opts)]
            self._reload_self()

        def cycle_paint() -> None:
            opts = ("midnight_blue", "oxide_red", "ghost_white")
            idx = opts.index(v.paint_id) if v.paint_id in opts else 0
            v.paint_id = opts[(idx + 1) % len(opts)]
            self._reload_self()

        def cycle_body() -> None:
            opts = ("stock", "wide_aero", "drift_kit")
            idx = opts.index(v.body_kit_id) if v.body_kit_id in opts else 0
            v.body_kit_id = opts[(idx + 1) % len(opts)]
            self._reload_self()

        rows = (
            ("vis_neon", f"NEON ROUTING :: {v.neon_style.upper()}", cycle_neon),
            ("vis_paint", f"PAINT LAYER :: {v.paint_id.upper()}", cycle_paint),
            ("vis_body", f"BODY SHELL :: {v.body_kit_id.upper()}", cycle_body),
        )
        for i, (key, label, cmd) in enumerate(rows):
            self.create_cyber_button(key, label, cmd, (0.0, 0.0, self.list_row_z(i)), accent="magenta")

        self.add_back_button(row_index=6)

    def _reload_self(self) -> None:
        self.ui_manager.pop_menu()
        self.ui_manager.push_menu("visual_override")


class VehicleStorageMenu(BaseMenu):
    menu_key = "vehicle_storage"

    def __init__(
        self,
        game_base: Any,
        profile: PlayerProfile,
        ui_manager: UIManager,
        labels: Dict[str, str],
    ) -> None:
        super().__init__(game_base, profile, ui_manager, labels)

    def show(self) -> None:
        self.add_section_title("VEHICLE STORAGE")
        font = self._resolve_cyber_font()
        lr = self._layout_scale_ratio()
        for idx, vid in enumerate(self.profile.fleet_vehicle_ids):
            active = vid == self.profile.active_vehicle_id
            prefix = "ACTIVE // " if active else "STANDBY // "

            def select(v: str = vid) -> None:
                self.profile.active_vehicle_id = v
                self.ui_manager.pop_menu()
                self.ui_manager.push_menu("vehicle_storage")

            self.create_cyber_button(
                f"fleet_{idx}",
                prefix + vid.upper(),
                select,
                (0.0, 0.0, self.list_row_z(idx)),
                accent="cyan",
                enabled=not active,
            )

        note = DirectFrame(
            frameColor=(0, 0, 0, 0),
            text="PLACEHOLDER FLEET — EXTEND WITH GARAGE DATA LAYER.",
            text_align=TextNode.ALeft,
            text_scale=0.038 * max(0.88, min(1.12, lr)),
            text_fg=(0.55, 0.72, 0.78, 0.9),
            text_font=font,
            parent=self.list_parent,
            pos=(
                0.0,
                0.0,
                self.list_row_z(max(len(self.profile.fleet_vehicle_ids), 3) + 1),
            ),
        )
        note.setBin("gui-popup", 2)
        self._extra_widgets.append(note)

        self.add_back_button(row_index=6)
