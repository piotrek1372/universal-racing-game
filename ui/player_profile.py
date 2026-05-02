"""Persistent player state shared across menu screens and gameplay hooks."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CarMechanicalStats:
    """Tune placeholders; affect performance multiplier when wired into racing."""

    engine_level: int = 1
    tire_level: int = 1
    suspension_level: int = 1


@dataclass
class CarVisualStats:
    """Cosmetic placeholders."""

    neon_style: str = "cyan_arc"
    paint_id: str = "midnight_blue"
    body_kit_id: str = "stock"


@dataclass
class PlayerProfile:
    """Money, reputation, vehicle condition — menus read/write this object."""

    money: float = 12_500.0
    reputation: int = 120
    car_condition: float = 72.0  # 0–100
    story_chapter: int = 1
    story_mission: str = "Neon Circuit — Qualifier"
    active_vehicle_id: str = "runner_mk1"
    fleet_vehicle_ids: tuple[str, ...] = ("runner_mk1",)
    mechanical: CarMechanicalStats = field(default_factory=CarMechanicalStats)
    visual: CarVisualStats = field(default_factory=CarVisualStats)

    # Repair economy (placeholder tuning)
    repair_cost_per_condition_point: float = 45.0

    def repair_cost_to_full(self) -> float:
        """Credits needed to restore condition to 100 from current."""
        gap = max(0.0, 100.0 - float(self.car_condition))
        return gap * self.repair_cost_per_condition_point

    def can_afford_repair_full(self) -> bool:
        return self.money >= self.repair_cost_to_full()

    def apply_full_repair(self) -> bool:
        """Spend money and max condition; returns False if unaffordable."""
        cost = self.repair_cost_to_full()
        if self.money < cost or cost <= 0:
            return False
        self.money -= cost
        self.car_condition = 100.0
        return True

    def condition_performance_factor(self) -> float:
        """Placeholder 0.85–1.0 based on mechanical wear."""
        # Condition scales grip/power placeholders for future physics hook-in.
        return 0.85 + 0.15 * (float(self.car_condition) / 100.0)

    def tuning_performance_bonus(self) -> float:
        """Small stacked bonus from mod levels (placeholder)."""
        m = self.mechanical
        tiers = m.engine_level + m.tire_level + m.suspension_level
        return min(0.12, tiers * 0.01)
