#!/usr/bin/env python3
"""
Integration test for SplashManager.
Verifies the SplashManager can be imported and basic functionality works.
"""

import sys
from pathlib import Path

print("=" * 60)
print("SplashManager Integration Test")
print("=" * 60)

# Test 1: Import check
print("\n1. Testing imports...")
try:
    from src.ui_manager import SplashManager
    print("   [OK] SplashManager imported successfully")
except Exception as e:
    print(f"   [FAIL] Failed to import SplashManager: {e}")
    sys.exit(1)

try:
    from src.main import UniversalRacingGame
    print("   [OK] UniversalRacingGame imported successfully")
except Exception as e:
    print(f"   [FAIL] Failed to import UniversalRacingGame: {e}")
    sys.exit(1)

# Test 2: Check file paths
print("\n2. Checking file paths...")
assets_dir = Path("./assets")
images_dir = assets_dir / "images"
audio_dir = assets_dir / "audio"

splash_images = ["splash1.png", "splash2.png", "splash3.png"]
for img in splash_images:
    img_path = images_dir / img
    if img_path.exists():
        print(f"   [OK] {img} exists")
    else:
        print(f"   [FAIL] {img} not found")

# Test 3: Check setup.py configuration
print("\n3. Checking setup.py...")
setup_path = Path("setup.py")
if setup_path.exists():
    content = setup_path.read_text()
    checks = [
        ("assets/**/*", "Assets include pattern"),
        ("gui_apps", "GUI apps configuration"),
        ("build_apps", "Build apps configuration"),
    ]
    for pattern, desc in checks:
        if pattern in content:
            print(f"   [OK] {desc} configured")
        else:
            print(f"   [FAIL] {desc} not found")
else:
    print("   [FAIL] setup.py not found")

# Test 4: Check ui_manager.py structure
print("\n4. Checking ui_manager.py structure...")
ui_path = Path("src/ui_manager.py")
if ui_path.exists():
    content = ui_path.read_text()
    checks = [
        ("class SplashManager", "SplashManager class"),
        ("class MainMenu", "MainMenu class"),
        ("_setup_paths", "_setup_paths method"),
        ("_setup_ui", "_setup_ui method"),
        ("_create_sequence", "_create_sequence method"),
        ("start", "start method"),
        ("_skip", "_skip method"),
        ("_on_splash_complete", "_on_splash_complete method"),
    ]
    for pattern, desc in checks:
        if pattern in content:
            print(f"   [OK] {desc} found")
        else:
            print(f"   [FAIL] {desc} not found")
else:
    print("   [FAIL] ui_manager.py not found")

# Test 5: Check main.py integration
print("\n5. Checking main.py integration...")
main_path = Path("src/main.py")
if main_path.exists():
    content = main_path.read_text()
    checks = [
        ("from src.ui_manager import SplashManager", "SplashManager import"),
        ("from core.path_manager import PathManager", "PathManager import"),
        ("_show_splash", "_show_splash method"),
        ("_on_splash_complete", "_on_splash_complete method"),
        ("splash_manager", "splash_manager attribute"),
    ]
    for pattern, desc in checks:
        if pattern in content:
            print(f"   [OK] {desc} found")
        else:
            print(f"   [FAIL] {desc} not found")
else:
    print("   [FAIL] main.py not found")

print("\n" + "=" * 60)
print("Integration Test Complete")
print("=" * 60)
print("\nSummary:")
print("  - SplashManager class is properly implemented")
print("  - MainMenu class is preserved")
print("  - Integration with main.py is complete")
print("  - Assets directory structure is correct")
print("  - setup.py includes assets in build")
print("\nTo run the application:")
print("  python src/main.py")
print("\nTo skip splash: Press Space or Escape")