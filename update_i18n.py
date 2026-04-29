import re
with open('C:/Users/piotr/Desktop/universal-racing-game/src/i18n.py', 'r') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    if lines[i].strip() == 'def __init__(self, locales_dir: str = None) -> None:':
        new_lines.append(lines[i])
        i += 1
        # Skip docstring
        while i < len(lines) and '"""' in lines[i]:
            i += 1
        while i < len(lines) and '"""' not in lines[i]:
            i += 1
        if i < len(lines) and '"""' in lines[i]:
            i += 1
        # Now replace the Args section
        new_lines.append('        """\n')
        new_lines.append('        Initialize the LocalizationManager.\n')
        new_lines.append('        \n')
        new_lines.append('        Args:\n')
        new_lines.append('            locales_dir: Path to directory containing locale JSON files.\n')
        new_lines.append('                        Defaults to "../locales" relative to this file (src/).\n')
        new_lines.append('        """\n')
        # Skip old args and docstring
        while i < len(lines) and 'Defaults to' in lines[i]:
            i += 1
        while i < len(lines) and '"""' not in lines[i]:
            i += 1
        if i < len(lines) and '"""' in lines[i]:
            i += 1
        # Now replace the body
        new_lines.append('        if locales_dir is None:\n')
        new_lines.append('            # Ustaw bazowa sciezke: wychodzimy z src/ do katalogu glownego\n')
        new_lines.append('            self.locales_dir: Path = Path(__file__).parent.parent / "locales"\n')
        new_lines.append('        else:\n')
        new_lines.append('            self.locales_dir: Path = Path(locales_dir)\n')
        new_lines.append('        self.current_language: str = ""\n')
        new_lines.append('        self.translations: Dict[str, Any] = {}\n')
        new_lines.append('        self.default_language: str = "en"\n')
        new_lines.append('        \n')
        new_lines.append('        # Ensure locales directory exists\n')
        new_lines.append('        self.locales_dir.mkdir(parents=True, exist_ok=True)\n')
        new_lines.append('        \n')
        new_lines.append('        # Detect and load system language\n')
        new_lines.append('        self._detect_and_load_language()\n')
        # Skip old body
        while i < len(lines) and 'self._detect_and_load_language()' not in lines[i]:
            i += 1
        if i < len(lines) and 'self._detect_and_load_language()' in lines[i]:
            i += 1
    else:
        new_lines.append(lines[i])
        i += 1

with open('C:/Users/piotr/Desktop/universal-racing-game/src/i18n.py', 'w') as f:
    f.writelines(new_lines)
print('Updated i18n.py')
