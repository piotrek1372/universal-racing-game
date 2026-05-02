"""High-level UI navigation states for the modular menu system."""

from __future__ import annotations

from enum import Enum, auto


class UIState(Enum):
    MAIN_MENU = auto()
    GARAGE = auto()
    MAP = auto()
    MISSION_SELECT = auto()
