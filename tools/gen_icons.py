#!/usr/bin/env python3
"""
Icon Generator for Universal Racing Game

Generates placeholder icon files (.ico and .png) for all platforms
to avoid errors when the application starts and icon files are missing.

This script creates simple placeholder icons using Pillow (PIL).
The generated icons are minimal but valid, allowing the application
to run without modification. For production, replace these with
properly designed icons.

Author: URG Development Team
Version: 1.0.0
"""

from pathlib import Path
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Pillow not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "-q"])
    from PIL import Image, ImageDraw


def create_placeholder_ico(output_path: Path, size: int = 256) -> None:
    """
    Create a placeholder ICO file with a simple game controller icon.
    
    Args:
        output_path: Path where the .ico file will be saved
        size: Icon size in pixels (default 256)
    """
    # Create a new image with RGBA (transparency support)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple racing-themed icon
    # Background circle (racing wheel style)
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(30, 30, 40, 255),
        outline=(0, 150, 255, 255),
        width=max(1, size // 32)
    )
    
    # Inner circle
    inner_margin = size // 4
    draw.ellipse(
        [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
        fill=(50, 50, 60, 255),
        outline=(0, 200, 255, 255),
        width=max(1, size // 64)
    )
    
    # Center dot
    center = size // 2
    dot_radius = max(1, size // 16)
    draw.ellipse(
        [
            center - dot_radius,
            center - dot_radius,
            center + dot_radius,
            center + dot_radius,
        ],
        fill=(0, 200, 255, 255),
    )
    
    # Save as ICO (multiple sizes embedded)
    img.save(output_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print(f"Created: {output_path} ({size}x{size})")


def create_placeholder_png(output_path: Path, size: int = 256) -> None:
    """
    Create a placeholder PNG file with a simple game controller icon.
    
    Args:
        output_path: Path where the .png file will be saved
        size: Icon size in pixels (default 256)
    """
    # Create a new image with RGBA (transparency support)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple racing-themed icon
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(30, 30, 40, 255),
        outline=(0, 150, 255, 255),
        width=max(1, size // 32)
    )
    
    inner_margin = size // 4
    draw.ellipse(
        [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
        fill=(50, 50, 60, 255),
        outline=(0, 200, 255, 255),
        width=max(1, size // 64)
    )
    
    center = size // 2
    dot_radius = max(1, size // 16)
    draw.ellipse(
        [
            center - dot_radius,
            center - dot_radius,
            center + dot_radius,
            center + dot_radius,
        ],
        fill=(0, 200, 255, 255),
    )
    
    # Save as PNG
    img.save(output_path, format="PNG")
    print(f"Created: {output_path} ({size}x{size})")


def create_placeholder_icns(output_path: Path) -> None:
    """
    Create a placeholder ICNS file for macOS.
    
    Note: ICNS is a macOS-specific format. This creates a simple PNG
    as a fallback since proper ICNS creation requires additional tools.
    For production macOS builds, use a proper .icns file.
    
    Args:
        output_path: Path where the .icns file will be saved
    """
    # Create a high-quality PNG as fallback
    # (ICNS would require pyicns or iconutil on macOS)
    print(f"Note: Creating PNG fallback for macOS icon (rename to .icns for production)")
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    margin = 64
    draw.ellipse(
        [margin, margin, 512 - margin, 512 - margin],
        fill=(30, 30, 40, 255),
        outline=(0, 150, 255, 255),
        width=8,
    )
    
    inner_margin = 128
    draw.ellipse(
        [inner_margin, inner_margin, 512 - inner_margin, 512 - inner_margin],
        fill=(50, 50, 60, 255),
        outline=(0, 200, 255, 255),
        width=4,
    )
    
    center = 256
    dot_radius = 32
    draw.ellipse(
        [center - dot_radius, center - dot_radius, center + dot_radius, center + dot_radius],
        fill=(0, 200, 255, 255),
    )
    
    # Save as PNG (macOS can use PNG as icon in some contexts)
    # For proper .icns, use: iconutil or a dedicated tool
    img.save(output_path, format="PNG")
    print(f"Created: {output_path} (512x512 PNG - rename to .icns or convert for production)")


def main() -> None:
    """Generate all placeholder icon files."""
    # Determine project root (parent of tools/)
    tools_dir = Path(__file__).parent
    project_root = tools_dir.parent
    icons_dir = project_root / "assets" / "icons"
    
    # Ensure icons directory exists
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    print("=== Universal Racing Game - Icon Generator ===")
    print(f"Output directory: {icons_dir}\n")
    
    # Generate icons
    create_placeholder_ico(icons_dir / "icon.ico", size=256)
    create_placeholder_png(icons_dir / "icon.png", size=256)
    create_placeholder_icns(icons_dir / "icon.icns")
    
    print("\n=== All icons generated successfully ===")
    print("\nNote: These are placeholder icons for development.")
    print("For production, replace with professionally designed icons.")


if __name__ == "__main__":
    main()
