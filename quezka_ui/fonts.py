"""The suite's typeface, shipped with the kit so every app looks the same on every machine: Manrope (SIL Open
Font License, see assets/Manrope-OFL.txt), with Cyrillic for the Russian translations."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFontDatabase

FAMILY = "Manrope"
WEIGHTS = ("Regular", "Medium", "SemiBold", "Bold")
_ASSETS = Path(__file__).with_name("assets")


def load() -> str | None:
    """Make the typeface available to Qt. Returns its family, or None if it couldn't be loaded (then the
    app keeps the system's font)."""
    loaded = [QFontDatabase.addApplicationFont(str(_ASSETS / f"{FAMILY}-{weight}.ttf")) for weight in WEIGHTS]
    return FAMILY if any(i >= 0 for i in loaded) else None
