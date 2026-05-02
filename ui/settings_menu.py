"""System calibration — audio, video, controls stubs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, Optional

from ui.base_menu import BaseMenu

if TYPE_CHECKING:
    from typing import Any

    from ui.player_profile import PlayerProfile
    from ui.ui_manager import UIManager


class SystemCalibrationMenu(BaseMenu):
    menu_key = "system_calibration"

    def __init__(
        self,
        game_base: Any,
        profile: PlayerProfile,
        ui_manager: UIManager,
        labels: Dict[str, str],
        *,
        on_audio: Optional[Callable[[], None]] = None,
        on_video: Optional[Callable[[], None]] = None,
        on_controls: Optional[Callable[[], None]] = None,
    ) -> None:
        self._on_audio = on_audio
        self._on_video = on_video
        self._on_controls = on_controls
        super().__init__(game_base, profile, ui_manager, labels)

    def show(self) -> None:
        self.add_section_title("SYSTEM CALIBRATION")

        def _audio() -> None:
            if self._on_audio:
                self._on_audio()

        def _video() -> None:
            if self._on_video:
                self._on_video()

        def _controls() -> None:
            if self._on_controls:
                self._on_controls()

        rows = (
            ("cal_audio", "AUDIO CORE", _audio),
            ("cal_video", "VIDEO MATRIX", _video),
            ("cal_controls", "CONTROL SCHEMA", _controls),
        )
        for i, (key, label, cmd) in enumerate(rows):
            self.create_cyber_button(key, label, cmd, (0.0, 0.0, self.list_row_z(i)), accent="cyan")

        self.add_back_button(row_index=6)
