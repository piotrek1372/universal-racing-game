with open('C:/Users/piotr/Desktop/universal-racing-game/src/i18n.py', 'r') as f:
    s = f.read()
old = '''    def __init__(self, locales_dir: str = "src/locales") -> None:
        """
        Initialize the LocalizationManager.
        
        Args:
            locales_dir: Path to directory containing locale JSON files.
                        Defaults to 'src/locales'.
        """
        self.locales_dir: Path = Path(locales_dir)
        self.current_language: str = ""
        self.translations: Dict[str, Any] = {}
        self.default_language: str = "en"
        
        # Ensure locales directory exists
        self.locales_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect and load system language
        self._detect_and_load_language()'''
new = '''    def __init__(self, locales_dir: str = None) -> None:
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
        
        # Ensure locales directory exists
        self.locales_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect and load system language
        self._detect_and_load_language()'''
s = s.replace(old, new)
with open('C:/Users/piotr/Desktop/universal-racing-game/src/i18n.py', 'w') as f:
    f.write(s)
print('Zaktualizowano i18n.py')
