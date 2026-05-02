"""Path discovery and asset resolution helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class PathManager:
    """Resolve project-relative paths for game assets and resources."""

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    ASSETS_DIR: Path = BASE_DIR / "assets"
    IMAGES_DIR: Path = ASSETS_DIR / "images"
    LANG_DIR: Path = ASSETS_DIR / "lang"
    AUDIO_DIR: Path = ASSETS_DIR / "audio"
    SOUNDTRACKS_DIR: Path = ASSETS_DIR / "soundtracks"

    @classmethod
    def resolve_language_candidates(cls, lang_code: str) -> tuple[Path, Path]:
        """Return requested and English fallback language file paths."""
        requested_file: Path = cls.LANG_DIR / f"{lang_code}.json"
        english_file: Path = cls.LANG_DIR / "en.json"
        return requested_file, english_file

    @classmethod
    def resolve_audio_file(cls, filename: str) -> Optional[Path]:
        """Resolve audio file from known audio directories."""
        search_directories: tuple[Path, Path] = (
            cls.AUDIO_DIR,
            cls.SOUNDTRACKS_DIR,
        )
        requested_lower: str = filename.lower()

        for directory in search_directories:
            if not directory.exists() or not directory.is_dir():
                continue

            direct_match: Path = directory / filename
            if direct_match.exists() and direct_match.is_file():
                return direct_match.resolve()

            for candidate in directory.iterdir():
                if candidate.is_file() and candidate.name.lower() == requested_lower:
                    return candidate.resolve()

        return None

    @classmethod
    def resolve_image_file(cls, *filenames: str) -> Optional[Path]:
        """Resolve an image path by trying case-insensitive filename matches."""
        if not cls.IMAGES_DIR.exists() or not cls.IMAGES_DIR.is_dir():
            return None

        available_files: tuple[Path, ...] = tuple(
            candidate for candidate in cls.IMAGES_DIR.iterdir() if candidate.is_file()
        )
        if not available_files:
            return None

        available_by_lower: dict[str, Path] = {
            candidate.name.lower(): candidate for candidate in available_files
        }

        for filename in filenames:
            if not filename:
                continue
            resolved: Optional[Path] = available_by_lower.get(filename.lower())
            if resolved is not None:
                return resolved.resolve()

        return None
