#!/usr/bin/env python3
"""
Test script for SplashManager implementation.
This script verifies that the splash screen system is properly configured.
"""

import sys
from pathlib import Path

# Check if required files exist
assets_dir = Path("./assets")
images_dir = assets_dir / "images"
audio_dir = assets_dir / "audio"

print("=" * 60)
print("Splash Screen System Verification")
print("=" * 60)

# Check splash images
print("\n1. Checking splash images:")
splash_images = ["splash1.png", "splash2.png", "splash3.png"]
for img in splash_images:
    img_path = images_dir / img
    if img_path.exists():
        size = img_path.stat().st_size
        print(f"   [OK] {img} ({size:,} bytes)")
    else:
        print(f"   [MISSING] {img}")

# Check audio directory
print("\n2. Checking audio directory:")
if audio_dir.exists():
    print(f"   [OK] Audio directory exists")
    audio_files = list(audio_dir.glob("*"))
    if audio_files:
        for af in audio_files:
            print(f"   - {af.name}")
    else:
        print(f"   - No audio files found (expected splash_ambient.mp3 or .wav)")
else:
    print(f"   [MISSING] Audio directory not found")

# Check Python modules
print("\n3. Checking Python modules:")
try:
    from src.ui_manager import SplashManager
    print("   [OK] SplashManager class imported successfully")
except ImportError as e:
    print(f"   [ERROR] Failed to import SplashManager: {e}")

try:
    from src.main import UniversalRacingGame
    print("   [OK] UniversalRacingGame class imported successfully")
except ImportError as e:
    print(f"   [ERROR] Failed to import UniversalRacingGame: {e}")

# Check setup.py configuration
print("\n4. Checking setup.py configuration:")
setup_path = Path("setup.py")
if setup_path.exists():
    content = setup_path.read_text()
    if "assets/**/*" in content:
        print("   [OK] Assets include pattern configured")
    else:
        print("   [WARNING] Assets include pattern not found")
else:
    print("   [ERROR] setup.py not found")

print("\n" + "=" * 60)
print("Verification Complete")
print("=" * 60)
print("\nNote: To run the actual splash screen, execute:")
print("  python src/main.py")
print("\nTo skip splash, press Space or Escape during the sequence.")