"""
Universal Racing Game - Setup Configuration

This setup.py file configures the build process for the Universal Racing Game
using setuptools and panda3d-build. It defines package metadata, dependencies,
and build options for creating distributable runtime packages across multiple
platforms.

Author: piotrek1372
Version: 0.1.0
"""

from setuptools import setup

# Package metadata
NAME = "universal-racing-game"
VERSION = "0.1.0"
AUTHOR = "piotrek1372"
DESCRIPTION = "Wieloplatformowa gra wyścigowa 3D oparta na architekturze ECS."

# Dependencies required for runtime
INSTALL_REQUIRES = [
    "panda3d",
    "panda3d-complexpbr",
    "requests",
]

# Build configuration for panda3d-build
# The build_apps command from panda3d-build creates standalone runtime packages
# that bundle the Python interpreter, Panda3D runtime, and application code.
setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    description=DESCRIPTION,
    install_requires=INSTALL_REQUIRES,

    # Build options for panda3d-build
    # These options configure how the runtime packages are built and what
    # platforms are targeted.
    options={
        "build_apps": {
            # Target platforms for the runtime build
            # - win_amd64: 64-bit Windows
            # - manylinux2014_x86_64: 64-bit Linux (compatible with glibc 2.17+)
            # - macosx_10_9_x86_64: 64-bit macOS (10.9 and newer)
            "platforms": [
                "win_amd64",
                "manylinux2014_x86_64",
                "macosx_10_9_x86_64",
            ],

            # Icon files for specific platforms
            # Each platform can have its own icon format:
            # - Windows: .ico format
            # - macOS: .icns format
            # - Linux: Uses the default icon from the application or window manager
            "icon_files": {
                "win_amd64": {
                    "icon_file": "assets/icons/icon.ico",
                },
                "macosx_10_9_x86_64": {
                    "icon_file": "assets/icons/icon.icns",
                },
            },

            # Main application entry point
            # Panda3D's gui_apps option specifies which Python scripts should be
            # converted into executable GUI applications (with their own window
            # and event loop). The format is "module:function" where the function
            # is called to start the application.
            "gui_apps": {
                "main": "main",
            },

            # Include patterns for additional files to bundle in the runtime
            # These glob patterns ensure that non-Python resources are included
            # in the final distribution packages.
            #
            # - locales/*.json: Localization files containing translated strings
            # - assets/**/*: Game assets including 3D models, textures, sounds
            # - assets/icons/*: Application icons for all supported platforms
            "include_patterns": [
                "locales/*.json",
                "assets/**/*",
                "assets/icons/*",
            ],

            # Output directory for built runtime packages
            # Each platform will have its own subdirectory with the standalone
            # executable and all required runtime files.
            "output_dir": "dist",

            # Log file for the build process
            # Records detailed information about the build for debugging
            "log_filename": "build.log",

            # Runtime mode (as opposed to development mode)
            # In runtime mode, only the necessary Python modules and resources
            # are included, resulting in smaller distribution packages.
            "runtime": "deploy",

            # Use console for output (set to False for pure GUI apps)
            # For a racing game with a graphical interface, this is typically
            # set to False to avoid showing a console window on Windows.
            "console": False,

            # Application name shown in window title and task manager
            "appname": "Universal Racing Game",

            # Company/organization name
            "company": "URG Development Team",

            # Copyright information
            "copyright": "Copyright (c) 2026 piotrek1372",

            # Application version (separate from package version)
            "version": VERSION,

            # Icon file for the application
            # Uncomment and specify path if you have an icon file:
            # "icon": "assets/icon.ico",
        }
    },

    # Python version requirement
    python_requires=">=3.7",

    # Package structure
    package_dir={'': 'src'},
    packages=['src'],
    py_modules=[],

    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: MacOS X",
        "Environment :: Win32 (MS Windows)",
        "Environment :: X11 Applications",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment :: Racing",
        "Topic :: Multimedia :: Graphics :: 3D Rendering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)