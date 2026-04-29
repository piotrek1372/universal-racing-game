"""
Localization Manager for Universal Racing Game

This module provides internationalization (i18n) support with automatic
language detection and fallback mechanisms. It uses Python's locale module
to detect the system language and loads appropriate translation files
from the locales directory.

Author: URG Development Team
Version: 1.0.0
"""

import json
import locale
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Any


class LocalizationManager:
    """
    Manages localization and internationalization for the application.
    
    This class handles automatic language detection, loading of translation
    files, and provides a unified interface for accessing translated strings.
    It supports UTF-8 encoded JSON files and includes a robust fallback
    mechanism to ensure the application always has valid translations.
    
    Attributes:
        locales_dir (Path): Directory containing locale JSON files
        current_language (str): Currently active language code
        translations (Dict[str, Any]): Loaded translation dictionary
        default_language (str): Fallback language code (en)
    """
    
    def __init__(self, locales_dir: str = None) -> None:
        """
        Initialize the LocalizationManager.
        
        Args:
            locales_dir: Path to directory containing locale JSON files.
                        Defaults to '../locales' relative to this file (src/).
        """
        if locales_dir is None:
            # Ustaw bazowa sciezke: wychodzimy z src/ do katalogu glownego
            self.locales_dir: Path = Path(__file__).parent.parent / "locales"
        else:
            self.locales_dir: Path = Path(locales_dir)
        self.current_language: str = ""
        self.translations: Dict[str, Any] = {}
        self.default_language: str = "en"
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
        
        # Log the locales directory path
        logging.debug(f"Szukam tłumaczeń w: {self.locales_dir.absolute()}")
        
        # Ensure locales directory exists
        self.locales_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect and load system language
        self._detect_and_load_language()
    
    def _detect_system_language(self) -> str:
        """
        Detect the system's default language using locale module.
        
        Uses locale.getdefaultlocale() to determine the system language.
        Extracts the language code (e.g., 'en' from 'en_US') and normalizes
        it for use with our locale files.
        
        Returns:
            str: Detected language code (e.g., 'en', 'ja', 'zh', 'ar')
        
        Note:
            If locale detection fails or returns None, defaults to 'en'.
            Handles both format variations: 'en_US' and 'en-US'.
        """
        try:
            # Get system default locale
            sys_locale = locale.getdefaultlocale()
            
            if sys_locale and sys_locale[0]:
                # Extract language code (e.g., 'en' from 'en_US' or 'en-US')
                lang_code = sys_locale[0].split('_')[0].split('-')[0].lower()
                return lang_code
            else:
                # Fallback to English if detection fails
                return self.default_language
        except Exception as e:
            # Log error in production (here we just fallback)
            print(f"Warning: Could not detect system language: {e}")
            return self.default_language
    
    def _load_translations(self, language_code: str) -> Optional[Dict[str, Any]]:
        """
        Load translations from JSON file for the specified language.
        
        Loads UTF-8 encoded JSON file from the locales directory.
        The file should be named '{language_code}.json' (e.g., 'en.json').
        
        Args:
            language_code: ISO 639-1 language code (e.g., 'en', 'ja', 'zh')
        
        Returns:
            Optional[Dict[str, Any]]: Loaded translations dictionary, or None if file not found
        
        Note:
            All JSON files must be UTF-8 encoded to support Unicode characters
            from various languages (Cyrillic, Arabic, Chinese, Japanese, etc.).
        """
        locale_file: Path = self.locales_dir / f"{language_code}.json"
        
        if not locale_file.exists():
            print(f"Warning: Locale file not found: {locale_file}")
            return None
        
        try:
            # Open with UTF-8 encoding to support all Unicode characters
            with open(locale_file, 'r', encoding='utf-8') as f:
                translations: Dict[str, Any] = json.load(f)
                return translations
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {locale_file}: {e}")
            return None
        except Exception as e:
            print(f"Error: Could not load {locale_file}: {e}")
            return None
    
    def _detect_and_load_language(self) -> None:
        """
        Detect system language and load appropriate translations.
        
        Implements a fallback chain:
        1. Try to load detected system language
        2. If not available, try to load default language (en)
        3. If default also fails, initialize with empty dict
        
        This ensures the application always has valid translations,
        even if locale files are missing or corrupted.
        """
        # Step 1: Detect system language
        detected_lang: str = self._detect_system_language()
        self.current_language = detected_lang
        
        print(f"Detected system language: {detected_lang}")
        
        # Step 2: Try to load detected language
        translations: Optional[Dict[str, Any]] = self._load_translations(detected_lang)
        
        if translations is not None:
            self.translations = translations
            print(f"Loaded translations for: {detected_lang}")
            return
        
        # Step 3: Fallback to default language
        print(f"Falling back to default language: {self.default_language}")
        translations = self._load_translations(self.default_language)
        
        if translations is not None:
            self.translations = translations
            self.current_language = self.default_language
            print(f"Loaded fallback translations for: {self.default_language}")
            return
        
        # Step 4: Ultimate fallback - empty translations
        print("Warning: Could not load any translations, using empty dict")
        self.translations = {}
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get a translated string by key.
        
        Supports nested keys using dot notation (e.g., 'menu.start').
        If the key is not found, returns the default value or the key itself.
        
        Args:
            key: Translation key, supports dot notation for nested access
            default: Default value if key not found (defaults to key itself)
        
        Returns:
            str: Translated string or default value
        
        Example:
            >>> lm = LocalizationManager()
            >>> lm.get('welcome_message')
            'Welcome to Universal Racing Game!'
            >>> lm.get('menu.start')
            'Start Game'
        """
        # Navigate nested dictionary using dot notation
        keys: list[str] = key.split('.')
        value: Any = self.translations
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Key not found
                return default if default is not None else key
        
        # Ensure we return a string
        return str(value) if value is not None else (default if default is not None else key)
    
    def get_language(self) -> str:
        """
        Get the current language code.
        
        Returns:
            str: Current language code (e.g., 'en', 'ja', 'zh')
        """
        return self.current_language
    
    def get_all_translations(self) -> Dict[str, Any]:
        """
        Get all loaded translations.
        
        Returns:
            Dict[str, Any]: Complete translations dictionary
        """
        return self.translations.copy()
    
    def reload(self) -> bool:
        """
        Reload translations for the current language.
        
        Useful when locale files have been updated without restarting
        the application.
        
        Returns:
            bool: True if reload successful, False otherwise
        """
        translations: Optional[Dict[str, Any]] = self._load_translations(self.current_language)
        
        if translations is not None:
            self.translations = translations
            return True
        
        # Try default language as fallback
        translations = self._load_translations(self.default_language)
        if translations is not None:
            self.translations = translations
            self.current_language = self.default_language
            return True
        
        return False
    
    def set_language(self, language_code: str) -> bool:
        """
        Manually set the language (override auto-detection).
        
        Args:
            language_code: Language code to switch to
        
        Returns:
            bool: True if language changed successfully, False otherwise
        """
        translations: Optional[Dict[str, Any]] = self._load_translations(language_code)
        
        if translations is not None:
            self.translations = translations
            self.current_language = language_code
            print(f"Language changed to: {language_code}")
            return True
        
        print(f"Warning: Could not load language: {language_code}")
        return False


# Global instance for easy access
_localization_manager: Optional[LocalizationManager] = None


def get_localization_manager() -> LocalizationManager:
    """
    Get or create the global LocalizationManager instance.
    
    Implements singleton pattern to ensure only one instance exists
    throughout the application lifecycle.
    
    Returns:
        LocalizationManager: Global localization manager instance
    """
    global _localization_manager
    
    if _localization_manager is None:
        _localization_manager = LocalizationManager()
    
    return _localization_manager


if __name__ == "__main__":
    # Test the localization manager
    lm: LocalizationManager = get_localization_manager()
    
    print(f"Current language: {lm.get_language()}")
    print(f"Welcome message: {lm.get('welcome_message')}")
    print(f"Start button: {lm.get('menu.start')}")
    print(f"Speed label: {lm.get('game.speed')}")