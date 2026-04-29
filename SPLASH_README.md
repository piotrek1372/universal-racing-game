# Splash Screen Implementation

## Overview
This document describes the multimedia splash screen implementation for the Universal Racing Game.

## Features
- Sequential display of 3 splash images (splash1.png, splash2.png, splash3.png)
- Smooth fade-in/fade-out transitions (1s fade in, 1.5s hold, 1s fade out per image)
- Ambient audio support with configurable volume
- Skip functionality (Space or Escape keys)
- Graceful handling of missing assets

## File Structure
```
universal-racing-game/
├── src/
│   ├── main.py              # Main application (integrated splash)
│   └── ui_manager.py        # SplashManager and MainMenu classes
├── assets/
│   ├── images/
│   │   ├── splash1.png      # First splash image
│   │   ├── splash2.png      # Second splash image
│   │   └── splash3.png      # Third splash image
│   └── audio/
│       └── splash_ambient.mp3  # Ambient audio (optional)
└── setup.py                 # Build configuration
```

## Implementation Details

### SplashManager Class (ui_manager.py)

**Key Methods:**
- `__init__(base, on_complete)`: Initialize splash manager
- `_setup_paths()`: Configure file paths for assets
- `_setup_ui()`: Create UI elements (fullscreen card)
- `_load_audio()`: Load ambient audio file
- `_create_sequence()`: Build animation sequence
- `start()`: Begin splash screen sequence
- `_skip()`: Skip splash immediately
- `_on_splash_complete()`: Handle completion
- `destroy()`: Clean up resources

**Animation Sequence:**
1. Image 1: Fade in (1s) → Hold (1.5s) → Fade out (1s)
2. Image 2: Fade in (1s) → Hold (1.5s) → Fade out (1s)
3. Image 3: Fade in (1s) → Hold (1.5s) → Fade out (1s)

Total duration: ~13.5 seconds

### Integration with Main Application

**main.py Changes:**
1. Import SplashManager from ui_manager
2. Add `_show_splash()` method to display splash
3. Add `_on_splash_complete()` callback
4. Modify `_setup_input()` to handle skip keys
5. Update `__init__()` to show splash before main menu

**Flow:**
```
Application Start
    ↓
ShowBase Initialization
    ↓
SplashManager.start()
    ↓
[Display splash images with transitions]
    ↓
User presses Space/Escape OR sequence completes
    ↓
_on_splash_complete()
    ↓
Create main menu UI
    ↓
Main application loop
```

## Audio Support

The splash screen supports ambient audio with the following characteristics:
- Format: MP3 or WAV
- Location: `./assets/audio/splash_ambient.mp3` (or .wav)
- Behavior: Loops during splash sequence
- Volume: Starts muted (0.0), can be controlled externally

**Note:** Volume fade-in would require a custom interval or task, as Panda3D's standard LerpVolumeInterval is not available in all versions.

## Skip Functionality

Users can skip the splash screen at any time by pressing:
- **Space** key
- **Escape** key

When skipped:
1. Animation sequence stops immediately
2. Audio stops
3. Splash card is hidden
4. Main menu is displayed

## Error Handling

The implementation gracefully handles missing assets:
- Missing splash images: Warning logged, sequence continues with available images
- Missing audio file: Warning logged, splash continues without audio
- No images available: 1-second delay before proceeding to main menu

## Build Configuration

**setup.py** includes assets in the build:
```python
"include_patterns": [
    "locales/*.json",
    "assets/**/*",  # Includes all assets recursively
    "assets/icons/*",
]
```

This ensures all splash images and audio files are included in the distributable package.

## Usage

### Running the Application
```bash
python src/main.py
```

### Testing
```bash
# Verify implementation
python test_integration.py

# Check splash screen components
python test_splash.py
```

### Adding Custom Audio
1. Place audio file in `./assets/audio/`
2. Name it `splash_ambient.mp3` or `splash_ambient.wav`
3. The splash screen will automatically load and play it

## Technical Notes

- Uses Panda3D's `Sequence` and `LerpColorScaleInterval` for animations
- Fullscreen card rendered in `render2d` space
- Alpha blending for smooth transitions
- Input handlers properly cleaned up on completion
- Compatible with existing MainMenu class

## Future Enhancements

Potential improvements:
1. Add volume fade-in using custom interval or task
2. Support for more image formats
3. Configurable timing per image
4. Progress indicator during splash
5. Background loading of main menu assets during splash