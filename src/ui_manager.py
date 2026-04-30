"""
UI Manager for Universal Racing Game

This module provides UI components and management for the game's interface.
It handles menus, HUD elements, and user interaction through Panda3D's
DirectGUI system.

Author: URG Development Team
Version: 1.0.0
"""

from panda3d.core import (
    TextNode,
    NodePath,
    LVector4,
    TransparencyAttrib,
    CardMaker,
    LVector3,
    Vec4,
    Vec3,
    VBase4
)
from direct.gui.DirectGui import (
    DirectFrame,
    DirectButton,
    DirectLabel,
    DGG
)
from direct.interval.IntervalGlobal import (
    Sequence,
    Parallel,
    LerpColorScaleInterval,
    Func,
    Wait
)
from pathlib import Path
import sys
import os

from .i18n import get_localization_manager


class MainMenu:
    """
    Main menu UI for the Universal Racing Game.

    Displays the game title and a vertical list of buttons for navigation.
    All text is loaded from localization files and supports Unicode characters
    including Polish diacritics (ą, ę, ś, ć, ż, ź, ó, ł, ń).

    Attributes:
        base: Reference to the main application (ShowBase instance)
        frame: Main container frame for the menu
        title_label: Game title label
        buttons: Dictionary of menu buttons
    """

    def __init__(self, base) -> None:
        """
        Initialize the main menu.

        Args:
            base: The ShowBase instance (main application)
        """
        self.base = base
        self.frame: DirectFrame = None
        self.title_label: DirectLabel = None
        self.buttons: dict = {}

        # Get localization manager
        self.i18n = get_localization_manager()

        # Build the UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the complete main menu UI."""
        self._create_background()
        self._create_title()
        self._create_buttons()

    def _create_background(self) -> None:
        """Create a semi-transparent background frame for the menu."""
        self.frame = DirectFrame(
            frameSize=(-1.5, 1.5, -1.0, 1.0),
            frameColor=(0.0, 0.0, 0.0, 0.7),
            parent=self.base.render2d,
        )
        self.frame.setTransparency(TransparencyAttrib.MAlpha)

    def _create_title(self) -> None:
        """Create the game title label at the top center of the screen."""
        self.title_label = DirectLabel(
            text=self.i18n.get("menu_title"),
            text_fg=LVector4(1.0, 0.8, 0.2, 1.0),
            text_font=self._get_font(),
            text_scale=0.12,
            text_align=TextNode.ACenter,
            frameColor=(0.0, 0.0, 0.0, 0.0),
            pos=(0.0, 0.0, 0.8),
            parent=self.frame,
        )

    def _create_buttons(self) -> None:
        """Create the vertical list of menu buttons."""
        button_configs = [
            ("start", self.i18n.get("btn_start"), self._on_start),
            ("free_roam", self.i18n.get("btn_free_roam"), self._on_free_roam),
            ("settings", self.i18n.get("btn_settings"), self._on_settings),
            ("exit", self.i18n.get("btn_exit"), self._on_exit),
        ]

        button_height = 0.15
        button_spacing = 0.12
        total_height = len(button_configs) * button_height + (
            len(button_configs) - 1
        ) * button_spacing
        start_y = total_height / 2 - button_height / 2

        for i, (key, text, command) in enumerate(button_configs):
            y_pos = start_y - i * (button_height + button_spacing)

            btn = DirectButton(
                text=text,
                text_fg=LVector4(1.0, 1.0, 1.0, 1.0),
                text_font=self._get_font(),
                text_scale=0.07,
                frameSize=(-1.2, 1.2, -0.8, 0.8),
                frameColor=[
                    (0.2, 0.2, 0.4, 1.0),
                    (0.3, 0.3, 0.5, 1.0),
                    (0.4, 0.4, 0.6, 1.0),
                    (0.15, 0.15, 0.3, 1.0),
                ],
                pos=(0.0, 0.0, y_pos),
                command=command,
                parent=self.frame,
                relief=DGG.FLAT,
            )
            self.buttons[key] = btn

    def _get_font(self):
        """
        Get a font that supports Polish Unicode characters.

        Panda3D's default font supports basic ASCII but for full Unicode
        support including Polish diacritics (ą, ę, ś, ć, ż, ź, ó, ł, ń),
        place a .ttf font file in assets/fonts/ and load it here.

        Example:
            from panda3d.core import TextFont
            return loader.loadFont("assets/fonts/DejaVuSans.ttf")

        Returns:
            The default Panda3D font (supports basic ASCII).
        """
        # Using Panda3D's default font.
        # For full Polish character support, uncomment the code above and
        # place a Unicode-compatible .ttf font file in assets/fonts/.
        return None

    # --- Button callback methods ---

    def _on_start(self) -> None:
        """Handle Start button click."""
        print("Start kliknięty")

    def _on_free_roam(self) -> None:
        """Handle Free Roam button click."""
        print("Swobodna Jazda kliknięta")

    def _on_settings(self) -> None:
        """Handle Settings button click."""
        print("Ustawienia kliknięte")

    def _on_exit(self) -> None:
        """Handle Exit button click."""
        print("Wyjście kliknięte")
        self.base.userExit()

    def destroy(self) -> None:
        """Clean up and remove all UI elements."""
        if self.frame:
            self.frame.destroy()
            self.frame = None
        self.buttons.clear()

    def show(self) -> None:
        """Show the main menu."""
        if self.frame:
            self.frame.show()

    def hide(self) -> None:
        """Hide the main menu."""
        if self.frame:
            self.frame.hide()


class SplashManager:
    """
    Splash screen manager for Universal Racing Game.

    Displays a sequence of splash images with smooth fade transitions
    and a gradually increasing ambient audio track. Supports skipping
    the splash sequence with Space or Escape keys.

    Attributes:
        base: Reference to the ShowBase application instance
        splash_images: List of splash image file paths
        audio_file: Path to the ambient audio file
        sound: Loaded music object for ambient audio
        splash_card: NodePath for displaying splash images
        sequence: Interval sequence for the splash animation
        is_active: Whether the splash screen is currently showing
        on_complete: Callback function when splash completes
    """

    def __init__(self, base, on_complete=None) -> None:
        """
        Initialize the splash screen manager.

        Args:
            base: The ShowBase instance (main application)
            on_complete: Optional callback when splash sequence finishes
        """
        self.base = base
        self.on_complete = on_complete
        self.splash_images = []
        self.audio_file = None
        self.sound = None
        self.splash_card = None
        self.sequence = None
        self.is_active = False

        # Define splash image paths (relative to src/)
        self._setup_paths()

        # Build the splash UI
        self._setup_ui()

    def _setup_paths(self) -> None:
        """Set up file paths for splash images and audio."""
        # Path from src/ to assets/
        assets_dir = Path("../assets")
        images_dir = assets_dir / "images"
        audio_dir = assets_dir / "audio"

        # Check for splash images
        splash_files = [
            images_dir / "splash1.png",
            images_dir / "splash2.png",
            images_dir / "splash3.png",
        ]

        for splash_file in splash_files:
            if splash_file.exists():
                self.splash_images.append(str(splash_file))
            else:
                print(f"Warning: Splash image not found: {splash_file}")

        # Check for audio file
        audio_files = [
            audio_dir / "splash_ambient.mp3",
            audio_dir / "splash_ambient.wav",
        ]

        for audio_file in audio_files:
            if audio_file.exists():
                self.audio_file = str(audio_file)
                break

        if not self.audio_file:
            print("Warning: No splash audio file found (expected splash_ambient.mp3 or .wav)")

    def _setup_ui(self) -> None:
        """Create the splash screen UI elements."""
        # Create a fullscreen card for displaying splash images
        cm = CardMaker("splashCard")
        cm.setFrame(-1, 1, -1, 1)
        self.splash_card = self.base.render2d.attachNewNode(cm.generate())
        self.splash_card.setTransparency(TransparencyAttrib.MAlpha)
        self.splash_card.setColorScale(0, 0, 0, 0)  # Start fully transparent
        self.splash_card.hide()

        # Load texture for the first image (will be swapped during sequence)
        if self.splash_images:
            from panda3d.core import Texture
            self.textures = []
            for img_path in self.splash_images:
                tex = loader.loadTexture(img_path)
                if tex:
                    self.textures.append(tex)
                else:
                    print(f"Warning: Could not load texture: {img_path}")
        else:
            self.textures = []

    def _load_audio(self) -> None:
        """Load the ambient audio file."""
        if self.audio_file and not self.sound:
            try:
                self.sound = self.base.loader.loadMusic(self.audio_file)
                if self.sound:
                    self.sound.setVolume(0.0)  # Start muted
                    self.sound.setLoop(True)  # Loop during splash
                    print(f"Loaded splash audio: {self.audio_file}")
            except Exception as e:
                print(f"Warning: Could not load audio file {self.audio_file}: {e}")

    def _create_sequence(self) -> Sequence:
        """
        Create the interval sequence for the splash animation.

        Returns:
            Sequence: The complete splash animation sequence
        """
        if not self.textures:
            # No images, just wait and call complete
            return Sequence(
                Wait(1.0),
                Func(self._on_splash_complete)
            )

        intervals = []
        num_images = len(self.textures)

        for i, texture in enumerate(self.textures):
            # Fade in (1 second)
            fade_in = LerpColorScaleInterval(
                self.splash_card,
                duration=1.0,
                colorScale=Vec4(1, 1, 1, 1),
                startColorScale=Vec4(1, 1, 1, 0)
            )

            # Hold (1.5 seconds)
            hold = Wait(1.5)

            # Fade out (1 second) - except for last image
            if i < num_images - 1:
                fade_out = LerpColorScaleInterval(
                    self.splash_card,
                    duration=1.0,
                    colorScale=Vec4(1, 1, 1, 0),
                    startColorScale=Vec4(1, 1, 1, 1)
                )
            else:
                # Last image: fade out completely
                fade_out = LerpColorScaleInterval(
                    self.splash_card,
                    duration=1.0,
                    colorScale=Vec4(1, 1, 1, 0),
                    startColorScale=Vec4(1, 1, 1, 1)
                )

            # Function to set texture
            def set_tex(tex=texture):
                self.splash_card.setTexture(tex, 1)

            # Add to sequence
            intervals.append(Func(self.splash_card.show))
            intervals.append(Func(set_tex))
            intervals.append(fade_in)
            intervals.append(hold)
            intervals.append(fade_out)

        # Final callback
        intervals.append(Func(self._on_splash_complete))

        return Sequence(*intervals)

    def start(self) -> None:
        """Start the splash screen sequence."""
        if self.is_active:
            return

        self.is_active = True

        # Load audio
        self._load_audio()

        # Start ambient audio (starts muted, can be controlled externally)
        if self.sound:
            self.sound.play()
            # Create volume fade-in interval: 0.0 to 1.0 over 7.5 seconds
            from direct.interval.IntervalGlobal import LerpFunctionInterval
            
            def set_volume(volume):
                if self.sound:
                    self.sound.setVolume(volume)
            
            self.volume_interval = LerpFunctionInterval(
                set_volume,
                fromData=0.0,
                toData=1.0,
                duration=7.5,  # Total time for all 3 images (3 * 1.5s hold + transitions)
                blendType="easeInOut"
            )
            self.volume_interval.start()

        # Create and start the sequence
        self.sequence = self._create_sequence()
        self.sequence.start()

        # Set up input handlers for skipping
        self.base.accept("space", self._skip)
        self.base.accept("escape", self._skip)

        print("Splash screen started")

    def _skip(self) -> None:
        """Skip the splash screen immediately."""
        if not self.is_active:
            return

        print("Splash screen skipped")

        # Stop the sequence
        if self.sequence:
            self.sequence.finish()

        # Stop and fade out audio
        if self.sound:
            self.sound.stop()
            self.sound = None

        # Stop volume interval if running
        if hasattr(self, 'volume_interval'):
            self.volume_interval.finish()

        # Hide splash card
        if self.splash_card:
            self.splash_card.hide()

        self.is_active = False

        # Call completion callback
        self._on_splash_complete()

    def _on_splash_complete(self) -> None:
        """Handle splash screen completion."""
        if not self.is_active:
            return

        self.is_active = False

        # Clean up audio
        if self.sound:
            self.sound.stop()
            self.sound = None

        # Stop volume interval if running
        if hasattr(self, 'volume_interval'):
            self.volume_interval.finish()

        # Hide splash card
        if self.splash_card:
            self.splash_card.hide()

        # Remove input handlers
        self.base.ignore("space")
        self.base.ignore("escape")

        print("Splash screen completed")

        # Call completion callback
        if self.on_complete:
            self.on_complete()

    def destroy(self) -> None:
        """Clean up splash screen resources."""
        self._skip()  # Ensure everything is stopped

        if self.splash_card:
            self.splash_card.removeNode()
            self.splash_card = None

        self.textures = []
        self.splash_images = []
        self.audio_file = None