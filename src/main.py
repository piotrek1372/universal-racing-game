"""
Universal Racing Game - Main Application

Panda3D-based racing game with full Unicode support for international
text rendering. Uses Entity-Component-System (ECS) architecture and
automatic language detection for seamless localization.

Author: URG Development Team
Version: 1.0.0
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Check if we need to fix imports for direct script execution
if Path(__file__).name == 'main.py' and not __package__:
    # We're running as a script or imported without proper package context
    # Re-import this module properly using importlib
    import importlib.util
    import types
    
    # Ensure parent directory is in path
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    # Create a proper module with correct __package__
    spec = importlib.util.spec_from_file_location('src.main', __file__)
    proper_module = importlib.util.module_from_spec(spec)
    proper_module.__package__ = 'src'
    
    # Add to sys.modules and execute
    sys.modules['src.main'] = proper_module
    sys.modules[__name__] = proper_module
    spec.loader.exec_module(proper_module)
    
    # Copy all attributes to this module
    for key, value in proper_module.__dict__.items():
        if key not in globals():
            globals()[key] = value
    
    # Prevent further execution of this script
    sys.exit(0)

# Normal package imports
from .i18n import get_localization_manager
from .ecs import (
    Entity,
    TransformComponent,
    TextComponent,
    SystemManager,
    LocaleSystem
)
from .ui_manager import SplashManager
from .core.physics import PhysicsWorld, PhysicsWorldConfig
from .game.vehicle import Vehicle

# Panda3D imports
try:
    from direct.showbase.ShowBase import ShowBase
    from direct.showbase.ShowBaseGlobal import globalClock
    from direct.gui.DirectGui import DirectLabel, DirectButton
    from panda3d.core import LVector3, TextNode, NodePath
    from panda3d.core import loadPrcFileData
    from direct.task import Task
except ImportError as e:
    print(f"Error: Panda3D not properly installed: {e}")
    print("Please install: pip install panda3d")
    sys.exit(1)


class UniversalRacingGame(ShowBase):
    """
    Main application class for Universal Racing Game.
    
    Extends Panda3D's ShowBase to provide the game window, rendering
    pipeline, and main game loop. Integrates ECS architecture with
    Panda3D's scene graph and provides full Unicode text support.
    
    Attributes:
        locale_manager: Internationalization system instance
        ecs_manager: Entity-Component-System manager
        ui_elements: List of UI element NodePaths for cleanup
        splash_manager: Manager for splash screen sequence
    """
    
    def __init__(self) -> None:
        """
        Initialize the Universal Racing Game application.
        
        Sets up Panda3D configuration, loads Unicode fonts, initializes
        the ECS system, and creates the main menu UI with localized text.
        """
        # Configure Panda3D before ShowBase initialization
        self._configure_panda3d()
        
        # Initialize ShowBase (creates window and rendering pipeline)
        super().__init__()
        
        # Set window title
        self.win.setCaption("Universal Racing Game")
        
        # Initialize systems
        self.locale_manager = get_localization_manager()
        # Override locales directory to project root
        self.locale_manager.locales_dir = Path("locales")
        self.ecs_manager = SystemManager()
        self.ui_elements: list[NodePath] = []
        self.splash_manager: Optional[SplashManager] = None
        self.physics_world: Optional[PhysicsWorld] = None
        self.player_vehicle: Optional[Vehicle] = None
        
        # Configure ECS with locale system
        self._setup_ecs()
        self._setup_physics()
        self._setup_input()
        self.taskMgr.add(self.update, "update_task")
        self.taskMgr.add(self._physics_task, "physics_task")
        
        # Show splash screen first
        self._show_splash()

    def _setup_physics(self) -> None:
        """
        Initialize Bullet world with fixed 60 Hz stepping and gravity.
        """

        self.physics_world = PhysicsWorld(
            PhysicsWorldConfig(
                gravity=LVector3(0.0, 0.0, -9.81),
                fixed_time_step=1.0 / 60.0,
                max_substeps=6,
            )
        )
        self.player_vehicle = Vehicle(
            physics_world=self.physics_world,
            parent=self.render,
        )
    
    def _show_splash(self) -> None:
        """
        Display the splash screen sequence.
        
        Creates and starts the splash screen manager. The splash will
        automatically transition to the main menu when complete.
        """
        self.splash_manager = SplashManager(self, on_complete=self._on_splash_complete)
        self.splash_manager.start()
    
    def _on_splash_complete(self) -> None:
        """
        Handle splash screen completion.
        
        Called when the splash sequence finishes (either naturally or
        via user skip). Transitions to the main menu UI.
        """
        # Create main UI after splash completes
        self._create_ui()
        
        # Clean up splash manager
        if self.splash_manager:
            self.splash_manager.destroy()
            self.splash_manager = None
    
    def _configure_panda3d(self) -> None:
        """
        Configure Panda3D settings before initialization.
        
        Sets up rendering parameters, enables Unicode text support,
        and configures window properties. Uses loadPrcFileData to
        set configuration variables programmatically.
        
        Note:
            This method must be called before ShowBase.__init__().
        """
        # Enable Unicode text support (essential for non-ASCII characters)
        loadPrcFileData("", "text-flatten 0")  # Preserve Unicode in text
        loadPrcFileData("", "win-size 1280 720")  # Window size
        loadPrcFileData("", "win-title Universal Racing Game")
        loadPrcFileData("", "framebuffer-multisample 1")  # Anti-aliasing
        loadPrcFileData("", "multisamples 4")
        
        # Configure text rendering for better Unicode support
        loadPrcFileData("", "text-page-size 256")  # Larger texture pages for complex glyphs
        loadPrcFileData("", "text-dynamic 1")  # Dynamic texture generation
    
    def _setup_ecs(self) -> None:
        """
        Set up Entity-Component-System architecture.
        
        Creates the LocaleSystem for automatic text localization and
        registers it with the ECS manager. This system will automatically
        update all TextComponents when the language changes.
        """
        # Create and add locale system
        locale_system: LocaleSystem = LocaleSystem(self.locale_manager)
        self.ecs_manager.add_system(locale_system)
    
    def _setup_input(self) -> None:
        """Set up input handlers for the game."""
        # ESC key to exit the game
        self.accept("escape", self._on_escape)
        # Space key to skip splash (if active)
        self.accept("space", self._on_space)
    
    def _on_space(self) -> None:
        """Handle Space key press - skip splash if active."""
        if self.splash_manager and self.splash_manager.is_active:
            self.splash_manager._skip()
    
    def _on_escape(self) -> None:
        """Handle ESC key press - exit the game."""
        # If splash is active, skip it
        if self.splash_manager and self.splash_manager.is_active:
            self.splash_manager._skip()
            return
        
        print("ESC pressed - exiting game")
        self.cleanup()
        self.userExit()
    
    def _load_unicode_font(self) -> Optional[str]:
        """
        Load a Unicode-compatible font for text rendering.
        
        Attempts to load Noto Sans (supports most Unicode scripts including
        Cyrillic, Arabic, Chinese, Japanese, etc.). Falls back to default
        Panda3D font if Noto Sans is not available.
        
        Returns:
            Optional[str]: Path to loaded font file, or None if using default
        
        Note:
            Noto Sans is recommended because it provides comprehensive
            Unicode coverage across multiple scripts without requiring
            separate font files for each language.
        """
        # Panda3D can load TTF files directly
        # Noto Sans provides excellent Unicode coverage
        font_paths = [
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",  # Linux
            "C:/Windows/Fonts/arial.ttf",  # Windows fallback
            "/System/Library/Fonts/PingFang.ttc",  # macOS Chinese
        ]
        
        from panda3d.core import Filename
        
        for font_path in font_paths:
            font_file = Filename.fromOsSpecific(font_path)
            if font_file.exists():
                try:
                    # Load the font
                    self.loader.loadFont(font_path)
                    print(f"Loaded Unicode font: {font_path}")
                    return font_path
                except Exception as e:
                    print(f"Warning: Could not load font {font_path}: {e}")
        
        # Use default Panda3D font (limited Unicode support)
        print("Using default Panda3D font (limited Unicode support)")
        print("For full Unicode support, install Noto Sans font")
        return None
    
    def _create_ui(self) -> None:
        """
        Create the main menu user interface.
        
        Creates localized UI elements including welcome message, menu
        buttons, and game information displays. All text is automatically
        localized through the ECS system.
        
        Note:
            DirectLabel and DirectButton automatically handle text rendering
            with the configured font. The LocaleSystem ensures text updates
            when language changes.
        """
        # Load Unicode font
        font_path = self._load_unicode_font()
        
        # Create title
        title = DirectLabel(
            text="UNIVERSAL RACING GAME",
            text_fg=(1.0, 1.0, 1.0, 1.0),
            text_font=self.loader.loadFont(font_path) if font_path else None,
            text_scale=0.15,
            frameSize=(-4.0, 4.0, -0.4, 0.4),
            pos=(0, 0, 0.8),
            relief=None,
            text_align=TextNode.ACenter
        )
        title.setTransparency(True)
        self.ui_elements.append(title)
        
        # Create menu buttons with localized text
        self._create_menu_buttons(font_path)
        
        # Create game info display
        self._create_game_info(font_path)
        
        # Create language switcher
        self._create_language_switcher(font_path)
    
    def _create_menu_buttons(self, font_path: Optional[str]) -> None:
        """
        Create menu buttons with localized text.
        
        Args:
            font_path: Path to Unicode font file, or None for default
        """
        button_configs = [
            ("btn_start", 0.2, self._start_game),
            ("btn_free_roam", 0.0, self._free_roam),
            ("btn_settings", -0.2, self._show_settings),
            ("btn_exit", -0.4, self._exit_game)
        ]
        
        self.menu_buttons: list[tuple[DirectLabel, str]] = []
        
        for key, y_pos, command in button_configs:
            # Get localized text
            localized_text = self.locale_manager.get(key)
            
            # Create button entity
            button_entity = Entity(name=f"Button_{key}")
            button_entity.add_component(TextComponent(
                text_key=key,
                text=localized_text,
                font_size=16,
                color=(0.2, 0.6, 1.0, 1.0)
            ))
            self.ecs_manager.add_entity(button_entity)
            
            # Create Panda3D DirectLabel as button
            button = DirectLabel(
                text=localized_text,
                text_fg=(0.2, 0.6, 1.0, 1.0),
                text_font=self.loader.loadFont(font_path) if font_path else None,
                text_scale=0.08,
                frameSize=(-2.0, 2.0, -0.25, 0.25),
                pos=(0, 0, y_pos),
                relief=1,
                frameColor=(0.3, 0.3, 0.3, 0.8),
                text_align=TextNode.ACenter
            )
            button.setTransparency(True)
            
            # Bind click event
            def make_handler(cmd):
                return lambda: cmd()
            
            # Simulate click on mouse1 press
            button.bind(DGG.F1PRESS, lambda event, c=command: c())
            
            self.ui_elements.append(button)
            self.menu_buttons.append((button, key))
    
    def _create_game_info(self, font_path: Optional[str]) -> None:
        """
        Create game information display.
        
        Shows game stats like speed, lap, and position using localized
        labels and ECS-managed text components.
        
        Args:
            font_path: Path to Unicode font file, or None for default
        """
        # Engine status display
        engine_entity = Entity(name="EngineStatus")
        engine_entity.add_component(TextComponent(
            text_key="engine_status",
            text=self.locale_manager.get("engine_status").format(status="OFF"),
            font_size=14,
            color=(0.8, 0.8, 0.8, 1.0)
        ))
        self.ecs_manager.add_entity(engine_entity)
        
        engine_label = DirectLabel(
            text=engine_entity.get_component(TextComponent).text,
            text_fg=(0.8, 0.8, 0.8, 1.0),
            text_font=self.loader.loadFont(font_path) if font_path else None,
            text_scale=0.07,
            frameSize=(-2.0, 2.0, -0.2, 0.2),
            pos=(-1.5, 0, -0.6),
            relief=None,
            text_align=TextNode.ALeft
        )
        engine_label.setTransparency(True)
        self.ui_elements.append(engine_label)
        self.engine_label = engine_label
        self.engine_entity = engine_entity
    
    def _create_language_switcher(self, font_path: Optional[str]) -> None:
        """
        Create language switcher buttons.
        
        Allows users to manually switch between available languages,
        demonstrating the dynamic language switching capability.
        
        Args:
            font_path: Path to Unicode font file, or None for default
        """
        languages = [
            ("Polski", "pl"),
            ("English", "en"),
            ("日本語", "ja"),
            ("العربية", "ar"),
            ("中文", "zh")
        ]
        
        lang_frame = DirectLabel(
            text="",
            frameSize=(-3.0, 3.0, -0.3, 1.5),
            pos=(1.5, 0, -0.2),
            relief=1,
            frameColor=(0.2, 0.2, 0.2, 0.7)
        )
        lang_frame.setTransparency(True)
        self.ui_elements.append(lang_frame)
        
        lang_title = DirectLabel(
            text="Language / Język",
            text_fg=(1.0, 1.0, 1.0, 1.0),
            text_font=self.loader.loadFont(font_path) if font_path else None,
            text_scale=0.06,
            frameSize=(-2.8, 2.8, -0.25, 0.25),
            pos=(0, 0, 0.5),
            relief=None,
            parent=lang_frame,
            text_align=TextNode.ACenter
        )
        lang_title.setTransparency(True)
        
        for i, (label, code) in enumerate(languages):
            def make_lang_handler(lang_code):
                return lambda: self._switch_language(lang_code)
            
            btn = DirectLabel(
                text=label,
                text_fg=(0.9, 0.9, 0.9, 1.0),
                text_font=self.loader.loadFont(font_path) if font_path else None,
                text_scale=0.06,
                frameSize=(-1.2, 1.2, -0.2, 0.2),
                pos=(0, 0, 0.2 - i * 0.25),
                relief=1,
                frameColor=(0.3, 0.3, 0.5, 0.8),
                parent=lang_frame,
                text_align=TextNode.ACenter
            )
            btn.setTransparency(True)
            btn.bind(DGG.F1PRESS, make_lang_handler(code))
            self.ui_elements.append(btn)
    
    def _switch_language(self, language_code: str) -> None:
        """
        Switch application language.
        
        Args:
            language_code: Target language code (e.g., 'en', 'ja', 'ar', 'zh', 'pl')
        
        Note:
            Updates the locale manager and forces the LocaleSystem to
            refresh all text components immediately.
        """
        if self.locale_manager.set_language(language_code):
            # Force update all text through ECS
            locale_system: Optional[LocaleSystem] = self.ecs_manager.get_system(LocaleSystem)
            if locale_system:
                locale_system.force_update()
            
            # Update Panda3D labels
            self._update_ui_text()
            
            print(f"Language switched to: {language_code}")
    
    def _update_ui_text(self) -> None:
        """
        Update all Panda3D UI labels with current language text.
        
        Synchronizes Panda3D DirectLabel text with ECS TextComponent
        values after language changes.
        """
        # Update menu buttons
        if hasattr(self, 'menu_buttons'):
            for button, key in self.menu_buttons:
                localized = self.locale_manager.get(key)
                button["text"] = localized
        
        # Update engine status
        if hasattr(self, 'engine_entity'):
            text_comp = self.engine_entity.get_component(TextComponent)
            if text_comp:
                self.engine_label["text"] = text_comp.text
    
    def _start_game(self) -> None:
        """Handle start game button click."""
        print("Start (Online/Offline) kliknięty")
    
    def _free_roam(self) -> None:
        """Handle free roam button click."""
        print("Swobodna Jazda kliknięta")
    
    def _show_settings(self) -> None:
        """Handle settings button click."""
        print("Ustawienia kliknięte")
    
    def _exit_game(self) -> None:
        """Handle exit game button click."""
        print("Wyjście kliknięte")
        self.cleanup()
        self.userExit()
    
    def update(self, task) -> int:
        """
        Main update loop.
        
        Called every frame by Panda3D's task manager. Updates the ECS
        systems and handles game logic.
        
        Args:
            task: Panda3D task object
        
        Returns:
            int: task.cont to continue the task
        """
        # Calculate delta time
        dt = globalClock.getDt()
        
        # Update ECS systems
        self.ecs_manager.update(dt)
        
        return task.cont

    def _physics_task(self, task: Task) -> int:
        """
        Advance fixed-step physics and sync vehicle visuals each frame.

        Args:
            task: Panda3D task object.

        Returns:
            int: `task.cont` while simulation remains active.
        """

        if not self.physics_world:
            return task.cont

        dt: float = globalClock.getDt()
        self.physics_world.step(dt)

        if self.player_vehicle:
            self.player_vehicle.sync_visuals()

        return task.cont

    def cleanup(self) -> None:
        """
        Cleanly detach runtime systems and physics objects.
        """

        self.taskMgr.remove("physics_task")
        self.taskMgr.remove("update_task")

        if self.player_vehicle:
            self.player_vehicle.cleanup()
            self.player_vehicle = None

        if self.physics_world:
            self.physics_world.cleanup()
            self.physics_world = None


def main() -> None:
    """
    Application entry point.
    
    Creates and runs the Universal Racing Game application.
    Handles graceful shutdown on errors.
    """
    try:
        # Create application instance
        game = UniversalRacingGame()
        
        # Run the game
        game.run()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
